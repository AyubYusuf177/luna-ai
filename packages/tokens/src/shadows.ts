// Web box-shadow values — used in styled components via style prop
export const webShadows = {
  sm: '0 1px 2px rgba(0,0,0,0.06), 0 1px 3px rgba(0,0,0,0.10)',
  md: '0 4px 6px rgba(0,0,0,0.07), 0 2px 4px rgba(0,0,0,0.06)',
  lg: '0 10px 15px rgba(0,0,0,0.10), 0 4px 6px rgba(0,0,0,0.05)',
} as const

// Native elevation values — used on React Native via elevation prop
export const nativeElevation = {
  sm: 2,
  md: 4,
  lg: 8,
} as const
