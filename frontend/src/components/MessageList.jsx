import { Fragment, useEffect, useRef } from 'react'
import { Avatar } from './Avatar.jsx'
import { colorFor, formatDay, formatTime } from '../utils.js'

const GROUP_WINDOW_S = 5 * 60

export function MessageList({ messages, me, room }) {
  const endRef = useRef(null)
  const boxRef = useRef(null)

  useEffect(() => {
    const box = boxRef.current
    if (!box) return
    // Only auto-scroll if the reader is already near the bottom.
    const nearBottom = box.scrollHeight - box.scrollTop - box.clientHeight < 160
    if (nearBottom || messages.length < 60) endRef.current?.scrollIntoView({ block: 'end' })
  }, [messages])

  if (!messages.length) {
    return (
      <div className="messages empty" ref={boxRef}>
        <div className="empty-state">
          <div className="empty-hash">#</div>
          <h2>Welcome to #{room}</h2>
          <p className="muted">This is the start of the room. Say hi 👋</p>
        </div>
      </div>
    )
  }

  let prev = null
  let prevDay = null

  return (
    <div className="messages" ref={boxRef}>
      {messages.map((m) => {
        const day = formatDay(m.ts)
        const dayDivider = day !== prevDay
        prevDay = day

        if (m.type === 'system') {
          prev = null
          return (
            <Fragment key={m.id}>
              {dayDivider && <div className="day"><span>{day}</span></div>}
              <div className="system">{m.text}</div>
            </Fragment>
          )
        }

        const grouped =
          !dayDivider && prev && prev.username === m.username && m.ts - prev.ts < GROUP_WINDOW_S
        prev = m
        const mine = m.username === me

        return (
          <Fragment key={m.id}>
            {dayDivider && <div className="day"><span>{day}</span></div>}
            <div className={`msg ${grouped ? 'grouped' : ''} ${mine ? 'mine' : ''}`}>
              <div className="msg-gutter">
                {grouped ? (
                  <span className="msg-time-hover">{formatTime(m.ts)}</span>
                ) : (
                  <Avatar name={m.username} size={36} />
                )}
              </div>
              <div className="msg-body">
                {!grouped && (
                  <div className="msg-meta">
                    <span className="msg-author" style={{ color: colorFor(m.username) }}>
                      {m.username}
                    </span>
                    {mine && <span className="you">you</span>}
                    <span className="msg-time">{formatTime(m.ts)}</span>
                  </div>
                )}
                <div className="msg-text">{m.text}</div>
              </div>
            </div>
          </Fragment>
        )
      })}
      <div ref={endRef} />
    </div>
  )
}
