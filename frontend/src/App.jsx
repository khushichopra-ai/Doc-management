import { useEffect, useMemo, useState } from 'react'
import './App.css'

// ── Bespoke duotone icon system (custom-drawn, 24px grid) ──────────────
// `f` = soft silhouette layer, `d` = crisp outline. Both inherit color and
// shift to a violet→cyan gradient on active/hover via CSS (url(#aka-line)).
const Ico = ({ f, d, s = 20 }) => (
  <svg viewBox="0 0 24 24" width={s} height={s} fill="none" aria-hidden="true" className="ico">
    {f ? <path className="duo-fill" d={f} /> : null}
    {(Array.isArray(d) ? d : [d]).map((p, i) => (
      <path key={i} className="duo-line" d={p} strokeLinecap="round" strokeLinejoin="round" />
    ))}
  </svg>
)

const ICONS = {
  // Overview — a 4-panel grid with one live tile
  overview: (
    <Ico
      f="M5.5 4.5h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z"
      d={[
        'M5.5 4.5h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z',
        'M14.5 4.5h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z',
        'M14.5 13.5h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z',
        'M5.5 13.5h4a1 1 0 0 1 1 1v4a1 1 0 0 1-1 1h-4a1 1 0 0 1-1-1v-4a1 1 0 0 1 1-1z',
      ]}
    />
  ),
  // Library — a document with a folded corner
  library: (
    <Ico
      f="M9 3.5h4.2L18 8.3V18a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V5.5a2 2 0 0 1 2-2z"
      d={[
        'M9 3.5h4.2L18 8.3V18a2 2 0 0 1-2 2H9a2 2 0 0 1-2-2V5.5a2 2 0 0 1 2-2z',
        'M13 3.7V8h4.3',
        'M10.5 12.5h5',
        'M10.5 15.5h3',
      ]}
    />
  ),
  // Assistant — a chat bubble carrying an AI spark
  assistant: (
    <Ico
      f="M7 4.5h10a2.5 2.5 0 0 1 2.5 2.5v5a2.5 2.5 0 0 1-2.5 2.5h-4l-4.5 3.2V14.5H7A2.5 2.5 0 0 1 4.5 12V7A2.5 2.5 0 0 1 7 4.5z"
      d={[
        'M7 4.5h10a2.5 2.5 0 0 1 2.5 2.5v5a2.5 2.5 0 0 1-2.5 2.5h-4l-4.5 3.2V14.5H7A2.5 2.5 0 0 1 4.5 12V7A2.5 2.5 0 0 1 7 4.5z',
        'M12 7.6l.8 2 2 .8-2 .8-.8 2-.8-2-2-.8 2-.8z',
      ]}
    />
  ),
  // Access — a key (governed permission), not a delivery truck
  requests: (
    <Ico
      f="M15 5.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z"
      d={[
        'M15 5.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z',
        'M12.6 11.4 6 18',
        'M9.2 14.8l1.8 1.8',
        'M6 18l1.7 1.7',
      ]}
    />
  ),
}

// Inline glyphs used inside buttons / chips (inherit the element's color).
const G = {
  upload: (
    <Ico s={16} f="M5.5 15.5h13v2.5a1.5 1.5 0 0 1-1.5 1.5H7a1.5 1.5 0 0 1-1.5-1.5z"
      d={['M12 15.5V5', 'M8.2 8.8 12 5l3.8 3.8', 'M5.5 15.5v3a1.5 1.5 0 0 0 1.5 1.5h10a1.5 1.5 0 0 0 1.5-1.5v-3']} />
  ),
  trash: (
    <Ico s={16} f="M6.6 7.5h10.8l-.9 11a2 2 0 0 1-2 1.8H9.5a2 2 0 0 1-2-1.8z"
      d={['M4.5 7.5h15', 'M9.5 7.5V5.6a1.5 1.5 0 0 1 1.5-1.5h2a1.5 1.5 0 0 1 1.5 1.5V7.5', 'M7 7.5l.9 11.2a2 2 0 0 0 2 1.8h4.2a2 2 0 0 0 2-1.8L17 7.5', 'M10.5 11v6', 'M13.5 11v6']} />
  ),
  key: (
    <Ico s={16} f="M15 5.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z"
      d={['M15 5.5a3.5 3.5 0 1 1 0 7 3.5 3.5 0 0 1 0-7z', 'M12.6 11.4 6 18', 'M9.2 14.8l1.8 1.8', 'M6 18l1.7 1.7']} />
  ),
  send: <Ico s={16} d={['M5 12h12.5', 'M12.5 6.5 19 12l-6.5 5.5']} />,
  refresh: <Ico s={16} d={['M19.5 12a7.5 7.5 0 1 1-2.2-5.3', 'M19.5 4.2v3.6h-3.6']} />,
  signout: <Ico s={15} d={['M14 5h3a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2h-3', 'M10 8l-4 4 4 4', 'M6 12h9']} />,
  check: <Ico s={16} d={['M5 12.5 10 17 19 7']} />,
  close: <Ico s={16} d={['M7 7l10 10', 'M17 7 7 17']} />,
  lock: (
    <Ico s={14} f="M6.5 11h11a1 1 0 0 1 1 1v6.5a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1V12a1 1 0 0 1 1-1z"
      d={['M8 11V8.5a4 4 0 0 1 8 0V11', 'M6.5 11h11a1 1 0 0 1 1 1v6.5a1 1 0 0 1-1 1h-11a1 1 0 0 1-1-1V12a1 1 0 0 1 1-1z']} />
  ),
  spark: (
    <Ico s={14} f="M12 4l1.7 4.8 4.8 1.7-4.8 1.7L12 17l-1.7-4.8L5.5 10.5l4.8-1.7z"
      d={['M12 4l1.7 4.8 4.8 1.7-4.8 1.7L12 17l-1.7-4.8L5.5 10.5l4.8-1.7z']} />
  ),
}

// Gradient defs referenced by icons / brand mark (rendered once, invisibly).
const GradientDefs = () => (
  <svg width="0" height="0" aria-hidden="true" style={{ position: 'absolute' }}>
    <defs>
      <linearGradient id="aka-line" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stopColor="#a78bff" />
        <stop offset="1" stopColor="#3ee0e6" />
      </linearGradient>
      <radialGradient id="aka-orb" cx="0.34" cy="0.28" r="0.85">
        <stop offset="0" stopColor="#c5b3ff" />
        <stop offset="0.5" stopColor="#7c5cff" />
        <stop offset="1" stopColor="#23c8d6" />
      </radialGradient>
    </defs>
  </svg>
)

// Orbital orb — the AKA brand mark (replaces the old text-in-a-box logo).
const BrandMark = ({ size = 38 }) => (
  <svg width={size} height={size} viewBox="0 0 40 40" fill="none" aria-hidden="true" className="brandmark">
    <circle cx="20" cy="20" r="13" fill="url(#aka-orb)" opacity="0.22" />
    <circle cx="20" cy="20" r="13" stroke="url(#aka-line)" strokeWidth="1.5" />
    <circle cx="20" cy="20" r="5.4" fill="url(#aka-orb)" />
    <ellipse cx="20" cy="20" rx="17.5" ry="7" stroke="url(#aka-line)" strokeWidth="1.3" opacity="0.65" transform="rotate(-26 20 20)" />
    <circle cx="33.6" cy="13" r="2.2" fill="#52e8ea" />
  </svg>
)

// Orbital spark — the AI assistant's avatar (replaces the literal text "AKA").
const AssistantMark = () => (
  <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
    <circle cx="12" cy="12" r="3.8" fill="url(#aka-orb)" />
    <ellipse cx="12" cy="12" rx="9" ry="3.8" stroke="url(#aka-line)" strokeWidth="1.4" opacity="0.85" transform="rotate(-28 12 12)" />
    <circle cx="19.5" cy="7.6" r="1.5" fill="#52e8ea" />
  </svg>
)

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Overview', icon: ICONS.overview },
  { key: 'documents', label: 'Library', icon: ICONS.library },
  { key: 'chat', label: 'Assistant', icon: ICONS.assistant },
  { key: 'requests', label: 'Access', icon: ICONS.requests },
]

// Soft accent rotation for department monograms (visual only).
const DEPT_ACCENTS = ['violet', 'blue', 'emerald', 'amber', 'rose']

// Per-department glyphs (custom duotone, inherit the tile's accent color).
const DEPT_GLYPHS = {
  // AI Team — a CPU/neural core
  'ai-team': (
    <Ico s={18} f="M9.5 9.5h5v5h-5z"
      d={['M7 7h10v10H7z', 'M9.5 9.5h5v5h-5z', 'M10 4v3M14 4v3M10 17v3M14 17v3', 'M4 10h3M4 14h3M17 10h3M17 14h3']} />
  ),
  // AI Showcases — twin sparkles
  'ai-showcases': (
    <Ico s={18} f="M10 3.5l1.5 4.3 4.3 1.5-4.3 1.5L10 15l-1.5-4.2L4.2 9.3l4.3-1.5z"
      d={['M10 3.5l1.5 4.3 4.3 1.5-4.3 1.5L10 15l-1.5-4.2L4.2 9.3l4.3-1.5z', 'M17 14l.7 1.9 1.9.7-1.9.7-.7 1.9-.7-1.9-1.9-.7 1.9-.7z']} />
  ),
  // CeFi — a bank (centralized)
  cefi: (
    <Ico s={18} f="M5 10h14v8H5z"
      d={['M4 10l8-5 8 5', 'M6 10v7M10 10v7M14 10v7M18 10v7', 'M4 19.5h16']} />
  ),
  // DeFi — a node network (decentralized)
  defi: (
    <Ico s={18} f="M6.6 5.4a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4z"
      d={['M6.6 5.4a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4z', 'M17 7a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4z', 'M11 14.4a2.2 2.2 0 1 1 0 4.4 2.2 2.2 0 0 1 0-4.4z', 'M8.7 8.4 15 9M8.4 9.6 10.4 14.4M16 11.2 12.6 15']} />
  ),
  // Sales — a rising trend
  sales: (
    <Ico s={18} f="M4 15l5-5 3 3 7-7V19H4z"
      d={['M4 15l5-5 3 3 7-7', 'M15 6h4v4']} />
  ),
  _fallback: (
    <Ico s={18} f="M12 4l8 4-8 4-8-4z"
      d={['M12 4l8 4-8 4-8-4z', 'M4 12l8 4 8-4', 'M4 16l8 4 8-4']} />
  ),
}
const deptGlyph = (slug) => DEPT_GLYPHS[slug] || DEPT_GLYPHS._fallback

// Same-origin via the Vite dev proxy; HttpOnly access/refresh cookies ride along.
const API_BASE = '/api'

const INSUFFICIENT = 'I do not have enough information'

function formatBytes(bytes) {
  if (bytes < 1024) return `${bytes} B`
  const units = ['KB', 'MB', 'GB']
  let value = bytes / 1024
  let unitIndex = 0
  while (value >= 1024 && unitIndex < units.length - 1) {
    value /= 1024
    unitIndex += 1
  }
  return `${value.toFixed(1)} ${units[unitIndex]}`
}

async function api(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    credentials: 'include', // send HttpOnly auth cookies
    ...options,
  })
  const contentType = response.headers.get('content-type') || ''
  const data = contentType.includes('application/json') ? await response.json() : null
  if (!response.ok) {
    const message = data?.detail || response.statusText || 'Request failed'
    throw new Error(message)
  }
  return data
}

const jsonPost = (path, body) => api(path, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

function Chip({ children, tone = 'neutral' }) {
  return <span className={`chip chip-${tone}`}>{children}</span>
}

function Card({ title, subtitle, actions, children, className = '' }) {
  return (
    <section className={`card ${className}`}>
      <div className="card-head">
        <div>
          <h2>{title}</h2>
          {subtitle ? <p className="muted">{subtitle}</p> : null}
        </div>
        {actions ? <div className="card-actions">{actions}</div> : null}
      </div>
      {children}
    </section>
  )
}

function App() {
  // Session lives only in React state (no localStorage/sessionStorage, per spec).
  const [user, setUser] = useState(null)
  const [departments, setDepartments] = useState([])
  const [department, setDepartment] = useState('')

  const [activeTab, setActiveTab] = useState('dashboard')
  const [loginUsername, setLoginUsername] = useState('')
  const [loginPassword, setLoginPassword] = useState('')
  const [busy, setBusy] = useState(false)
  const [notice, setNotice] = useState('')
  const [error, setError] = useState('')
  const [documents, setDocuments] = useState([])
  const [chatQuestion, setChatQuestion] = useState('')
  const [messages, setMessages] = useState([])
  const [chatLoading, setChatLoading] = useState(false)
  const [chatError, setChatError] = useState('')
  const [uploadFile, setUploadFile] = useState(null)
  const [uploadSensitivity, setUploadSensitivity] = useState('open')
  const [requestText, setRequestText] = useState('')
  const [requestReason, setRequestReason] = useState('')
  const [requestDocumentId, setRequestDocumentId] = useState('')
  const [requestStatus, setRequestStatus] = useState('')
  const [notifications, setNotifications] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  // Requests the lead has decided this session — kept visible (with their
  // outcome) since the pending endpoint only returns still-pending requests.
  const [decidedRequests, setDecidedRequests] = useState([])

  // Account registration + Lead contributor-approval workflow.
  const [authScreen, setAuthScreen] = useState('login') // 'login' | 'register'
  const [regName, setRegName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regRole, setRegRole] = useState('viewer')
  const [regMessage, setRegMessage] = useState('')
  const [regError, setRegError] = useState('')
  const [pendingContributors, setPendingContributors] = useState([])
  // Contributors decided this session — kept visible with their outcome.
  const [decidedContributors, setDecidedContributors] = useState([])

  const isAccountLead = user?.role === 'lead'

  const currentDepartment = useMemo(
    () => departments.find((item) => item.dept_slug === department) || null,
    [departments, department],
  )
  const role = currentDepartment?.role || 'viewer'
  const visibleDepartments = departments

  useEffect(() => {
    if (user && department) {
      refreshAll()
      setMessages([]) // fresh chat thread per department
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user, department])

  useEffect(() => {
    if (isAccountLead) loadPendingContributors()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user])

  // Auto-dismiss the toast banners after 4 seconds.
  useEffect(() => {
    if (!notice) return undefined
    const t = setTimeout(() => setNotice(''), 4000)
    return () => clearTimeout(t)
  }, [notice])

  useEffect(() => {
    if (!error) return undefined
    const t = setTimeout(() => setError(''), 4000)
    return () => clearTimeout(t)
  }, [error])

  async function refreshAll() {
    if (!user || !department) return
    try {
      const [docs, notifs, pending] = await Promise.all([
        api(`/documents/?department=${encodeURIComponent(department)}`),
        api('/notifications/').catch(() => []),
        role === 'lead' ? api('/requests/pending/').catch(() => []) : Promise.resolve([]),
      ])
      setDocuments(docs)
      setNotifications(notifs)
      setPendingRequests(pending)
    } catch (err) {
      setError(err.message)
    }
  }

  async function loadPendingContributors() {
    try {
      setPendingContributors(await api('/contributors/pending/'))
    } catch {
      setPendingContributors([])
    }
  }

  async function handleRegister(event) {
    event.preventDefault()
    setRegError('')
    setRegMessage('')
    setBusy(true)
    try {
      const res = await jsonPost('/auth/register/', {
        name: regName.trim(),
        email: regEmail.trim(),
        password: regPassword,
        role: regRole,
      })
      setRegMessage(res.detail)
      setRegName(''); setRegEmail(''); setRegPassword('')
      if (regRole === 'viewer') {
        // Viewers are active immediately — prefill the login form.
        setLoginUsername(regEmail.trim())
      }
    } catch (err) {
      setRegError(err.message)
    } finally {
      setBusy(false)
    }
  }

  async function decideContributor(contributor, action) {
    try {
      await jsonPost(`/contributors/${contributor.id}/${action}/`, {})
      setDecidedContributors((prev) => [
        { ...contributor, decidedStatus: action === 'approve' ? 'approved' : 'rejected' },
        ...prev.filter((c) => c.id !== contributor.id),
      ])
      await loadPendingContributors()
      setNotice(`Contributor ${action === 'approve' ? 'approved' : 'rejected'}.`)
    } catch (err) {
      setError(err.message)
    }
  }

  async function loadUser(username, password) {
    setBusy(true)
    setError('')
    setNotice('')
    try {
      const data = await jsonPost('/login/', { username, password })
      setUser(data.user)
      const depts = data.departments || []
      setDepartments(depts)
      setDepartment(depts[0]?.dept_slug || '')
      setActiveTab('dashboard')
      setLoginPassword('')
      setMessages([])
      setNotice(`Signed in as ${data.user.name || data.user.username}.`)
    } catch (err) {
      // Surface the backend message (e.g. awaiting approval / rejected).
      setError(err.message || 'Invalid username or password.')
    } finally {
      setBusy(false)
    }
  }

  function handleLogin(event) {
    event.preventDefault()
    loadUser(loginUsername.trim(), loginPassword)
  }

  async function logout() {
    try {
      await api('/logout/', { method: 'POST' })
    } catch {
      /* ignore */
    }
    setUser(null)
    setDepartments([])
    setDepartment('')
    setDocuments([])
    setNotifications([])
    setPendingRequests([])
    setDecidedRequests([])
    setDecidedContributors([])
  }

  async function handleUpload(event) {
    event.preventDefault()
    if (!uploadFile) return
    setError('')
    setNotice('')
    setBusy(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('department', department)
      formData.append('sensitivity', uploadSensitivity)
      await api('/documents/upload/', { method: 'POST', body: formData })
      setUploadFile(null)
      event.target.reset()
      setNotice('Document uploaded.')
      await refreshAll()
    } catch (err) {
      setError(`Upload failed: ${err.message}`)
    } finally {
      setBusy(false)
    }
  }

  async function handleDelete(documentId) {
    try {
      await api(`/documents/${documentId}/`, { method: 'DELETE' })
      await refreshAll()
    } catch (err) {
      setError(err.message)
    }
  }

  async function handleChat(event) {
    event.preventDefault()
    const question = chatQuestion.trim()
    if (!question) return
    setChatError('')
    setMessages((prev) => [...prev, { role: 'user', text: question }])
    setChatQuestion('')
    setChatLoading(true)
    try {
      // Same API contract: a single stateless query per send (no history sent).
      const data = await jsonPost('/chat/query/', { question, department })
      setMessages((prev) => [
        ...prev,
        {
          role: 'assistant',
          text: data.answer,
          sources: data.sources || [],
          question,
          insufficient: (data.answer || '').includes(INSUFFICIENT),
        },
      ])
    } catch (err) {
      setChatError(err.message)
      setMessages((prev) => [...prev, { role: 'assistant', text: err.message, error: true }])
    } finally {
      setChatLoading(false)
    }
  }

  // Pre-fill and open the request form (from a greyed document or an insufficient answer).
  function startRequest({ documentId = '', text = '' } = {}) {
    setRequestDocumentId(documentId)
    setRequestText(text)
    setRequestReason('')
    setRequestStatus('')
    setActiveTab('requests')
  }

  async function createRequest(event) {
    event.preventDefault()
    setRequestStatus('')
    try {
      const data = await jsonPost('/requests/', {
        request_text: requestText,
        reason: requestReason,
        department,
        document_id: requestDocumentId || null,
      })
      setRequestStatus(`Request ${data.status} for ${data.department}.`)
      setRequestText('')
      setRequestReason('')
      setRequestDocumentId('')
      await refreshAll()
    } catch (err) {
      setRequestStatus(err.message)
    }
  }

  async function approveRequest(item) {
    try {
      await jsonPost(`/requests/${item.id}/approve/`, { note: 'Approved by lead.' })
      setDecidedRequests((prev) => [{ ...item, decidedStatus: 'approved' }, ...prev.filter((r) => r.id !== item.id)])
      await refreshAll()
    } catch (err) {
      setError(err.message)
    }
  }

  async function rejectRequest(item) {
    try {
      await jsonPost(`/requests/${item.id}/reject/`, { note: 'Rejected by lead.' })
      setDecidedRequests((prev) => [{ ...item, decidedStatus: 'rejected' }, ...prev.filter((r) => r.id !== item.id)])
      await refreshAll()
    } catch (err) {
      setError(err.message)
    }
  }

  const unreadNotifications = notifications.filter((item) => !item.is_read).length

  if (!user) {
    return (
      <div className="auth-shell">
        <GradientDefs />
        <div className="aurora" aria-hidden="true" />
        <div className="mesh" aria-hidden="true" />
        <div className="auth-card">
          <div className="auth-brand">
            <BrandMark size={46} />
            <div>
              <strong>AKA</strong>
              <span>Antier Knowledge Assistant</span>
            </div>
          </div>
          <h1>Governed knowledge,<br />beautifully delivered.</h1>

          <div className="hint-users" style={{ marginBottom: 16 }}>
            <button
              type="button"
              className={authScreen === 'login' ? 'dept-pill' : 'ghost'}
              onClick={() => { setAuthScreen('login'); setError(''); setRegError(''); setRegMessage('') }}
            >
              Sign In
            </button>
            <button
              type="button"
              className={authScreen === 'register' ? 'dept-pill' : 'ghost'}
              onClick={() => { setAuthScreen('register'); setError(''); setRegError('') }}
            >
              Register
            </button>
          </div>

          {authScreen === 'login' ? (
            <>
              <form className="form" onSubmit={handleLogin}>
                <label className="field">
                  <span>Email</span>
                  <input
                    value={loginUsername}
                    autoFocus
                    autoComplete="username"
                    placeholder="you@example.com"
                    onChange={(e) => setLoginUsername(e.target.value)}
                  />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={loginPassword}
                    autoComplete="current-password"
                    placeholder="Password"
                    onChange={(e) => setLoginPassword(e.target.value)}
                  />
                </label>
                <button className="primary" type="submit" disabled={busy || !loginUsername.trim() || !loginPassword}>
                  {busy ? 'Signing in…' : <>{G.spark}<span>Sign In</span></>}
                </button>
              </form>
              {error ? <p className="error">{error}</p> : null}
            </>
          ) : (
            <>
              <p className="muted">Create an account. Viewers are active immediately; contributors require Lead approval.</p>
              <form className="form" onSubmit={handleRegister}>
                <label className="field">
                  <span>Role</span>
                  <select value={regRole} onChange={(e) => setRegRole(e.target.value)}>
                    <option value="viewer">Viewer</option>
                    <option value="contributor">Contributor</option>
                  </select>
                </label>
                <label className="field">
                  <span>Name</span>
                  <input value={regName} placeholder="Full name" onChange={(e) => setRegName(e.target.value)} />
                </label>
                <label className="field">
                  <span>Email</span>
                  <input value={regEmail} placeholder="you@example.com" onChange={(e) => setRegEmail(e.target.value)} />
                </label>
                <label className="field">
                  <span>Password</span>
                  <input
                    type="password"
                    value={regPassword}
                    placeholder="At least 6 characters"
                    onChange={(e) => setRegPassword(e.target.value)}
                  />
                </label>
                <button
                  className="primary"
                  type="submit"
                  disabled={busy || !regName.trim() || !regEmail.trim() || regPassword.length < 6}
                >
                  {busy ? 'Submitting…' : 'Register'}
                </button>
              </form>
              {regMessage ? <p className="muted">{regMessage}</p> : null}
              {regError ? <p className="error">{regError}</p> : null}
            </>
          )}
        </div>
      </div>
    )
  }

  return (
    <div className="app-shell">
      <GradientDefs />
      <div className="app-glow" aria-hidden="true" />
      <aside className="sidebar">
        <div className="brand">
          <BrandMark size={40} />
          <div>
            <h1>AKA Portal</h1>
            <p className="muted">Antier Knowledge Assistant</p>
          </div>
        </div>

        <div className="session-card">
          <div className="avatar">{user.username?.[0]?.toUpperCase()}</div>
          <div>
            <strong>{user.username}</strong>
            <p className="muted">{user.org_role}</p>
          </div>
          <button className="link" onClick={logout} aria-label="Sign out">{G.signout}</button>
        </div>

        <div className="nav">
          {NAV_ITEMS.map((item) => (
            <button
              key={item.key}
              className={activeTab === item.key ? 'nav-item active' : 'nav-item'}
              onClick={() => setActiveTab(item.key)}
            >
              <span className="nav-ico" aria-hidden="true">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
              {item.key === 'requests' && unreadNotifications ? (
                <span className="badge">{unreadNotifications}</span>
              ) : null}
            </button>
          ))}
        </div>

        <div className="panel">
          <div className="panel-head">
            <h2>Departments</h2>
            <span className="muted">Visible only to you</span>
          </div>
          <div className="dept-list">
            {visibleDepartments.map((dept, i) => (
              <button
                key={dept.dept_slug}
                className={department === dept.dept_slug ? 'dept active' : 'dept'}
                onClick={() => setDepartment(dept.dept_slug)}
              >
                <span className={`mono mono-${DEPT_ACCENTS[i % DEPT_ACCENTS.length]}`} aria-hidden="true">
                  {deptGlyph(dept.dept_slug)}
                </span>
                <span className="dept-text">
                  <strong>{dept.dept_name}</strong>
                  <span>{dept.role} · {dept.sensitivity_ceiling}</span>
                </span>
              </button>
            ))}
          </div>
        </div>
      </aside>

      <main className="main">
        <header className="topbar">
          <div>
            <h2>{NAV_ITEMS.find((item) => item.key === activeTab)?.label}</h2>
            <p className="muted">{currentDepartment?.dept_name || 'Choose a department to continue'}</p>
          </div>
          <div className="topbar-actions">
            <button className="ghost" onClick={refreshAll}>{G.refresh}<span>Refresh</span></button>
          </div>
        </header>

        {notice ? <div className="toast">{notice}</div> : null}
        {error ? <div className="toast toast-error">{error}</div> : null}

        {activeTab === 'dashboard' ? (
          <div className="grid">
            <Card title="Session" subtitle="Identity and department context">
              <div className="stat-grid">
                <div><span>User</span><strong>{user.username}</strong></div>
                <div><span>Role</span><strong>{role}</strong></div>
                <div><span>Department</span><strong>{currentDepartment?.dept_name || 'None'}</strong></div>
                <div><span>Unread</span><strong>{unreadNotifications}</strong></div>
              </div>
            </Card>

            <Card title="Knowledge spaces" subtitle="Only permitted departments are rendered">
              <div className="dept-cloud">
                {visibleDepartments.map((dept) => (
                  <button key={dept.dept_slug} className="dept-pill" onClick={() => setDepartment(dept.dept_slug)}>
                    {dept.dept_name}
                  </button>
                ))}
              </div>
            </Card>

            {isAccountLead ? (
              <Card
                title="Pending Contributor Requests"
                subtitle="Approve or reject new contributor sign-ups"
                className="full-width"
                actions={pendingContributors.length ? <Chip tone="warning">{pendingContributors.length}</Chip> : null}
              >
                <div className="request-list">
                  {pendingContributors.map((c) => (
                    <article key={c.id} className="request-row">
                      <div>
                        <strong>{c.name}</strong>
                        <p className="muted">{c.email}</p>
                        <div className="row-meta">
                          <span>Requested {new Date(c.requested_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="row-actions">
                        <button className="primary" onClick={() => decideContributor(c, 'approve')}>{G.check}<span>Approve</span></button>
                        <button className="danger" onClick={() => decideContributor(c, 'reject')}>{G.close}<span>Reject</span></button>
                      </div>
                    </article>
                  ))}
                  {decidedContributors.map((c) => (
                    <article key={c.id} className="request-row">
                      <div>
                        <strong>{c.name}</strong>
                        <p className="muted">{c.email}</p>
                        <div className="row-meta">
                          <span>Requested {new Date(c.requested_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="row-actions">
                        <Chip tone={c.decidedStatus === 'approved' ? 'success' : 'danger'}>
                          {c.decidedStatus === 'approved' ? 'Approved' : 'Rejected'}
                        </Chip>
                      </div>
                    </article>
                  ))}
                  {!pendingContributors.length && !decidedContributors.length ? (
                    <p className="muted">No pending contributor requests.</p>
                  ) : null}
                </div>
              </Card>
            ) : null}
          </div>
        ) : null}

        {activeTab === 'documents' ? (
          <div className="grid two-up">
            <Card
              title="Upload"
              subtitle="Lead and Contributor only"
              actions={role === 'viewer' ? <Chip tone="neutral">Upload hidden</Chip> : null}
            >
              {role !== 'viewer' ? (
                <form className="form" onSubmit={handleUpload}>
                  <label className="field">
                    <span>File</span>
                    <input type="file" onChange={(e) => setUploadFile(e.target.files?.[0] || null)} />
                  </label>
                  <label className="field">
                    <span>Sensitivity</span>
                    <select value={uploadSensitivity} onChange={(e) => setUploadSensitivity(e.target.value)}>
                      <option value="open">Open</option>
                      <option value="internal">Internal</option>
                      <option value="restricted">Restricted</option>
                      <option value="confidential">Confidential</option>
                    </select>
                  </label>
                  <button className="primary" type="submit" disabled={busy || !uploadFile}>
                    {busy ? 'Uploading…' : <>{G.upload}<span>Upload Document</span></>}
                  </button>
                </form>
              ) : (
                <p className="muted">Viewers cannot upload documents.</p>
              )}
            </Card>

            <Card title="Document Library" subtitle="Every document is listed; gated ones are greyed">
              <div className="doc-list">
                {documents.map((doc) => (
                  <article key={doc.id} className={doc.accessible ? 'doc-row' : 'doc-row locked'}>
                    <div className="doc-main">
                      <strong>{doc.name}</strong>
                      <div className="row-meta">
                        <Chip tone={doc.sensitivity === 'confidential' ? 'danger' : doc.sensitivity === 'restricted' ? 'warning' : 'neutral'}>
                          {doc.sensitivity}
                        </Chip>
                        <span>{doc.department}</span>
                        <span>v{doc.version}</span>
                        <span>{doc.uploader}</span>
                        <span>{new Date(doc.uploaded_at).toLocaleDateString()}</span>
                        <span>{formatBytes(doc.file_size)}</span>
                      </div>
                    </div>
                    <div className="row-actions">
                      {!doc.accessible ? (
                        <button
                          className="ghost"
                          onClick={() => startRequest({ documentId: doc.id, text: `Access to ${doc.name}` })}
                        >
                          {G.key}<span>Request Access</span>
                        </button>
                      ) : null}
                      {role === 'lead' ? <button className="danger" onClick={() => handleDelete(doc.id)}>{G.trash}<span>Delete</span></button> : null}
                    </div>
                  </article>
                ))}
                {!documents.length ? <p className="muted">No documents in this space yet.</p> : null}
              </div>
            </Card>
          </div>
        ) : null}

        {activeTab === 'chat' ? (
          <div className="chat-window">
            <div className="chat-thread">
              {!messages.length && !chatLoading ? (
                <div className="chat-empty">
                  <h2>Ask anything about {currentDepartment?.dept_name || 'your knowledge base'}</h2>
                  <p className="muted">Answers are grounded in the documents you’re permitted to see, with sources cited.</p>
                </div>
              ) : null}

              {messages.map((msg, index) => (
                <div key={index} className={`chat-msg chat-msg-${msg.role}`}>
                  <div className="chat-avatar">{msg.role === 'user' ? (user.username?.[0]?.toUpperCase() || 'U') : <AssistantMark />}</div>
                  <div className="chat-bubble">
                    <p className={msg.error ? 'error' : undefined}>{msg.text}</p>
                    {msg.sources && msg.sources.length ? (
                      <div className="source-list">
                        {msg.sources.map((source, i) => (
                          <div key={`${source.doc_name}-${i}`} className="source-chip">
                            <strong>{source.doc_name}</strong>
                            <span>{source.department}</span>
                            <Chip>{source.sensitivity}</Chip>
                          </div>
                        ))}
                      </div>
                    ) : null}
                  </div>
                </div>
              ))}

              {chatLoading ? (
                <div className="chat-msg chat-msg-assistant">
                  <div className="chat-avatar"><AssistantMark /></div>
                  <div className="chat-bubble">
                    <span className="chat-typing"><i /><i /><i /></span>
                  </div>
                </div>
              ) : null}
            </div>

            <form className="chat-composer" onSubmit={handleChat}>
              <textarea
                rows="1"
                value={chatQuestion}
                onChange={(e) => setChatQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    handleChat(e)
                  }
                }}
                placeholder={`Ask a question about ${currentDepartment?.dept_name || 'this department'}…`}
              />
              <button className="primary" type="submit" disabled={chatLoading || !chatQuestion.trim()}>
                {chatLoading ? 'Thinking…' : <>{G.send}<span>Send</span></>}
              </button>
            </form>
            {chatError ? <p className="error chat-error">{chatError}</p> : null}
          </div>
        ) : null}

        {activeTab === 'requests' ? (
          <div className={role === 'lead' ? 'grid' : 'grid two-up'}>
            {role !== 'lead' ? (
            <Card title="New Request" subtitle="Create a governed access request">
              <form className="form" onSubmit={createRequest}>
                <label className="field">
                  <span>What do you need?</span>
                  <input value={requestText} onChange={(e) => setRequestText(e.target.value)} />
                </label>
                <label className="field">
                  <span>Why do you need it?</span>
                  <textarea rows="3" value={requestReason} onChange={(e) => setRequestReason(e.target.value)} />
                </label>
                <label className="field">
                  <span>Document (optional)</span>
                  <select value={requestDocumentId} onChange={(e) => setRequestDocumentId(e.target.value)}>
                    <option value="">General department request</option>
                    {documents.map((doc) => (
                      <option key={doc.id} value={doc.id}>{doc.name}</option>
                    ))}
                  </select>
                </label>
                <button className="primary" type="submit" disabled={!requestText.trim() || !requestReason.trim()}>
                  {G.key}<span>Submit Request</span>
                </button>
              </form>
              {requestStatus ? <p className="muted">{requestStatus}</p> : null}
            </Card>
            ) : null}

            <Card title="Inbox" subtitle={role === 'lead' ? 'Pending approvals + your notifications' : 'Your notifications'}>
              {role === 'lead' ? (
                <div className="request-list">
                  {pendingRequests.map((item) => (
                    <article key={item.id} className="request-row">
                      <div>
                        <strong>{item.requester}</strong>
                        <p className="muted">{item.request_text}</p>
                        <div className="row-meta">
                          <span>{item.department}</span>
                          <span>{item.document || 'No document yet'}</span>
                          <span>{new Date(item.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="row-actions">
                        <button className="primary" onClick={() => approveRequest(item)}>{G.check}<span>Approve</span></button>
                        <button className="danger" onClick={() => rejectRequest(item)}>{G.close}<span>Reject</span></button>
                      </div>
                    </article>
                  ))}
                  {decidedRequests.map((item) => (
                    <article key={item.id} className="request-row">
                      <div>
                        <strong>{item.requester}</strong>
                        <p className="muted">{item.request_text}</p>
                        <div className="row-meta">
                          <span>{item.department}</span>
                          <span>{item.document || 'No document yet'}</span>
                          <span>{new Date(item.created_at).toLocaleString()}</span>
                        </div>
                      </div>
                      <div className="row-actions">
                        <Chip tone={item.decidedStatus === 'approved' ? 'success' : 'danger'}>
                          {item.decidedStatus === 'approved' ? 'Approved' : 'Rejected'}
                        </Chip>
                      </div>
                    </article>
                  ))}
                  {!pendingRequests.length && !decidedRequests.length ? (
                    <p className="muted">No access requests.</p>
                  ) : null}
                </div>
              ) : null}
              <div className="request-list">
                {notifications.map((item) => (
                  <article key={item.id} className={item.is_read ? 'request-row' : 'request-row unread'}>
                    <div>
                      <strong>{item.title}</strong>
                      <p className="muted">{item.message}</p>
                      <div className="row-meta">
                        <span>{item.notification_type}</span>
                        <span>{new Date(item.created_at).toLocaleString()}</span>
                      </div>
                    </div>
                  </article>
                ))}
                {!notifications.length ? <p className="muted">No notifications yet.</p> : null}
              </div>
            </Card>
          </div>
        ) : null}
      </main>
    </div>
  )
}

export default App
