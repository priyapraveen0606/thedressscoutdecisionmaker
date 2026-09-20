from __future__ import annotations

import base64
import os
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import Depends, FastAPI, File, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

from .ai_service import build_search_queries, evaluate_search_results, summarize_results
from .crawler import crawl_catalog
from .engine import evaluate_product
from .personal_profile import load_personal_profile, save_personal_profile
from .schema import DecisionResult, EvaluateRequest, ProductCandidate, UserProfile

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "local-dev-secret-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRES_MINUTES = int(os.getenv("JWT_EXPIRES_MINUTES", "60"))
API_USERNAME = os.getenv("API_USERNAME", "admin")
API_PASSWORD = os.getenv("API_PASSWORD", "admin")

app = FastAPI(title="Petite Office Agent", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


async def _default_user_lookup(username: str, password: str) -> bool:
    return username == API_USERNAME and password == API_PASSWORD


def _create_access_token(username: str) -> str:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(minutes=JWT_EXPIRES_MINUTES)
    payload = {
        "sub": username,
        "iat": issued_at,
        "exp": expires_at,
    }
    return jwt.encode(payload, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def get_current_user(token: str = Depends(oauth2_scheme)) -> dict[str, Any]:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:  # pragma: no cover - handled by HTTP exception
        raise credentials_exception from exc

    username = payload.get("sub")
    if not username:
        raise credentials_exception

    return {"username": username}


@app.get("/health")
def healthcheck() -> dict[str, str]:
    return {"status": "ok", "service": "petite-office-agent"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Petite Office Agent is ready."}


@app.get("/profile")
def profile() -> dict[str, object]:
    return load_personal_profile()


@app.get("/admin/profile")
def admin_profile() -> dict[str, object]:
    return load_personal_profile()


@app.post("/admin/profile")
def update_admin_profile(profile: UserProfile) -> dict[str, object]:
    payload = profile.model_dump()
    save_personal_profile(payload)
    return payload


@app.post("/token")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()) -> dict[str, str]:
    if not await _default_user_lookup(form_data.username, form_data.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect username or password")
    token = _create_access_token(form_data.username)
    return {"access_token": token, "token_type": "bearer"}


@app.post("/evaluate", response_model=DecisionResult)
def evaluate(request: EvaluateRequest) -> DecisionResult:
    return evaluate_product(request.product, request.user)


@app.post("/catalog/evaluate")
async def evaluate_catalog(urls: dict[str, list[str]]) -> dict[str, list[dict[str, object]]]:
    profile = UserProfile(**load_personal_profile())
    results: list[dict[str, object]] = []

    for url in urls.get("urls", []):
        catalog_items = await crawl_catalog(url)
        for item in catalog_items:
            decision = evaluate_product(item, profile)
            results.append(
                {
                    "url": url,
                    "title": item.title,
                    "brand": item.brand,
                    "color": item.color,
                    "decision": decision.decision,
                    "score": decision.score,
                    "summary": decision.summary,
                    "reasons": decision.reasons,
                }
            )

    return {"items": results}


@app.post("/ai/search-queries")
def generate_search_queries(payload: dict[str, object]) -> dict[str, list[str]]:
    profile = payload.get("profile", {})
    retailers = payload.get("retailers", ["amazon", "fablestreet"])
    limit = int(payload.get("limit", 3))
    return {"queries": build_search_queries(dict(profile), retailers=list(retailers), limit=limit)}


@app.post("/ai/summarize")
def summarize_catalog_results(payload: dict[str, list[dict[str, object]]]) -> dict[str, str]:
    items = payload.get("items", [])
    return {"summary": summarize_results(list(items))}


@app.post("/search/evaluate")
async def search_and_evaluate(payload: dict[str, object]) -> dict[str, object]:
    profile_data = load_personal_profile()
    queries = build_search_queries(
        profile_data,
        retailers=list(payload.get("retailers", ["amazon", "fablestreet"])),
        limit=int(payload.get("limit", 3)),
    )

    curated: list[dict[str, object]] = []
    for query in queries:
        for retailer in ["amazon", "fablestreet"]:
            if retailer not in query:
                continue
            items = await crawl_catalog(f"https://www.{retailer}.com/search?q={query.replace(' ', '+')}")
            curated.extend(evaluate_search_results([item.model_dump() for item in items], profile_data, minimum_score=80))

    unique: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in curated:
        key = f"{item.get('title')}:{item.get('brand')}:{item.get('score')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return {"queries": queries, "items": unique[:10], "summary": summarize_results(unique[:10])}


@app.post("/api/v1/evaluate-structured")
async def evaluate_structured(payload: dict[str, Any], current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    user_payload = payload.get("user")
    product_payload = payload.get("product")
    baseline = payload.get("baseline")

    if user_payload is None or product_payload is None:
        return {
            "user": current_user["username"],
            "status": "accepted",
            "baseline": baseline,
            "message": "Structured evaluation received but no product was provided for scoring.",
        }

    try:
        user = UserProfile(**user_payload)
        product = ProductCandidate(**product_payload)
        decision = evaluate_product(product, user)
    except Exception as exc:  # pragma: no cover - defensive validation path
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid structured evaluation payload: {exc}") from exc

    return {
        "user": current_user["username"],
        "decision": decision.model_dump(),
        "baseline": baseline,
        "status": "ok",
    }


@app.post("/api/v1/evaluate-image")
async def evaluate_image(
    file: UploadFile = File(...),
    current_user: dict[str, Any] = Depends(get_current_user),
) -> dict[str, Any]:
    image_bytes = await file.read()
    image_base64 = base64.b64encode(image_bytes).decode("utf-8")
    return {
        "user": current_user["username"],
        "filename": file.filename,
        "content_type": file.content_type,
        "image_base64": image_base64[:120] + ("..." if len(image_base64) > 120 else ""),
        "result": {
            "decision": "BUY",
            "score": 88,
            "summary": "Image evaluation placeholder: a multimodal Instructor backend can be integrated here when configured.",
            "reasons": ["Image received and base64 encoded successfully.", "Protected route validated."]
        },
        "status": "ok",
    }


@app.get("/api/v1/scout")
async def scout_and_score_dresses(current_user: dict[str, Any] = Depends(get_current_user)) -> dict[str, Any]:
    profile_data = load_personal_profile()
    queries = build_search_queries(profile_data, retailers=["amazon", "fablestreet"], limit=2)
    curated: list[dict[str, object]] = []

    for query in queries:
        retailer = "amazon" if "amazon" in query else "fablestreet"
        items = await crawl_catalog(f"https://www.{retailer}.com/search?q={query.replace(' ', '+')}")
        curated.extend(evaluate_search_results([item.model_dump() for item in items], profile_data, minimum_score=80))

    unique: list[dict[str, object]] = []
    seen: set[str] = set()
    for item in curated:
        key = f"{item.get('title')}:{item.get('brand')}:{item.get('score')}"
        if key in seen:
            continue
        seen.add(key)
        unique.append(item)

    return {
        "user": current_user["username"],
        "queries": queries,
        "items": unique[:10],
        "summary": summarize_results(unique[:10]),
        "status": "ok",
    }
