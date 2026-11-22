import { useEffect, useState } from 'react'
import { Avatar } from './Avatar.jsx'

const ROOM_RE = /^[a-z0-9][a-z0-9-]{0,23}$/

export function Sidebar({ room, onSelect, username, onLeave, open, onClose }) {
  const [rooms, setRooms] = useState([])
  const [draft, setDraft] = useState('')

  useEffect(() => {
    let alive = true
    const load = () =>
      fetch('/api/rooms')
        .then((r) => r.json())
        .then((data) => alive && setRooms(data))
        .catch(() => {})
    load()
    const id = setInterval(load, 4000)
    return () => {
      alive = false
      clearInterval(id)
    }
  }, [room])

  const list = rooms.some((r) => r.name === room) ? rooms : [...rooms, { name: room, online: 1 }]
  const slug = draft.trim().toLowerCase().replace(/\s+/g, '-')

  const create = (e) => {
    e.preventDefault()
    if (ROOM_RE.test(slug)) {
      onSelect(slug)
      setDraft('')
    }
  }

  return (
    <aside className={`sidebar ${open ? 'open' : ''}`}>
      <div className="sidebar-head">
        <span className="brand-mark small" aria-hidden>
          <svg viewBox="0 0 32 32"><path d="M7 17h4l2-5 4 10 2-5h6" /></svg>
        </span>
        <span className="brand-name">Pulse</span>
        <button className="icon-btn only-mobile" onClick={onClose} aria-label="Close menu">✕</button>
      </div>

      <div className="section-label">Rooms</div>
      <nav className="rooms">
        {list.map((r) => (
          <button
            key={r.name}
            className={`room ${r.name === room ? 'active' : ''}`}
            onClick={() => onSelect(r.name)}
          >
            <span className="hash">#</span>
            <span className="room-name">{r.name}</span>
            {r.online > 0 && <span className="badge">{r.online}</span>}
          </button>
        ))}
      </nav>

      <form className="new-room" onSubmit={create}>
        <input
          placeholder="+ new room"
          value={draft}
          maxLength={24}
          onChange={(e) => setDraft(e.target.value)}
          aria-label="Create or join a room"
        />
      </form>

      <div className="me">
        <Avatar name={username} size={30} online />
        <span className="me-name">{username}</span>
        <button className="link-btn" onClick={onLeave}>Sign out</button>
      </div>
    </aside>
  )
}
