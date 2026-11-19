/** Line-art campus: main building with a clock tower, wings, trees and clouds (decorative). */
const range = (n: number) => Array.from({ length: n }, (_, i) => i)

function ArchWindow({ x, y, w = 9, h = 16 }: { x: number; y: number; w?: number; h?: number }) {
  const r = w / 2
  return <path d={`M${x} ${y + h}V${y + r}a${r} ${r} 0 0 1 ${w} 0V${y + h}z`} />
}

function Tree({ x, y, s = 1 }: { x: number; y: number; s?: number }) {
  return (
    <g transform={`translate(${x} ${y}) scale(${s})`}>
      <path d="M0 0v-26M0-14l-7-7M0-18l6-6" />
      <path d="M-22-30a14 14 0 0 1 8-20 16 16 0 0 1 28-2 13 13 0 0 1 10 22 12 12 0 0 1-14 10H-12a11 11 0 0 1-10-10z" />
      <path d="M-12-38c4 2 6 2 9-1M4-44c3 3 6 3 9 1M-4-30c3 2 6 2 9 0" className="hatch" />
    </g>
  )
}

function Cloud({ x, y, s = 1 }: { x: number; y: number; s?: number }) {
  return (
    <path
      transform={`translate(${x} ${y}) scale(${s})`}
      d="M0 0h52a9 9 0 0 0-6-15 12 12 0 0 0-21-6 10 10 0 0 0-17 6A8 8 0 0 0 0 0z"
      className="cloud"
    />
  )
}

export function CampusIllustration() {
  return (
    <svg className="campus-art" viewBox="0 0 620 400" aria-hidden="true" focusable="false">
      <Cloud x={70} y={70} s={1.2} />
      <Cloud x={420} y={50} />
      <Cloud x={520} y={110} s={0.8} />

      {/* far buildings */}
      <g className="far">
        <path d="M40 360V250h50v-20h30v130M470 360V240h40v-25h40v25h30v120" />
        {range(4).map((i) => (
          <path key={i} d={`M${52 + i * 18} 270v14M${484 + i * 22} 255v14`} />
        ))}
      </g>

      {/* left wing */}
      <path d="M150 360V200h112v160M146 200h120l-6-12H152z" />
      {range(3).map((r) =>
        range(5).map((c) => <ArchWindow key={`l${r}${c}`} x={160 + c * 20} y={214 + r * 46} />),
      )}
      {/* right wing */}
      <path d="M358 360V200h112v160M354 200h120l-6-12H360z" />
      {range(3).map((r) =>
        range(5).map((c) => <ArchWindow key={`r${r}${c}`} x={367 + c * 20} y={214 + r * 46} />),
      )}

      {/* clock tower */}
      <path d="M262 360V120h96v240M256 120h108l-8-14H264zM270 106V86h80v20M276 86l34-44 34 44M310 42V18" />
      <path d="M310 18l14 5-14 5" className="accent" />
      <circle cx="310" cy="146" r="17" />
      <circle cx="310" cy="146" r="13" className="thin" />
      <path d="M310 146v-9M310 146l6 4" className="accent" />
      {range(3).map((r) =>
        range(3).map((c) => <ArchWindow key={`t${r}${c}`} x={276 + c * 26} y={180 + r * 42} w={14} h={24} />),
      )}
      <path d="M290 360v-30a20 20 0 0 1 40 0v30" />
      <path d="M282 360h56M276 366h68M270 372h80" className="thin" />

      {/* trees and ground */}
      <Tree x={110} y={362} s={1.25} />
      <Tree x={520} y={362} s={1.4} />
      <Tree x={585} y={364} s={0.9} />
      <Tree x={30} y={364} s={0.85} />
      <path d="M0 374h620" />
      <path d="M20 382h120M200 382h90M380 382h140" className="thin" />
    </svg>
  )
}
