import { colorFor, initials } from '../utils.js'

export function Avatar({ name, size = 32, online = false }) {
  return (
    <span
      className="avatar"
      style={{ width: size, height: size, fontSize: size * 0.4, background: colorFor(name) }}
      title={name}
    >
      {initials(name)}
      {online && <span className="avatar-dot" />}
    </span>
  )
}
