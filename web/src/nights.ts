// Nights as returned by GET /api/nights. Shown to Ava only; never sent to Claude.

export type Night = {
  date: string
  sleep_score: number | null
  readiness: number | null
  avg_hrv: number | null
}

export type NightsResponse = { source: 'oura' | 'sample'; nights: Night[]; counted: number }

export const NO_DATA = 'No data'
export const FROM_OURA = 'From your Oura ring.'
export const SAMPLE = 'Sample data. Not real Oura data.'

/** Like nights.show_value: a missing value reads "No data", never 0; floats keep one decimal. */
export function showValue(value: number | null): string {
  if (value === null || value === undefined) return NO_DATA
  return Number.isInteger(value) ? String(value) : String(Math.round(value * 10) / 10)
}
