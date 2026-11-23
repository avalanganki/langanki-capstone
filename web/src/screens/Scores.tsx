import { formatShortDate } from '../dates'
import { FROM_OURA, SAMPLE, showValue, type NightsResponse } from '../nights'

const R = 28
const CIRCUMFERENCE = 2 * Math.PI * R

function Ring({ label, value }: { label: string; value: number | null }) {
  const missing = value === null || value === undefined
  const fraction = missing ? 0 : Math.min(Math.max(value / 100, 0), 1)
  return (
    <div className="ring" role="group" aria-label={`${label}: ${showValue(value)}`}>
      <div className="ring-number-wrap">
        <svg viewBox="0 0 64 64" aria-hidden="true">
          <circle className="track" cx="32" cy="32" r={R} />
          {!missing && (
            <circle
              className="fill"
              cx="32"
              cy="32"
              r={R}
              strokeDasharray={CIRCUMFERENCE}
              strokeDashoffset={CIRCUMFERENCE * (1 - fraction)}
              transform="rotate(-90 32 32)"
              style={{ ['--ring-c' as string]: String(CIRCUMFERENCE) }}
            />
          )}
        </svg>
        <span className={missing ? 'ring-number missing' : 'ring-number'}>{showValue(value)}</span>
      </div>
      <span className="ring-label">{label}</span>
    </div>
  )
}

function Plain({ label, value }: { label: string; value: number | null }) {
  const missing = value === null || value === undefined
  return (
    <div className="ring" role="group" aria-label={`${label}: ${showValue(value)}`}>
      <div className="ring-number-wrap">
        <span className={missing ? 'ring-number missing' : 'ring-number plain'}>{showValue(value)}</span>
      </div>
      <span className="ring-label">{label}</span>
    </div>
  )
}

/** Last night's scores. Shown to Ava only; never sent to Claude. */
export function Scores({ data }: { data: NightsResponse }) {
  const last = data.nights[data.nights.length - 1]
  if (!last) return null
  return (
    <section aria-label="Last night's scores">
      <div className="rings-card">
        <Ring label="Readiness" value={last.readiness} />
        <Ring label="Sleep" value={last.sleep_score} />
        <Plain label="HRV (ms)" value={last.avg_hrv} />
      </div>
      <p className="rings-note">
        Last night, {formatShortDate(last.date)}. {data.source === 'oura' ? FROM_OURA : SAMPLE}
      </p>
    </section>
  )
}
