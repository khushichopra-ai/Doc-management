import { useEffect, useMemo, useState } from 'react'
import './App.css'

// Decorative inline icons (visual only). Lucide-style, inherit currentColor.
const svg = (paths) => (
  <svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor"
    strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
    {paths}
  </svg>
)
const ICONS = {
  dashboard: svg(<><rect x="3" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="3" width="7" height="7" rx="1.5" /><rect x="14" y="14" width="7" height="7" rx="1.5" /><rect x="3" y="14" width="7" height="7" rx="1.5" /></>),
  documents: svg(<><path d="M14 3v4a1 1 0 0 0 1 1h4" /><path d="M17 21H7a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h7l5 5v11a2 2 0 0 1-2 2z" /><path d="M9 13h6M9 17h4" /></>),
  chat: svg(<path d="M21 15a2 2 0 0 1-2 2H8l-4 4V5a2 2 0 0 1 2-2h13a2 2 0 0 1 2 2z" />),
  requests: svg(<><path d="M22 12h-6l-2 3h-4l-2-3H2" /><path d="M5.45 5.11 2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z" /></>),
}

const NAV_ITEMS = [
  { key: 'dashboard', label: 'Dashboard', icon: ICONS.dashboard },
  { key: 'documents', label: 'Documents', icon: ICONS.documents },
  { key: 'chat', label: 'Chat', icon: ICONS.chat },
  { key: 'requests', label: 'Requests', icon: ICONS.requests },
]

// Soft accent rotation for department monograms (visual only).
const DEPT_ACCENTS = ['violet', 'blue', 'emerald', 'amber', 'rose']

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

  // Account registration + Lead contributor-approval workflow.
  const [authScreen, setAuthScreen] = useState('login') // 'login' | 'register'
  const [regName, setRegName] = useState('')
  const [regEmail, setRegEmail] = useState('')
  const [regPassword, setRegPassword] = useState('')
  const [regRole, setRegRole] = useState('viewer')
  const [regMessage, setRegMessage] = useState('')
  const [regError, setRegError] = useState('')
  const [pendingContributors, setPendingContributors] = useState([])

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

  async function decideContributor(id, action) {
    try {
      await jsonPost(`/contributors/${id}/${action}/`, {})
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
  }

  async function handleUpload(event) {
    event.preventDefault()
    if (!uploadFile) return
    setError('')
    setNotice('')
    const fileName = uploadFile.name
    setBusy(true)
    try {
      const formData = new FormData()
      formData.append('file', uploadFile)
      formData.append('department', department)
      formData.append('sensitivity', uploadSensitivity)
      const result = await api('/documents/upload/', { method: 'POST', body: formData })
      setUploadFile(null)
      event.target.reset()
      setNotice(`✓ "${fileName}" uploaded successfully — ${result.chunk_count} chunk(s) indexed and now searchable.`)
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

  async function approveRequest(requestId) {
    try {
      await jsonPost(`/requests/${requestId}/approve/`, { note: 'Approved by lead.' })
      await refreshAll()
    } catch (err) {
      setError(err.message)
    }
  }

  async function rejectRequest(requestId) {
    try {
      await jsonPost(`/requests/${requestId}/reject/`, { note: 'Rejected by lead.' })
      await refreshAll()
    } catch (err) {
      setError(err.message)
    }
  }

  const unreadNotifications = notifications.filter((item) => !item.is_read).length

  if (!user) {
    return (
      <div className="auth-shell">
        <div className="auth-card">
          <Chip tone="accent">AKA Portal</Chip>
          <h1>Governed knowledge, one portal.</h1>

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
                  {busy ? 'Signing in…' : 'Sign In'}
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
      <aside className="sidebar">
        <div className="brand">
          <Chip tone="accent">AKA</Chip>
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
          <button className="link" onClick={logout}>Sign out</button>
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
                  {dept.dept_name?.[0]?.toUpperCase()}
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
            <button className="ghost" onClick={refreshAll}>Refresh</button>
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
                        <button className="primary" onClick={() => decideContributor(c.id, 'approve')}>Approve</button>
                        <button className="danger" onClick={() => decideContributor(c.id, 'reject')}>Reject</button>
                      </div>
                    </article>
                  ))}
                  {!pendingContributors.length ? <p className="muted">No pending contributor requests.</p> : null}
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
                    {busy ? 'Uploading…' : 'Upload Document'}
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
                          Request Access
                        </button>
                      ) : null}
                      {role === 'lead' ? <button className="danger" onClick={() => handleDelete(doc.id)}>Delete</button> : null}
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
                  <div className="chat-avatar">{msg.role === 'user' ? (user.username?.[0]?.toUpperCase() || 'U') : 'AKA'}</div>
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
                    {msg.insufficient ? (
                      <button className="ghost" onClick={() => startRequest({ text: msg.question })}>
                        Request this information
                      </button>
                    ) : null}
                  </div>
                </div>
              ))}

              {chatLoading ? (
                <div className="chat-msg chat-msg-assistant">
                  <div className="chat-avatar">AKA</div>
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
                {chatLoading ? 'Thinking…' : 'Send'}
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
                  Submit Request
                </button>
              </form>
              {requestStatus ? <p className="muted">{requestStatus}</p> : null}
            </Card>
            ) : null}

            <Card title="Inbox" subtitle={role === 'lead' ? 'Pending approvals + your notifications' : 'Your notifications'}>
              {role === 'lead' && pendingRequests.length ? (
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
                        <button className="primary" onClick={() => approveRequest(item.id)}>Approve</button>
                        <button className="danger" onClick={() => rejectRequest(item.id)}>Reject</button>
                      </div>
                    </article>
                  ))}
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
