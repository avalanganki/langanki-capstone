/** The night-sky band from docs/design/wireframes/prototype.html: dusk bands, stars, moon, hills. */
export function NightSky({ date, title }: { date: string; title: string }) {
  return (
    <header className="sky">
      <svg viewBox="0 0 360 120" preserveAspectRatio="none" aria-hidden="true">
        <rect x="0" y="0" width="360" height="24" fill="#1A1618" />
        <rect x="0" y="24" width="360" height="24" fill="#211c1f" />
        <rect x="0" y="48" width="360" height="24" fill="#2A2326" />
        <rect x="0" y="72" width="360" height="24" fill="#4a2f3b" />
        <rect x="0" y="96" width="360" height="24" fill="#7A4A5A" />
        <circle cx="60" cy="16" r="1.3" fill="#F3ECEE" opacity="0.8" />
        <circle cx="110" cy="30" r="1" fill="#F3ECEE" opacity="0.6" />
        <circle cx="200" cy="12" r="1.2" fill="#F3ECEE" opacity="0.7" />
        <circle cx="255" cy="36" r="1" fill="#F3ECEE" opacity="0.5" />
        <circle cx="330" cy="20" r="1.3" fill="#F3ECEE" opacity="0.8" />
        <circle cx="300" cy="24" r="10" fill="#E6B8C4" />
        <circle cx="304.5" cy="20.5" r="9" fill="#1A1618" />
        <polygon points="0,120 0,95 60,80 140,100 220,78 300,96 360,85 360,120" fill="#140F12" />
        <polygon points="0,120 0,108 90,92 180,112 270,90 360,104 360,120" fill="#0F0B0D" />
      </svg>
      <div className="sky-text">
        {date && <span className="date">{date}</span>}
        <h1>{title}</h1>
      </div>
    </header>
  )
}
