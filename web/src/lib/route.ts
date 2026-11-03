export type ViewId = 'ask' | 'laws' | 'gazette' | 'compare' | 'audit'

export const VIEW_IDS: ViewId[] = ['ask', 'laws', 'gazette', 'compare', 'audit']

export function viewFromHash(hash: string): ViewId {
  const id = hash.replace(/^#\/?/, '').split('?')[0] as ViewId
  return VIEW_IDS.includes(id) ? id : 'ask'
}
