export type ViewId = 'ask' | 'gazette' | 'compare' | 'audit'

export const VIEW_IDS: ViewId[] = ['ask', 'gazette', 'compare', 'audit']

export function viewFromHash(hash: string): ViewId {
  const id = hash.replace(/^#\/?/, '') as ViewId
  return VIEW_IDS.includes(id) ? id : 'ask'
}
