'use client'
import React from 'react'
import { TamaguiProvider } from '@tamagui/core'
import config from '@luna/tokens'

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <TamaguiProvider config={config} defaultTheme="light">
      {children}
    </TamaguiProvider>
  )
}
