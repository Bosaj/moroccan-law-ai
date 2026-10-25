import type { ReactNode } from 'react'
import { motion, useReducedMotion } from 'motion/react'

interface Props {
  children: ReactNode
  delay?: number
  className?: string
}

/**
 * Staggered reveal in the style of Magic UI's "Blur Fade": opacity, a small rise and a light blur.
 * Falls back to a static block when the user asks for reduced motion.
 */
export function BlurFade({ children, delay = 0, className }: Props) {
  const reduce = useReducedMotion()
  if (reduce) return <div className={className}>{children}</div>
  return (
    <motion.div
      className={className}
      initial={{ opacity: 0, y: 8, filter: 'blur(6px)' }}
      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
      transition={{ duration: 0.45, delay, ease: [0.16, 1, 0.3, 1] }}
    >
      {children}
    </motion.div>
  )
}
