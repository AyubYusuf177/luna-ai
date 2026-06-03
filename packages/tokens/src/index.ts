import { createTamagui, createTokens } from '@tamagui/core'
import { palette } from './colors'
import { spacingScale } from './spacing'
import { radiiScale } from './radii'
import {
  bodyFontFamily,
  monoFontFamily,
  fontSizes,
  lineHeights,
  fontWeights,
  letterSpacings,
} from './typography'

const tokens = createTokens({
  color: palette,
  space: spacingScale,
  size: {
    true: 44,
    0: 0,
    1: 16,
    2: 32,
    3: 44,
    4: 56,
    5: 64,
    6: 80,
  },
  radius: radiiScale,
  zIndex: {
    0: 0,
    1: 100,
    2: 200,
    3: 300,
    4: 400,
    5: 500,
  },
})

const lightTheme = {
  // Surfaces
  background:         palette.sand50,
  backgroundHover:    palette.sand100,
  backgroundPress:    palette.sand200,
  backgroundFocus:    palette.sand100,
  backgroundStrong:   palette.white,

  // Text
  color:              palette.sand950,
  colorHover:         palette.sand600,
  colorPress:         palette.sand950,
  colorFocus:         palette.sand950,
  colorTransparent:   palette.transparent,

  // Borders
  borderColor:        palette.sand200,
  borderColorHover:   palette.sand300,
  borderColorFocus:   palette.plum600,
  borderColorPress:   palette.sand300,

  // Input
  placeholderColor:   palette.sand400,

  // Shadow
  shadowColor:        'rgba(0,0,0,0.08)',
  shadowColorHover:   'rgba(0,0,0,0.14)',

  // Brand — Luna plum
  brand:              palette.plum600,
  brandHover:         palette.plum700,
  brandPress:         palette.plum800,
  brandMuted:         palette.plum100,
  brandText:          palette.white,

  // Semantic
  error:              palette.rose600,
  errorMuted:         palette.rose50,
  success:            palette.sage600,
  successMuted:       palette.sage50,
  warning:            palette.amber600,
  warningMuted:       palette.amber50,
  info:               palette.sky600,
  infoMuted:          palette.sky50,
}

type LunaTheme = Record<keyof typeof lightTheme, string>

const darkTheme: LunaTheme = {
  background:         palette.sand950,
  backgroundHover:    palette.sand900,
  backgroundPress:    palette.sand800,
  backgroundFocus:    palette.sand900,
  backgroundStrong:   palette.sand900,

  color:              palette.sand50,
  colorHover:         palette.sand400,
  colorPress:         palette.sand50,
  colorFocus:         palette.sand50,
  colorTransparent:   palette.transparent,

  borderColor:        palette.sand800,
  borderColorHover:   palette.sand700,
  borderColorFocus:   palette.plum400,
  borderColorPress:   palette.sand700,

  placeholderColor:   palette.sand600,

  shadowColor:        'rgba(0,0,0,0.40)',
  shadowColorHover:   'rgba(0,0,0,0.55)',

  brand:              palette.plum400,
  brandHover:         palette.plum300,
  brandPress:         palette.plum200,
  brandMuted:         palette.plum900,
  brandText:          palette.white,

  error:              palette.rose400,
  errorMuted:         palette.rose950,
  success:            palette.sage400,
  successMuted:       palette.sage950,
  warning:            palette.amber400,
  warningMuted:       palette.amber950,
  info:               palette.sky400,
  infoMuted:          palette.sky950,
}

export const config = createTamagui({
  tokens,
  themes: {
    light: lightTheme,
    dark: darkTheme,
  },
  fonts: {
    body: {
      family: bodyFontFamily,
      size: fontSizes,
      lineHeight: lineHeights,
      weight: fontWeights,
      letterSpacing: letterSpacings,
      face: {},
    },
    mono: {
      family: monoFontFamily,
      size: fontSizes,
      lineHeight: lineHeights,
      weight: fontWeights,
      letterSpacing: letterSpacings,
      face: {},
    },
  },
  defaultTheme: 'light',
  shouldAddPrefersColorTheme: false,
  disableSSR: true,
  shorthands: {
    px: 'paddingHorizontal',
    py: 'paddingVertical',
    mx: 'marginHorizontal',
    my: 'marginVertical',
  } as const,
})

export type AppConfig = typeof config

declare module '@tamagui/core' {
  interface TamaguiCustomConfig extends AppConfig {}
}

export { palette } from './colors'
export { spacingScale } from './spacing'
export { radiiScale } from './radii'
export { webShadows, nativeElevation } from './shadows'
export default config
