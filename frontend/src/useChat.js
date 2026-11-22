import { useCallback, useEffect, useRef, useState } from 'react'

const CLOSE_BAD_INPUT = 4400
const CLOSE_NAME_TAKEN = 4409
const TYPING_TTL_MS = 3000

function socketUrl(room, username) {
  const proto = window.location.protocol === 'https:' ? 'wss' : 'ws'
  return `${proto}://${window.location.host}/ws/${room}?username=${encodeURIComponent(username)}`
}

/**
 * One WebSocket per room. Reconnects with backoff, tracks presence and who is typing.
 * status: 'connecting' | 'online' | 'reconnecting' | 'error'
 */
export function useChat(room, username) {
  const [messages, setMessages] = useState([])
  const [users, setUsers] = useState([])
  const [typing, setTyping] = useState({})
  const [status, setStatus] = useState('connecting')
  const [error, setError] = useState(null)
  const wsRef = useRef(null)

  useEffect(() => {
    let closedByUs = false
    let retry = 0
    let nameRetries = 0
    let retryTimer
    const typingTimers = {}

    setMessages([])
    setUsers([])
    setTyping({})
    setError(null)
    setStatus('connecting')

    const clearTyping = (name) => {
      clearTimeout(typingTimers[name])
      setTyping((t) => {
        const { [name]: _gone, ...rest } = t
        return rest
      })
    }

    const open = () => {
      const ws = new WebSocket(socketUrl(room, username))
      wsRef.current = ws

      ws.onopen = () => {
        retry = 0
        setStatus('online')
      }

      ws.onmessage = (event) => {
        const msg = JSON.parse(event.data)
        switch (msg.type) {
          case 'history':
            nameRetries = 0 // the server accepted us, so any earlier clash is over
            setMessages(msg.messages)
            break
          case 'message':
            clearTyping(msg.username)
            setMessages((m) => [...m, msg])
            break
          case 'system':
            setMessages((m) => [...m, { ...msg, id: `sys-${msg.ts}-${msg.text}` }])
            break
          case 'presence':
            setUsers(msg.users)
            break
          case 'typing':
            if (msg.is_typing) {
              clearTimeout(typingTimers[msg.username])
              typingTimers[msg.username] = setTimeout(() => clearTyping(msg.username), TYPING_TTL_MS)
              setTyping((t) => ({ ...t, [msg.username]: true }))
            } else {
              clearTyping(msg.username)
            }
            break
          case 'error':
            setError(msg.text)
            setTimeout(() => setError(null), 2500)
            break
          default:
        }
      }

      ws.onclose = (event) => {
        if (closedByUs) return
        // A name clash right after a reconnect is usually our own old socket the server
        // hasn't dropped yet, so give it a few short retries before showing an error.
        if (event.code === CLOSE_NAME_TAKEN && nameRetries < 3) {
          nameRetries += 1
          retryTimer = setTimeout(open, 700)
          return
        }
        if (event.code === CLOSE_NAME_TAKEN || event.code === CLOSE_BAD_INPUT) {
          setStatus('error')
          setError(event.reason || 'Could not join this room.')
          return
        }
        setStatus('reconnecting')
        const delay = Math.min(1000 * 2 ** retry, 10000)
        retry += 1
        retryTimer = setTimeout(open, delay)
      }
    }

    open()
    return () => {
      closedByUs = true
      clearTimeout(retryTimer)
      Object.values(typingTimers).forEach(clearTimeout)
      wsRef.current?.close()
    }
  }, [room, username])

  const send = useCallback((payload) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(payload))
      return true
    }
    return false
  }, [])

  const sendMessage = useCallback((text) => send({ type: 'message', text }), [send])
  const setIsTyping = useCallback((isTyping) => send({ type: 'typing', is_typing: isTyping }), [send])

  return { messages, users, typing: Object.keys(typing), status, error, sendMessage, setIsTyping }
}
