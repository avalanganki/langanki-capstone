/** Same cleaning as entries.parse_tags: split on commas, lowercase, trim, drop blanks and repeats. */
export function cleanTags(text: string): string[] {
  const out: string[] = []
  for (const part of text.split(',')) {
    const tag = part.trim().toLowerCase()
    if (tag && !out.includes(tag)) out.push(tag)
  }
  return out
}

/** Streamlit's merge rule: keep what's there, then add suggestions not already present. */
export function mergeTags(current: string[], suggested: string[]): string[] {
  return [...current, ...suggested.filter((t) => !current.includes(t))]
}
