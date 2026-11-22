import { useEffect, useRef, useState } from 'react'

const MAX = 1000
const TYPING_IDLE_MS = 1500

function typingLabel(names) {
  if (names.length === 0) return ''
  if (names.length === 1) return `${names[0]} is typing`
  if (names.length === 2) return `${names[0]} and ${names[1]} are typing`
  return 'Several people are typing'
}

export function Composer({ room, disabled, onSend, onTyping, typing }) {
  const [text, setText] = useState('')
  const typingRef = useRef(false)
  const idleTimer = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    setText('')
    inputRef.current?.focus()
  }, [room])

  const stopTyping = () => {
    clearTimeout(idleTimer.current)
    if (typingRef.current) {
      typingRef.current = false
      onTyping(false)
    }
  }

  const handleChange = (e) => {
    setText(e.target.value)
    if (!typingRef.current) {
      typingRef.current = true
      onTyping(true)
    }
    clearTimeout(idleTimer.current)
    idleTimer.current = setTimeout(stopTyping, TYPING_IDLE_MS)
  }

  const submit = (e) => {
    e.preventDefault()
    const value = text.trim()
    if (!value || disabled) return
    if (onSend(value)) {
      setText('')
      stopTyping()
    }
  }

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) submit(e)
  }

  return (
    <div className="composer-wrap">
      <div className="typing" aria-live="polite">
        {typing.length > 0 && (
          <>
            <span className="dots"><i /><i /><i /></span>
            {typingLabel(typing)}…
          </>
        )}
      </div>
      <form className="composer" onSubmit={submit}>
        <textarea
          ref={inputRef}
          rows={1}
          value={text}
          maxLength={MAX}
          placeholder={disabled ? 'Connecting…' : `Message #${room}`}
          onChange={handleChange}
          onKeyDown={onKeyDown}
          onBlur={stopTyping}
          aria-label="Message"
        />
        <button className="send" disabled={disabled || !text.trim()} aria-label="Send">
          <svg viewBox="0 0 24 24"><path d="M3 11.5 21 3l-8.5 18-2-7.5z" /></svg>
        </button>
      </form>
      {text.length > MAX - 100 && <div className="counter">{MAX - text.length} left</div>}
    </div>
  )
}
