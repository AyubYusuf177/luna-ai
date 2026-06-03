import React from 'react'
import type { Metadata } from 'next'
import { Providers } from './providers'
import './globals.css'

export const dynamic = 'force-dynamic'

export const metadata: Metadata = {
  title: 'Luna',
  description: 'Your travel operator, inside your messages.',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>{children}</Providers>
      </body>
    </html>
  )
}
