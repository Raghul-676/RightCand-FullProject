import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import api from '../services/api'
import { useAuth } from '../services/AuthContext'

export default function ProfileSetup() {
  const [form, setForm] = useState({ 
    leetcode_username: '', 
    codeforces_handle: '', 
    github_username: '',
  })
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const { markSetupDone, user, logout } = useAuth()
  const navigate = useNavigate()

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    if (!form.leetcode_username.trim()) {
      setError('LeetCode Username is compulsory')
      return
    }
    setSaving(true)
    try {
      await api.post('/profile/setup', form)
      markSetupDone()
      navigate('/my-profile')
    } catch (err) {
      setError(err.response?.data?.detail || 'Setup failed. Please try again.')
    } finally {
      setSaving(false)
    }
  }

  const f = (key) => ({
    value: form[key],
    onChange: (e) => setForm({ ...form, [key]: e.target.value }),
  })

  const platforms = [
    { key: 'leetcode_username', label: 'LeetCode Username (Compulsory)', icon: '🟡', placeholder: 'e.g. john_doe', color: '#ffa116' },
    { key: 'codeforces_handle', label: 'Codeforces Handle (Optional)', icon: '🔵', placeholder: 'e.g. tourist', color: '#3b82f6' },
    { key: 'github_username', label: 'GitHub Username (Optional)', icon: '⚫', placeholder: 'e.g. torvalds', color: '#10b981' },
  ]

  return (
    <div className="auth-wrapper">
      <img src="/sece_logo.png" alt="Sri Eshwar College of Engineering" className="auth-logo" />

      <div className="glass-card">
        <div style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--primary-dark)', marginBottom: '0.25rem' }}>
            Set Up Your Profile
          </h2>
          <p style={{ color: 'var(--muted)', fontSize: '0.85rem' }}>
            Hi <strong style={{ color: 'var(--primary)' }}>{user?.username}</strong>! Link your coding accounts below.
          </p>
        </div>

        <form onSubmit={handleSubmit}>
          {platforms.map(({ key, label, icon, placeholder, color }) => (
            <div className="form-group" key={key}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.8rem', fontWeight: 700 }}>
                <span>{icon}</span> {label}
              </label>
              <input
                {...f(key)}
                placeholder={placeholder}
                style={{ borderLeft: `3px solid ${color}`, borderRadius: '9999px' }}
              />
            </div>
          ))}

          {error && <p className="error-msg" style={{ textAlign: 'center' }}>{error}</p>}

          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginTop: '1.5rem' }}>
            <button
              type="button"
              className="btn-outline"
              onClick={() => { logout(); navigate('/login') }}
              style={{ width: '100%' }}
            >
              Logout
            </button>
            <button
              type="submit"
              className="btn-primary"
              disabled={saving}
              style={{ width: '100%' }}
            >
              {saving ? 'Saving...' : 'Save'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
