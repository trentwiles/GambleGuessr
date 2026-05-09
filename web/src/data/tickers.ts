export type Ticker = {
  id: string
  name: string
  description: string
  value: number
  change: number
  changePercent: number
}

export const TICKERS: Ticker[] = [
  {
    id: 'OVR',
    name: 'Overall Rating',
    description: 'Aggregate skill rating across all modes.',
    value: 1487,
    change: 12,
    changePercent: 0.81,
  },
  {
    id: 'SDR',
    name: 'Standard Duel Rating',
    description: 'ELO in standard 1v1 duels.',
    value: 1342,
    change: -23,
    changePercent: -1.69,
  },
  {
    id: 'NMR',
    name: 'No-Move Duel Rating',
    description: 'ELO in no-move duels.',
    value: 1556,
    change: 41,
    changePercent: 2.71,
  },
  {
    id: 'TGA',
    name: '3-Game Average',
    description: 'Mean points over the last 3 singleplayer games.',
    value: 21430,
    change: 1820,
    changePercent: 9.28,
  },
  {
    id: 'FGA',
    name: '5-Game Average',
    description: 'Mean points over the last 5 singleplayer games.',
    value: 19874,
    change: -612,
    changePercent: -2.99,
  },
  {
    id: 'DWR',
    name: 'Duel Winrate (30d)',
    description: 'Win percentage in duels over the last 30 days.',
    value: 0.547,
    change: 0.022,
    changePercent: 4.19,
  },
]

export function getTicker(id: string): Ticker | undefined {
  return TICKERS.find((t) => t.id.toLowerCase() === id.toLowerCase())
}
