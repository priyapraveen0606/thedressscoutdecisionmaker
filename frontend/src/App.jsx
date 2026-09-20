import { useEffect, useMemo, useState } from 'react'

const defaultProduct = {
  title: 'Petite Teal Fit & Flare Dress',
  brand: 'Anchor Studio',
  price: 84,
  color: 'teal',
  silhouette: 'fit_flare',
  neckline: 'v_neck',
  sleeve_length: 'short',
  hem_length_below_knee_in: 0.5,
  is_office_formal: true,
}

const baseProfile = {
  height_cm: 156,
  weight_kg: 74,
  body_shape: 'pear',
  preferred_colors: ['green', 'teal', 'dark_blue', 'formal_blue', 'white', 'half_white'],
  foot_type: 'flat_foot',
  max_hem_below_knee_in: 1.5,
  formal_wear_black_disfavored: true,
  min_sleeve_required: true,
}

const offlineSampleCatalog = [
  {
    title: 'Amazon Essentials Midi Dress',
    brand: 'Amazon',
    color: 'teal',
    decision: 'BUY',
    score: 91,
    summary: 'Strong fit and preferred palette match.',
  },
  {
    title: 'Fable Street A-Line Dress',
    brand: 'Fable Street',
    color: 'green',
    decision: 'BUY',
    score: 88,
    summary: 'Balanced silhouette with office-appropriate length.',
  },
  {
    title: 'Structured Black Sheath Midi',
    brand: 'Amazon',
    color: 'black',
    decision: 'PASS',
    score: 42,
    summary: 'Black formal wear is deprioritized and the shape is less forgiving.',
  },
]

export default function App() {
  const [profile, setProfile] = useState(baseProfile)
  const [selectedRetailer, setSelectedRetailer] = useState('amazon')
  const [profileSaveState, setProfileSaveState] = useState('')
  const [urlsText, setUrlsText] = useState('https://www.amazon.com/dp/example\nhttps://www.fablestreet.com/products/aline-dress')
  const [result, setResult] = useState({
    decision: 'BUY',
    score: 92,
    summary: 'Strong fit for the petite office profile.',
    reasons: ['Balanced proportions', 'Preferred palette'],
    actions: ['Proceed with purchase'],
  })
  const [results, setResults] = useState([])
  const [status, setStatus] = useState('Ready to evaluate your selected retailer links.')

  useEffect(() => {
    const loadProfile = async () => {
      try {
        const response = await fetch('http://localhost:8000/profile')
        if (response.ok) {
          const data = await response.json()
          setProfile({ ...baseProfile, ...data })
        }
      } catch {
        // Intentionally keep the generic local profile if the backend is not running.
      }
    }

    loadProfile()
  }, [])

  const retailerOptions = useMemo(
    () => [
      { value: 'amazon', label: 'Amazon' },
      { value: 'fablestreet', label: 'Fable Street' },
      { value: 'all', label: 'Amazon + Fable Street' },
      { value: 'offline', label: 'Offline sample catalog' },
    ],
    [],
  )

  const handleProfileInput = (field, value) => {
    setProfile((current) => ({
      ...current,
      [field]: value,
    }))
  }

  const handleSaveProfile = async () => {
    const normalized = {
      ...profile,
      preferred_colors: profile.preferred_colors
        .map((color) => String(color).trim().toLowerCase())
        .filter(Boolean),
    }

    try {
      const response = await fetch('http://localhost:8000/admin/profile', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(normalized),
      })

      if (!response.ok) {
        throw new Error('Could not save profile')
      }

      setProfileSaveState('Profile encrypted and saved locally.')
      setStatus('Local encrypted profile updated and ready for search.')
    } catch {
      setProfileSaveState('Profile could not be saved. Check the backend service.')
    }
  }

  const handleEvaluate = async () => {
    const urls = urlsText
      .split(/\n|,/)
      .map((item) => item.trim())
      .filter(Boolean)

    if (!urls.length && selectedRetailer !== 'offline') {
      setStatus('Add at least one retailer link before evaluating.')
      return
    }

    if (selectedRetailer === 'offline') {
      setResults(offlineSampleCatalog)
      setStatus('Using the built-in offline sample catalog for local testing.')
      return
    }

    const payload = { urls }

    try {
      const response = await fetch('http://localhost:8000/catalog/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error('Backend unavailable')
      }

      const data = await response.json()
      const nextResults = data.items || []
      setResults(nextResults)
      setStatus(`Evaluated ${nextResults.length} product(s) from ${selectedRetailer}.`)

      if (nextResults.length > 0) {
        const best = nextResults.reduce((winner, item) => (item.score > winner.score ? item : winner), nextResults[0])
        setResult({
          decision: best.decision,
          score: best.score,
          summary: best.summary,
          reasons: best.reasons || ['Reviewed against the local profile.'],
          actions: ['Continue evaluating similar product options.'],
        })
      }
    } catch {
      setResults([])
      setStatus('The backend is unavailable. Use the offline sample catalog or start the API first.')
      setResult({
        decision: 'PASS',
        score: 0,
        summary: 'Unable to evaluate right now.',
        reasons: ['The backend is unavailable.'],
        actions: ['Start the backend service and retry.'],
      })
    }
  }

  const handleEvaluateSingleProduct = async () => {
    const payload = {
      user: profile,
      product: defaultProduct,
    }

    try {
      const response = await fetch('http://localhost:8000/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      })

      if (!response.ok) {
        throw new Error('Backend unavailable')
      }

      const data = await response.json()
      setResult(data)
    } catch {
      setResult({
        decision: 'PASS',
        score: 0,
        summary: 'Unable to evaluate right now.',
        reasons: ['The backend is unavailable.'],
        actions: ['Start the backend service and retry.'],
      })
    }
  }

  const handleCuratedSearch = async () => {
    const retailerSelection = selectedRetailer === 'all' ? ['amazon', 'fablestreet'] : [selectedRetailer]

    try {
      const response = await fetch('http://localhost:8000/search/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ retailers: retailerSelection, limit: 3 }),
      })

      if (!response.ok) {
        throw new Error('Backend unavailable')
      }

      const data = await response.json()
      const nextResults = data.items || []
      setResults(nextResults)
      setStatus(`Generated ${nextResults.length} curated recommendation(s) for ${selectedRetailer}.`)

      if (nextResults.length > 0) {
        const best = nextResults.reduce((winner, item) => (item.score > winner.score ? item : winner), nextResults[0])
        setResult({
          decision: best.decision,
          score: best.score,
          summary: best.summary || data.summary || 'Strong match for the local profile.',
          reasons: best.reasons || ['Reviewed against the local profile.'],
          actions: ['Continue evaluating similar product options.'],
        })
      } else {
        setResult({
          decision: 'PASS',
          score: 0,
          summary: data.summary || 'No item reached the curated threshold for this profile.',
          reasons: ['No product met the score threshold.'],
          actions: ['Try a broader search profile or different retailer selections.'],
        })
      }
    } catch {
      setResults([])
      setStatus('The curated search endpoint is unavailable. Start the API and retry.')
      setResult({
        decision: 'PASS',
        score: 0,
        summary: 'Unable to generate a curated feed right now.',
        reasons: ['The backend is unavailable.'],
        actions: ['Start the backend service and retry.'],
      })
    }
  }

  return (
    <main className="page-shell" aria-live="polite">
      <section className="panel" aria-labelledby="app-title">
        <p className="eyebrow">Style Decision Engine</p>
        <h1 id="app-title">Petite Office Agent</h1>
        <p className="lede">
          Review retailer links and score office-wear picks against your private anchor profile.
        </p>

        <div className="profile-card" aria-labelledby="profile-title">
          <div className="section-heading-row">
            <h2 id="profile-title">Profile editor</h2>
            <button type="button" className="secondary-btn compact" onClick={handleSaveProfile}>
              Save encrypted profile
            </button>
          </div>

          <div className="profile-grid">
            <label>
              <span>Height (cm)</span>
              <input
                type="number"
                min="120"
                max="210"
                value={profile.height_cm}
                onChange={(event) => handleProfileInput('height_cm', Number(event.target.value))}
              />
            </label>
            <label>
              <span>Weight (kg)</span>
              <input
                type="number"
                min="30"
                max="150"
                value={profile.weight_kg}
                onChange={(event) => handleProfileInput('weight_kg', Number(event.target.value))}
              />
            </label>
            <label>
              <span>Body shape</span>
              <select
                value={profile.body_shape}
                onChange={(event) => handleProfileInput('body_shape', event.target.value)}
              >
                <option value="pear">Pear</option>
                <option value="hourglass">Hourglass</option>
                <option value="straight">Straight</option>
                <option value="apple">Apple</option>
              </select>
            </label>
            <label>
              <span>Foot type</span>
              <select
                value={profile.foot_type}
                onChange={(event) => handleProfileInput('foot_type', event.target.value)}
              >
                <option value="flat_foot">Flat foot</option>
                <option value="neutral">Neutral</option>
                <option value="high_arch">High arch</option>
              </select>
            </label>
            <label className="wide-field">
              <span>Preferred colors</span>
              <input
                type="text"
                value={profile.preferred_colors.join(', ')}
                onChange={(event) =>
                  handleProfileInput(
                    'preferred_colors',
                    event.target.value
                      .split(',')
                      .map((color) => color.trim().toLowerCase())
                      .filter(Boolean),
                  )
                }
              />
            </label>
            <label>
              <span>Max hem below knee (in)</span>
              <input
                type="number"
                step="0.1"
                min="0"
                max="4"
                value={profile.max_hem_below_knee_in}
                onChange={(event) => handleProfileInput('max_hem_below_knee_in', Number(event.target.value))}
              />
            </label>
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={profile.formal_wear_black_disfavored}
                onChange={(event) => handleProfileInput('formal_wear_black_disfavored', event.target.checked)}
              />
              <span>Disfavor black office formal</span>
            </label>
            <label className="checkbox-field">
              <input
                type="checkbox"
                checked={profile.min_sleeve_required}
                onChange={(event) => handleProfileInput('min_sleeve_required', event.target.checked)}
              />
              <span>Require sleeves</span>
            </label>
          </div>

          {profileSaveState ? <p className="profile-save-status">{profileSaveState}</p> : null}
        </div>

        <div className="toolbar">
          <label className="field-label" htmlFor="retailer-select">
            Retailer
          </label>
          <select
            id="retailer-select"
            value={selectedRetailer}
            onChange={(event) => setSelectedRetailer(event.target.value)}
            className="select-input"
          >
            {retailerOptions.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <label className="field-label" htmlFor="links-input">
          Product links
        </label>
        <textarea
          id="links-input"
          value={urlsText}
          onChange={(event) => setUrlsText(event.target.value)}
          rows={5}
          className="link-input"
          placeholder="Paste one or more Amazon or Fable Street product links, one per line"
        />

        <div className="action-row">
          <button type="button" onClick={handleEvaluate} className="primary-btn">
            Evaluate retailer links
          </button>
          <button type="button" onClick={handleCuratedSearch} className="secondary-btn">
            Generate curated feed
          </button>
          <button type="button" onClick={handleEvaluateSingleProduct} className="secondary-btn">
            Test sample product
          </button>
        </div>

        <p className="status" role="status" aria-live="polite">
          {status}
        </p>

        <div className="scorecard" role="status" aria-live="polite" aria-atomic="true">
          <div className="score-row">
            <span className="label">Decision</span>
            <strong className={`decision ${result.decision.toLowerCase()}`}>{result.decision}</strong>
          </div>
          <div className="score-row">
            <span className="label">Score</span>
            <strong>{result.score}/100</strong>
          </div>
        </div>

        <h2>Summary</h2>
        <p>{result.summary}</p>

        <div className="table-wrap">
          <table>
            <caption className="sr-only">Retailer product evaluation results</caption>
            <thead>
              <tr>
                <th scope="col">Product</th>
                <th scope="col">Brand</th>
                <th scope="col">Decision</th>
                <th scope="col">Score</th>
              </tr>
            </thead>
            <tbody>
              {results.length === 0 ? (
                <tr>
                  <td colSpan="4">No results yet. Paste a retailer link to begin evaluating.</td>
                </tr>
              ) : (
                results.map((item, index) => (
                  <tr key={`${item.title}-${index}`}>
                    <td>{item.title}</td>
                    <td>{item.brand}</td>
                    <td>
                      <span className={`decision pill ${String(item.decision).toLowerCase()}`}>
                        {item.decision}
                      </span>
                    </td>
                    <td>{item.score ?? '—'}</td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </section>
    </main>
  )
}
