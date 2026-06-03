import React from 'react'
import { Slot } from 'expo-router'
import { TamaguiProvider } from '@tamagui/core'
import type { TamaguiProviderProps } from '@tamagui/core'
import config from '@luna/tokens'

export default function RootLayout() {
  return (
    <TamaguiProvider config={config as unknown as TamaguiProviderProps['config']} defaultTheme="dark">
      <Slot />
    </TamaguiProvider>
  )
}
