interface Props {
  className?: string
  /** Size of the square mark in px. */
  size?: number
}

/**
 * Mizan mark: a balance beam with two pans, set inside a rotated square (the eight-point star of
 * Moroccan zellige is built from two such squares; one is enough for a mark at small sizes).
 */
export function LogoMark({ className, size = 36 }: Props) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 64 64"
      role="img"
      aria-label="Mizan"
      className={className}
      fill="none"
      stroke="currentColor"
      strokeWidth={2.6}
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <rect x="26.5" y="6.5" width="11" height="11" rx="1" transform="rotate(45 32 12)" strokeWidth={2} />
      <path d="M32 18v28M20 46h24" />
      <path d="M14 24h36" />
      <path d="M14 24 8 38h12zM50 24l-6 14h12z" />
    </svg>
  )
}
