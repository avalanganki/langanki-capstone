/** Today's date as shown in the night-sky header, e.g. "Thursday, Oct 1". */
export function formatToday(now: Date = new Date()): string {
  return now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
}

/** Today in the browser's own time zone as YYYY-MM-DD (not UTC, so late-night entries keep tonight's date). */
export function todayIso(now: Date = new Date()): string {
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}`
}

/** "2026-11-06" as "Nov 6". Read as a calendar date, so no time-zone shift. */
export function formatShortDate(iso: string): string {
  const [y, m, d] = iso.split('-').map(Number)
  return new Date(y, m - 1, d).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })
}
