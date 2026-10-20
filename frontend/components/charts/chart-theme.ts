export const PALETTE = ['#0f7a52', '#d4900a', '#127e8a', '#6a9e1f', '#3f5a8a', '#b4532a', '#7c6aa8', '#5b6b5f']

export const COLORS = {
  primary: '#0f7a52',
  primaryDark: '#0f3d2a',
  synthetic: '#d4900a',
  text: '#1f3329',
  muted: '#6b7d73',
  grid: '#e6ece7',
  noData: '#e7eae6',
  highlight: '#0f3d2a',
}

export const SEQUENTIAL_GREENS: [number, string][] = [
  [0, '#f0f8ef'],
  [0.2, '#cfeac8'],
  [0.4, '#98d19a'],
  [0.6, '#53ad6e'],
  [0.8, '#1f8650'],
  [1, '#0b4f31'],
]

export const FONT_FAMILY = 'Inter, ui-sans-serif, system-ui, sans-serif'

export function baseLayout(overrides: Record<string, unknown> = {}): Record<string, unknown> {
  return {
    autosize: true,
    font: { family: FONT_FAMILY, size: 12, color: COLORS.text },
    paper_bgcolor: 'rgba(0,0,0,0)',
    plot_bgcolor: 'rgba(0,0,0,0)',
    margin: { l: 56, r: 16, t: 12, b: 44 },
    hoverlabel: { bgcolor: '#ffffff', bordercolor: '#d5ddd7', font: { family: FONT_FAMILY, color: COLORS.text, size: 12 } },
    legend: { orientation: 'h', y: -0.2, x: 0, font: { size: 11, color: COLORS.muted } },
    xaxis: { gridcolor: COLORS.grid, linecolor: COLORS.grid, zeroline: false, tickfont: { color: COLORS.muted }, automargin: true },
    yaxis: { gridcolor: COLORS.grid, linecolor: COLORS.grid, zeroline: false, tickfont: { color: COLORS.muted }, automargin: true },
    ...overrides,
  }
}

/** Plotly d3-format strings for each metric. */
export const METRIC_TICKFORMAT = { production: '.3s', area: '.3s', yield: '.2f' } as const
