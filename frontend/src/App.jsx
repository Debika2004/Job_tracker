import { useState, useEffect, useCallback } from 'react'
import './App.css'

const API_BASE = import.meta.env.VITE_API_URL || ''

async function apiFetch(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options)
  const body = await res.json()
  if (!res.ok) throw new Error(body.detail || `HTTP ${res.status}`)
  return body
}

function ConnectGmailCard() {
  const [authUrl, setAuthUrl] = useState('')
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const startOAuth = async () => {
    setLoading(true)
    setError('')
    setAuthUrl('')
    try {
      const data = await apiFetch('/api/gmail/oauth/start')
      setAuthUrl(data.auth_url)
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>📧 Connect Gmail</h2>
      <p>Authorize your Gmail account so the tracker can read job emails.</p>
      <button className="btn btn-primary" onClick={startOAuth} disabled={loading}>
        {loading ? 'Loading…' : 'Get Authorization URL'}
      </button>
      {authUrl && (
        <div className="auth-url-box">
          <a href={authUrl} target="_blank" rel="noopener noreferrer">
            Click here to authorize in your browser →
          </a>
        </div>
      )}
      {error && <div className="status-box status-error">{error}</div>}
    </div>
  )
}

function RunOnceCard({ onDone }) {
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')

  const runOnce = async () => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await apiFetch('/api/jobs/run-once', { method: 'POST' })
      setResult(data)
      if (onDone) onDone()
    } catch (e) {
      setError(e.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2>🔄 Manual Sync</h2>
      <p>Trigger Gmail fetch + OpenAI extraction + MongoDB save right now.</p>
      <button className="btn btn-primary" onClick={runOnce} disabled={loading}>
        {loading ? 'Running…' : 'Run Once'}
      </button>
      {result && (
        <div className="status-box status-success">
          ✓ Processed {result.processed} email(s) — {result.inserted} inserted, {result.updated ?? 0} updated
        </div>
      )}
      {error && <div className="status-box status-error">{error}</div>}
    </div>
  )
}

function HealthCard() {
  const [status, setStatus] = useState('checking…')

  useEffect(() => {
    apiFetch('/health')
      .then(() => setStatus('online'))
      .catch(() => setStatus('offline'))
  }, [])

  const cls = status === 'online' ? 'status-success' : status === 'offline' ? 'status-error' : 'status-info'

  return (
    <div className="card">
      <h2>🩺 Backend Health</h2>
      <p>Checks that the FastAPI server is reachable.</p>
      <div className={`status-box ${cls}`}>
        Backend is <strong>{status}</strong>
      </div>
    </div>
  )
}

function JobsTable({ jobs }) {
  if (!jobs || jobs.length === 0) {
    return (
      <div className="empty-state">
        <div className="icon">📂</div>
        <p>No jobs found. Run a sync to populate this list.</p>
      </div>
    )
  }

  return (
    <div className="jobs-table-wrap">
      <table>
        <thead>
          <tr>
            <th>Company</th>
            <th>Role</th>
            <th>Location</th>
            <th>Status</th>
            <th>Subject (email)</th>
            <th>From</th>
            <th>Processed At</th>
          </tr>
        </thead>
        <tbody>
          {jobs.map((job) => {
            const ex = job.extracted || {}
            const gmail = job.gmail || {}
            const processedAt = job.processed_at
              ? new Date(job.processed_at).toLocaleString()
              : '—'
            return (
              <tr key={job._id}>
                <td title={ex.company}>{ex.company || '—'}</td>
                <td title={ex.role}>{ex.role || '—'}</td>
                <td title={ex.location}>{ex.location || '—'}</td>
                <td>
                  {ex.status ? <span className="badge">{ex.status}</span> : '—'}
                </td>
                <td title={gmail.subject}>{gmail.subject || '—'}</td>
                <td title={gmail.from}>{gmail.from || '—'}</td>
                <td>{processedAt}</td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}

export default function App() {
  const [jobs, setJobs] = useState([])
  const [loadingJobs, setLoadingJobs] = useState(false)
  const [jobsError, setJobsError] = useState('')

  const fetchJobs = useCallback(async () => {
    setLoadingJobs(true)
    setJobsError('')
    try {
      const data = await apiFetch('/api/jobs/latest?limit=50')
      setJobs(data.jobs || [])
    } catch (e) {
      setJobsError(e.message)
    } finally {
      setLoadingJobs(false)
    }
  }, [])

  useEffect(() => { fetchJobs() }, [fetchJobs])

  return (
    <div className="app">
      <nav className="navbar">
        <span className="navbar-logo">💼</span>
        <span className="navbar-title">Job Tracker</span>
        <span className="navbar-badge">MVP</span>
      </nav>
      <main>
        <div className="card-grid">
          <HealthCard />
          <ConnectGmailCard />
          <RunOnceCard onDone={fetchJobs} />
        </div>

        <div className="section-header">
          <h2>Latest Extracted Jobs ({jobs.length})</h2>
          <button
            className="btn btn-secondary"
            onClick={fetchJobs}
            disabled={loadingJobs}
          >
            {loadingJobs ? 'Loading…' : '↻ Refresh'}
          </button>
        </div>

        {jobsError && <div className="status-box status-error" style={{ marginBottom: '1rem' }}>{jobsError}</div>}

        <JobsTable jobs={jobs} />
      </main>
    </div>
  )
}
