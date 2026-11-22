import { useState } from 'react'
import { Avatar } from './Avatar.jsx'

const NAME_RE = /^[\w .-]{1,24}$/

export function JoinScreen({ initialName, onJoin }) {
  const [name, setName] = useState(initialName || '')
  const trimmed = name.trim()
  const valid = NAME_RE.test(trimmed)

  const submit = (e) => {
    e.preventDefault()
    if (valid) onJoin(trimmed)
  }

  return (
    <div className="join">
      <form className="join-card" onSubmit={submit}>
        <div className="brand">
          <span className="brand-mark" aria-hidden>
            <svg viewBox="0 0 32 32"><path d="M7 17h4l2-5 4 10 2-5h6" /></svg>
          </span>
          <span className="brand-name">Pulse</span>
        </div>
        <h1>Real-time chat rooms</h1>
        <p className="muted">Pick a display name and jump in. No sign-up needed.</p>

        <label htmlFor="name">Display name</label>
        <div className="join-input">
          <Avatar name={trimmed || '?'} size={36} />
          <input
            id="name"
            autoFocus
            maxLength={24}
            placeholder="e.g. Ada Lovelace"
            value={name}
            onChange={(e) => setName(e.target.value)}
          />
        </div>
        {trimmed && !valid && (
          <p className="field-error">Letters, numbers, spaces, dots, dashes and underscores only.</p>
        )}
        <button className="btn-primary" disabled={!valid}>Join chat →</button>

        <ul className="features">
          <li>⚡ Instant delivery over WebSockets</li>
          <li>🟢 See who's online and who's typing</li>
          <li>💾 Message history saved per room</li>
        </ul>
      </form>
    </div>
  )
}
