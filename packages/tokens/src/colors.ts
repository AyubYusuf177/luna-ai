export const palette = {
  // Sand — warm neutral base
  sand50:  '#fafaf9',
  sand100: '#f5f5f4',
  sand200: '#e7e5e4',
  sand300: '#d6d3d1',
  sand400: '#a8a29e',
  sand500: '#78716c',
  sand600: '#57534e',
  sand700: '#44403c',
  sand800: '#292524',
  sand900: '#1c1917',
  sand950: '#0c0a09',

  // Plum — Luna brand primary
  plum50:  '#faf5ff',
  plum100: '#f3e8ff',
  plum200: '#e9d5ff',
  plum300: '#d8b4fe',
  plum400: '#c084fc',
  plum500: '#a855f7',
  plum600: '#9333ea',
  plum700: '#7e22ce',
  plum800: '#6b21a8',
  plum900: '#581c87',
  plum950: '#3b0764',

  // Sky — accent / info
  sky50:   '#f0f9ff',
  sky100:  '#e0f2fe',
  sky200:  '#bae6fd',
  sky300:  '#7dd3fc',
  sky400:  '#38bdf8',
  sky500:  '#0ea5e9',
  sky600:  '#0284c7',
  sky700:  '#0369a1',
  sky800:  '#075985',
  sky900:  '#0c4a6e',
  sky950:  '#082f49',

  // Rose — error / destructive
  rose50:  '#fff1f2',
  rose100: '#ffe4e6',
  rose200: '#fecdd3',
  rose300: '#fda4af',
  rose400: '#fb7185',
  rose500: '#f43f5e',
  rose600: '#e11d48',
  rose700: '#be123c',
  rose800: '#9f1239',
  rose900: '#881337',
  rose950: '#4c0519',

  // Sage — success / confirmed
  sage50:  '#f0fdf4',
  sage100: '#dcfce7',
  sage200: '#bbf7d0',
  sage300: '#86efac',
  sage400: '#4ade80',
  sage500: '#22c55e',
  sage600: '#16a34a',
  sage700: '#15803d',
  sage800: '#166534',
  sage900: '#14532d',
  sage950: '#052e16',

  // Amber — warning
  amber50:  '#fffbeb',
  amber100: '#fef3c7',
  amber200: '#fde68a',
  amber300: '#fcd34d',
  amber400: '#fbbf24',
  amber500: '#f59e0b',
  amber600: '#d97706',
  amber700: '#b45309',
  amber800: '#92400e',
  amber900: '#78350f',
  amber950: '#451a03',

  // Absolute
  white:       '#ffffff',
  black:       '#000000',
  transparent: 'transparent',
} as const

export type PaletteKey = keyof typeof palette
