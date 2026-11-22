import { useState } from 'react'
import { JoinScreen } from './components/JoinScreen.jsx'
import { Sidebar } from './components/Sidebar.jsx'
import { MessageList } from './components/MessageList.jsx'
import { Composer } from './components/Composer.jsx'
import { Avatar } from './components/Avatar.jsx'
import { useChat } from './useChat.js'
import { storage } from './utils.js'

const STATUS_TEXT = {
  connecting: 'Connecting…',
  online: 'Live',
  reconnecting: 'Reconnecting…',
  error: 'Disconnected',
}

function ChatRoom({ username, onLeave }) {
  const [room, setRoom] = useState(() => {
    const fromHash = window.location.hash.replace('#', '')
    return /^[a-z0-9][a-z0-9-]{0,23}$/.test(fromHash) ? fromHash : 'general'
  })
  const [menuOpen, setMenuOpen] = useState(false)
  const { messages, users, typing, status, error, sendMessage, setIsTyping } = useChat(room, username)

  const selectRoom = (name) => {
    setRoom(name)
    window.location.hash = name
    setMenuOpen(false)
  }

  return (
    <div className="app">
      <Sidebar
        room={room}
        onSelect={selectRoom}
        username={username}
        onLeave={onLeave}
        open={menuOpen}
        onClose={() => setMenuOpen(false)}
      />
      {menuOpen && <div className="scrim" onClick={() => setMenuOpen(false)} />}

      <main className="chat">
        <header className="chat-head">
          <button className="icon-btn only-mobile" onClick={() => setMenuOpen(true)} aria-label="Open menu">☰</button>
          <h2><span className="hash">#</span>{room}</h2>
          <span className={`status status-${status}`}>
            <span className="status-dot" />
            {STATUS_TEXT[status]}
          </span>
          <span className="head-count">{users.length} online</span>
        </header>

        {error && <div className="toast">{error}</div>}

        <MessageList messages={messages} me={username} room={room} />
        <Composer
          room={room}
          disabled={status !== 'online'}
          onSend={sendMessage}
          onTyping={setIsTyping}
          typing={typing}
        />
      </main>

      <aside className="people">
        <div className="section-label">Online — {users.length}</div>
        {users.map((u) => (
          <div className="person" key={u}>
            <Avatar name={u} size={28} online />
            <span>{u}</span>
            {u === username && <span className="you">you</span>}
            {typing.includes(u) && <span className="person-typing">typing…</span>}
          </div>
        ))}
      </aside>
    </div>
  )
}

export default function App() {
  const [username, setUsername] = useState(() => storage.get('pulse:name'))

  if (!username) {
    return (
      <JoinScreen
        initialName=""
        onJoin={(name) => {
          storage.set('pulse:name', name)
          setUsername(name)
        }}
      />
    )
  }

  return (
    <ChatRoom
      username={username}
      onLeave={() => {
        storage.remove('pulse:name')
        setUsername(null)
      }}
    />
  )
}
