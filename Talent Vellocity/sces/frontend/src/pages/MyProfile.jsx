import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../services/AuthContext'

const platforms = [
  { key: 'leetcode_username', label: 'LeetCode Username', icon: '🟡', placeholder: 'e.g. john_doe', color: '#ffa116' },
  { key: 'codeforces_handle', label: 'Codeforces Handle', icon: '🔵', placeholder: 'e.g. tourist', color: '#3b82f6' },
  { key: 'github_username', label: 'GitHub Username', icon: '⚫', placeholder: 'e.g. torvalds', color: '#10b981' },
]

const COMPLEXITY_COLOR = { Advanced: '#ef4444', Intermediate: '#f59e0b', Beginner: '#10b981' }

// ── SVG Radar Chart (DSA Topic Capability) ──
function RadarChart({ data }) {
  if (!data || Object.keys(data).length === 0) return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '180px', color: 'var(--muted)' }}>
      <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{ marginBottom: '0.5rem' }}>
        <path strokeLinecap="round" strokeLinejoin="round" d="M12 3v18m9-9H3" />
      </svg>
      <span style={{ fontSize: '0.8rem' }}>No capability stats loaded</span>
    </div>
  )
  const labels = Object.keys(data)
  const values = Object.values(data)
  const max = Math.max(...values, 1)
  const n = labels.length
  const cx = 130, cy = 130, r = 90
  const levels = 4

  const angle = (i) => (Math.PI * 2 * i) / n - Math.PI / 2
  const point = (i, ratio) => ({
    x: cx + r * ratio * Math.cos(angle(i)),
    y: cy + r * ratio * Math.sin(angle(i)),
  })

  const gridPolygons = Array.from({ length: levels }, (_, l) => {
    const ratio = (l + 1) / levels
    return Array.from({ length: n }, (_, i) => point(i, ratio))
      .map(p => `${p.x},${p.y}`).join(' ')
  })

  const dataPoints = labels.map((_, i) => point(i, values[i] / max))
  const dataPolygon = dataPoints.map(p => `${p.x},${p.y}`).join(' ')

  const labelPoints = labels.map((label, i) => {
    const p = point(i, 1.2)
    return { label, x: p.x, y: p.y }
  })

  return (
    <div className="radar-wrap" style={{ marginTop: '0.5rem' }}>
      <svg viewBox="0 0 260 260">
        {gridPolygons.map((pts, i) => (
          <polygon key={i} className="radar-grid" points={pts} />
        ))}
        {Array.from({ length: n }, (_, i) => {
          const p = point(i, 1)
          return <line key={i} className="radar-axis" x1={cx} y1={cy} x2={p.x} y2={p.y} />
        })}
        <polygon className="radar-polygon" points={dataPolygon} />
        {dataPoints.map((p, i) => (
          <circle key={i} className="radar-dot" cx={p.x} cy={p.y} r={4} />
        ))}
        {labelPoints.map(({ label, x, y }, i) => (
          <text key={i} className="radar-label" x={x} y={y} textAnchor="middle" dominantBaseline="middle">
            {label.length > 12 ? label.slice(0, 11) + '…' : label}
          </text>
        ))}
      </svg>
    </div>
  )
}

// ── SVG Consistency Ring ──
function ConsistencyRing({ value, max, label, color }) {
  const r = 36, circ = 2 * Math.PI * r
  const ratio = Math.min(value / (max || 1), 1)
  const offset = circ * (1 - ratio)
  return (
    <div className="consistency-ring">
      <svg width="100" height="100" viewBox="0 0 100 100">
        <circle className="ring-bg" cx="50" cy="50" r={r} />
        <circle className="ring-fill" cx="50" cy="50" r={r}
          stroke={color}
          strokeDasharray={circ}
          strokeDashoffset={offset}
        />
      </svg>
      <div className="ring-label">
        <span className="ring-value" style={{ color }}>{value}</span>
        <span className="ring-sub">{label}</span>
      </div>
    </div>
  )
}

function ProjectCard({ repo }) {
  const stack = (() => { try { return JSON.parse(repo.stack_breakdown || '{}') } catch { return {} } })()
  const color = COMPLEXITY_COLOR[repo.complexity] || '#94a3b8'
  return (
    <div className="card" style={{ borderTop: `4px solid ${color}`, position: 'relative' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.75rem' }}>
        <div>
          <h4 style={{ fontWeight: 700, fontSize: '1.05rem', color: '#000000' }}>{repo.project_name || 'Project'}</h4>
          <span style={{ fontSize: '0.75rem', color: 'var(--muted)', wordBreak: 'break-all' }}>{repo.repo_url}</span>
        </div>
        <span style={{ background: color + '15', color, border: `1px solid ${color}40`, borderRadius: '6px', padding: '0.2rem 0.5rem', fontSize: '0.72rem', fontWeight: 700, whiteSpace: 'nowrap' }}>
          {repo.complexity}
        </span>
      </div>

      {repo.summary && (
        <p style={{ fontSize: '0.84rem', color: 'var(--muted2)', marginBottom: '1rem', lineHeight: 1.5, whiteSpace: 'pre-line' }}>
          {repo.summary}
        </p>
      )}

      {/* Tech Stack Chips */}
      {Object.keys(stack).length > 0 && (
        <div style={{ marginBottom: '1rem' }}>
          <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.4rem', fontWeight: 600 }}>Detected Stack</div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
            {Object.keys(stack).map(tech => (
              <span key={tech} className="badge badge-blue" style={{ fontSize: '0.68rem', padding: '0.15rem 0.5rem' }}>
                {tech}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Grounded / Evidence Verification Badge */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', marginTop: '1rem', paddingTop: '0.75rem', borderTop: '1px solid var(--border)' }}>
        <span style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: '16px', height: '16px', borderRadius: '50%', background: 'rgba(16, 185, 129, 0.1)', color: 'var(--success)' }}>
          <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="3">
            <polyline points="20 6 9 17 4 12" />
          </svg>
        </span>
        <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--success)' }} title="This analysis is backed by verifiable code snippet citations extracted from the repository.">
          Evidence-based
        </span>
      </div>
    </div>
  )
}

export default function MyProfile() {
  const [form, setForm] = useState({ 
    leetcode_username: '', 
    codeforces_handle: '', 
    github_username: '',
  })
  const [stats, setStats] = useState(null)
  const [statsErrors, setStatsErrors] = useState([])
  const [repoList, setRepoList] = useState([])
  const [loading, setLoading] = useState(true)
  const [loadingStats, setLoadingStats] = useState(false)
  const [saving, setSaving] = useState(false)
  const [success, setSuccess] = useState('')
  const [error, setError] = useState('')
  const [redirecting, setRedirecting] = useState(false)
  const [redirectMsg, setRedirectMsg] = useState({ title: '', desc: '' })
  const { user, logout } = useAuth()
  const navigate = useNavigate()
 
  useEffect(() => {
    // Load student profile handles
    api.get('/profile/me')
      .then(({ data }) => {
        setForm({
          leetcode_username: data.leetcode_username || '',
          codeforces_handle: data.codeforces_handle || '',
          github_username: data.github_username || '',
        })
      })
      .catch(() => {})
      .finally(() => setLoading(false))

    // Load analyzed repositories
    api.get('/projects/my-repos')
      .then(({ data }) => setRepoList(data))
      .catch(() => {})

    // Load coding stats automatically on mount if linked
    api.get('/profile/my-stats')
      .then(({ data }) => {
        setStats(data.stats)
        setStatsErrors(data.errors || [])
      })
      .catch(() => {})
  }, [])

  const fetchStats = () => {
    setLoadingStats(true); setStatsErrors([])
    api.get('/profile/my-stats')
      .then(({ data }) => {
        setStats(data.stats)
        setStatsErrors(data.errors || [])
      })
      .catch(() => setStatsErrors([{ platform: 'all', error: 'Failed to load stats' }]))
      .finally(() => setLoadingStats(false))
  }

  const handleSave = async (e) => {
    e.preventDefault(); setError(''); setSuccess(''); setSaving(true)
    try {
      await api.put('/profile/update', form)
      setSuccess('Profile credentials updated!'); setTimeout(() => setSuccess(''), 3000);
      fetchStats()
    } catch (err) { setError(err.response?.data?.detail || 'Update failed') }
    finally { setSaving(false) }
  }

  const handleHandoff = () => {
    setRedirectMsg({
      title: 'Redirecting to AI Interview Preparation Assistant...',
      desc: 'Launching multi-agent interview preparation scorecard'
    })
    setRedirecting(true)
    setTimeout(() => {
      window.location.href = `http://localhost:5174/?username=${encodeURIComponent(user?.username || '')}&userId=${user?.id || ''}`
    }, 2000)
  }

  const lc = stats?.leetcode
  const cf = stats?.codeforces
  const gh = stats?.github

  // Consistency Score variables
  const lcDays = lc?.active_days_last20 || 0
  const cfDays = cf?.active_days_last100 || 0
  const ghDays = gh?.active_days_last30 || 0

  return (
    <div style={{ background: 'var(--bg)', minHeight: '100vh' }}>
      {/* ── Transition handoff screen ── */}
      {redirecting && (
        <div className="transition-overlay">
          <div style={{ textAlign: 'center' }}>
            <img src="/sece_logo.png" alt="SECE Logo" style={{ height: '70px', marginBottom: '2rem', filter: 'brightness(0) invert(1)' }} />
            <h2 style={{ fontSize: '1.6rem', fontWeight: 700, marginBottom: '0.75rem' }}>{redirectMsg.title}</h2>
            <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: '0.9rem', marginBottom: '2rem' }}>{redirectMsg.desc}</p>
            <div className="loading" style={{ margin: '0 auto' }} />
          </div>
        </div>
      )}

      {/* ── Navbar ── */}
      <nav className="navbar">
        <div className="brand">
          <img src="/sece_logo.png" alt="Sri Eshwar College of Engineering" />
        </div>
        <nav style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          <a onClick={() => navigate('/my-profile')} className="active" style={{ cursor: 'pointer' }}>Profile</a>
          <a onClick={() => navigate('/project-analysis')} style={{ cursor: 'pointer' }}>Projects</a>
          {user?.role === 'admin' && <a onClick={() => navigate('/admin/dashboard')} style={{ cursor: 'pointer' }}>Admin</a>}
          
          <button className="btn-accent" onClick={handleHandoff} style={{ padding: '0.45rem 1.1rem', fontSize: '0.85rem' }}>
            🎯 AI Interview Prep
          </button>
          <button className="btn-outline" onClick={() => { logout(); navigate('/login') }} style={{ padding: '0.45rem 1.1rem', fontSize: '0.85rem' }}>
            Logout
          </button>
        </nav>
      </nav>

      <div className="page" style={{ maxWidth: '1040px' }}>
        
        {/* ── Profile Header Block ── */}
        <div className="card" style={{ marginBottom: '1.5rem', display: 'flex', alignItems: 'center', gap: '1.5rem', flexWrap: 'wrap' }}>
          <div style={{
            width: '64px', height: '64px', borderRadius: '16px',
            background: 'linear-gradient(135deg, var(--primary), var(--primary-light))',
            display: 'flex', alignItems: 'center', justifycenter: 'center', justifyContent: 'center',
            fontSize: '1.6rem', fontWeight: 800, color: '#fff', boxShadow: '0 8px 24px rgba(11,78,162,0.2)'
          }}>
            {user?.username ? user.username[0].toUpperCase() : 'S'}
          </div>
          <div style={{ flex: 1, minWidth: '200px' }}>
            <h2 style={{ fontSize: '1.4rem', fontWeight: 800, color: 'var(--text)' }}>{user?.username}</h2>
            <p style={{ color: 'var(--muted)', fontSize: '0.84rem', marginTop: '0.15rem' }}>Sri Eshwar Registered Student Profile</p>
          </div>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            {form.leetcode_username && <span className="badge badge-orange">🟡 Leetcode: {form.leetcode_username}</span>}
            {form.codeforces_handle && <span className="badge badge-blue">🔵 Codeforces: {form.codeforces_handle}</span>}
            {form.github_username && <span className="badge badge-green">🟢 GitHub: {form.github_username}</span>}
          </div>
        </div>

        {/* ── Top grid: Credentials update + Stats refresh ── */}
        <div style={{ display: 'grid', gridTemplateColumns: '1.1fr 0.9fr', gap: '1.5rem', alignItems: 'start', marginBottom: '1.5rem' }} className="profile-grid">
          
          {/* Form */}
          <div className="card">
            <h3 style={{ fontWeight: 700, marginBottom: '1.25rem', fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Linked Accounts</h3>
            {loading ? <div className="loading" style={{ padding: '1rem' }} /> : (
              <form onSubmit={handleSave}>
                {platforms.map(({ key, label, icon, placeholder, color }) => (
                  <div className="form-group" key={key}>
                    <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 700, color: 'var(--primary-dark)' }}>
                      {icon} {label}
                    </label>

                    <input
                      value={form[key]}
                      onChange={(e) => setForm({ ...form, [key]: e.target.value })}
                      placeholder={placeholder}
                      style={{ borderLeft: `3px solid ${color}`, borderRadius: '9999px' }}
                    />
                  </div>
                ))}
                {error && <p className="error-msg">{error}</p>}
                {success && <p className="success-msg">✓ {success}</p>}
                <button type="submit" className="btn-primary" disabled={saving} style={{ width: '100%', marginTop: '1rem' }}>
                  {saving ? 'Saving...' : 'Update Links'}
                </button>
              </form>
            )}
          </div>

          {/* Stats triggers */}
          <div className="card" style={{ display: 'flex', flexDirection: 'column', height: '100%', justifyContent: 'space-between', minHeight: '310px' }}>
            <div>
              <h3 style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.75rem' }}>Evaluation Metrics</h3>
              <p style={{ fontSize: '0.84rem', color: 'var(--muted2)', lineHeight: 1.5 }}>
                Sync and compile stats across your LeetCode, Codeforces, and GitHub profiles. Re-evaluates consistency metrics, active days streaks, and DSA capabilities dynamically.
              </p>
            </div>
            
            <div style={{ marginTop: '1.5rem' }}>
              {loadingStats ? <div className="loading" style={{ padding: '1rem' }} /> : (
                <button className="btn-accent" onClick={fetchStats} disabled={loadingStats} style={{ width: '100%' }}>
                  {stats ? '↻ Refresh Coding Stats' : '▶ Pull Live Metrics'}
                </button>
              )}
              {statsErrors.length > 0 && (
                <p className="error-msg" style={{ marginTop: '0.5rem', fontSize: '0.78rem' }}>
                  Sync issues on: {statsErrors.map(e => e.platform).join(', ')}
                </p>
              )}
            </div>
          </div>
        </div>

        {/* ── Second row: Radar Chart & Consistency Rings ── */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem', marginBottom: '1.5rem' }} className="profile-grid">
            
            {/* Radar chart */}
            <div className="card" style={{ textAlign: 'center' }}>
              <h3 style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1rem' }}>
                Topic Capability (DSA Spectrum)
              </h3>
              <RadarChart data={stats.topics} />
            </div>

            {/* Consistency indicators */}
            <div className="card">
              <h3 style={{ fontWeight: 700, fontSize: '0.85rem', color: 'var(--muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '1.5rem' }}>
                Consistency Metrics
              </h3>
              <div style={{ display: 'flex', justifyContent: 'space-around', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
                <ConsistencyRing value={lcDays} max={20} label="LeetCode" color="#ffa116" />
                <ConsistencyRing value={cfDays} max={100} label="Codeforces" color="#3b82f6" />
                <ConsistencyRing value={ghDays} max={30} label="GitHub" color="#10b981" />
              </div>
              <p style={{ color: 'var(--muted)', fontSize: '0.78rem', marginTop: '1.5rem', textAlign: 'center', lineHeight: 1.4 }}>
                Active streak counts representing your code contribution, commits, and submissions over recent periods.
              </p>
            </div>
          </div>
        )}

        {/* ── LeetCode & Codeforces Profile Cards Row ── */}
        {stats && (
          <div style={{ display: 'grid', gridTemplateColumns: '1.2fr 0.8fr', gap: '1.5rem', marginBottom: '2rem' }} className="profile-grid">
            
            {/* LeetCode Custom Card */}
            {lc && (
              <div className="card">
                {/* Header */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                    <span style={{ fontSize: '1.2rem' }}>🟡</span>
                    <h3 style={{ fontWeight: 800, fontSize: '1rem', color: 'var(--primary-dark)', margin: 0 }}>
                      LeetCode Stats ({lc.username})
                    </h3>
                  </div>
                  <span style={{ color: 'var(--muted)', fontSize: '0.8rem', fontWeight: 700 }}>
                    Rank: #{lc.ranking || 'N/A'}
                  </span>
                </div>

                {/* Main Body */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.25rem' }}>
                  {/* Easy */}
                  <div style={{ background: 'rgba(16, 185, 129, 0.05)', border: '1px solid rgba(16, 185, 129, 0.15)', borderRadius: '8px', padding: '0.75rem', textAlign: 'center' }}>
                    <div style={{ fontWeight: 800, color: '#10b981', fontSize: '1.1rem' }}>{lc.easy_solved} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--muted2)' }}>/ {lc.total_easy}</span></div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', marginTop: '0.2rem', fontWeight: 600 }}>Easy</div>
                  </div>

                  {/* Medium */}
                  <div style={{ background: 'rgba(245, 158, 11, 0.05)', border: '1px solid rgba(245, 158, 11, 0.15)', borderRadius: '8px', padding: '0.75rem', textAlign: 'center' }}>
                    <div style={{ fontWeight: 800, color: '#f59e0b', fontSize: '1.1rem' }}>{lc.medium_solved} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--muted2)' }}>/ {lc.total_medium}</span></div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', marginTop: '0.2rem', fontWeight: 600 }}>Medium</div>
                  </div>

                  {/* Hard */}
                  <div style={{ background: 'rgba(239, 68, 68, 0.05)', border: '1px solid rgba(239, 68, 68, 0.15)', borderRadius: '8px', padding: '0.75rem', textAlign: 'center' }}>
                    <div style={{ fontWeight: 800, color: '#ef4444', fontSize: '1.1rem' }}>{lc.hard_solved} <span style={{ fontSize: '0.75rem', fontWeight: 500, color: 'var(--muted2)' }}>/ {lc.total_hard}</span></div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--muted)', textTransform: 'uppercase', marginTop: '0.2rem', fontWeight: 600 }}>Hard</div>
                  </div>
                </div>

                {/* Footer Details */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem', borderTop: '1px solid var(--border)', paddingTop: '1rem', textAlign: 'center' }}>
                  <div>
                    <div style={{ color: 'var(--muted)', fontSize: '0.7rem', marginBottom: '0.15rem', fontWeight: 600 }}>Rating</div>
                    <div style={{ fontWeight: 800, color: 'var(--text)', fontSize: '1rem' }}>{lc.contest_rating}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--muted)', fontSize: '0.7rem', marginBottom: '0.15rem', fontWeight: 600 }}>Highest Rating</div>
                    <div style={{ fontWeight: 800, color: '#ffb300', fontSize: '1rem' }}>{lc.highest_rating}</div>
                  </div>
                  <div>
                    <div style={{ color: 'var(--muted)', fontSize: '0.7rem', marginBottom: '0.15rem', fontWeight: 600 }}>Contest Percentile</div>
                    <div style={{ fontWeight: 800, color: 'var(--text)', fontSize: '0.95rem' }}>
                      {lc.global_ranking ? `${lc.top_percentage}%` : 'N/A'}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Other Stats Overview */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
              {/* Codeforces summary card */}
              <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1.2rem' }}>🔵</span>
                  <h4 style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--muted)' }}>CODEFORCES RATING</h4>
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--primary)' }}>
                  {cf?.rating || 0}
                </div>
                {cf && (
                  <p style={{ fontSize: '0.75rem', color: 'var(--muted2)', marginTop: '0.25rem' }}>
                    Rank: <strong style={{ color: 'var(--text)' }}>{cf.rank}</strong> | Solved: <strong style={{ color: 'var(--text)' }}>{cf.total_solved}</strong> problems
                  </p>
                )}
              </div>

              {/* Repos count card */}
              <div className="card" style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem' }}>
                  <span style={{ fontSize: '1.2rem' }}>🔍</span>
                  <h4 style={{ fontWeight: 700, fontSize: '0.9rem', color: 'var(--muted)' }}>REPOSITORIES ANALYZED</h4>
                </div>
                <div style={{ fontSize: '2rem', fontWeight: 800, color: 'var(--success)' }}>
                  {repoList.length}
                </div>
                <p style={{ fontSize: '0.75rem', color: 'var(--muted2)', marginTop: '0.25rem' }}>
                  Engineered portfolios with dynamic complexity classifications.
                </p>
              </div>
            </div>

          </div>
        )}


        {/* ── Fourth Row: Analyzed Projects Grid ── */}
        <div>
          <h2 style={{ fontWeight: 800, fontSize: '1.25rem', color: '#FFFFFF', marginBottom: '1rem', textShadow: '0 2px 4px rgba(0,0,0,0.15)' }}>🔍 Analyzed Portfolios</h2>
          {repoList.length > 0 ? (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(320px, 1fr))', gap: '1.25rem' }}>
              {repoList.map(repo => <ProjectCard key={repo.id} repo={repo} />)}
            </div>
          ) : (
            <div className="card" style={{ padding: '2rem', textAlign: 'center' }}>
              <p style={{ color: 'var(--muted)', fontSize: '0.88rem' }}>No projects analyzed yet. Head over to the Projects tab to add repositories.</p>
            </div>
          )}
        </div>

      </div>
    </div>
  )
}
