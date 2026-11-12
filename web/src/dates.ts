/** Today's date as shown in the night-sky header, e.g. "Thursday, Oct 1". */
export function formatToday(now: Date = new Date()): string {
  return now.toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })
}
