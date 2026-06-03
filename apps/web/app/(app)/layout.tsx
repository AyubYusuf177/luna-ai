'use client'
import React, { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import Link from 'next/link'
import { XStack, YStack, Body, Label, Caption } from '@luna/ui'

const ONBOARDING_KEY = 'luna:onboarding_complete'

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/integrations', label: 'Integrations' },
  { href: '/channels', label: 'Channels' },
  { href: '/actions', label: 'Actions' },
  { href: '/vault', label: 'Travel Vault' },
  { href: '/trips', label: 'Trips' },
  { href: '/settings', label: 'Settings' },
]

export default function AppLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (typeof window !== 'undefined' && !localStorage.getItem(ONBOARDING_KEY)) {
      router.replace('/onboarding')
    }
  }, [router])

  return (
    <XStack minHeight="100vh">
      <YStack
        width={240}
        minHeight="100vh"
        backgroundColor="$backgroundStrong"
        borderRightWidth={1}
        borderRightColor="$borderColor"
        padding="$4"
        gap="$1"
      >
        <YStack paddingHorizontal="$3" paddingVertical="$4" marginBottom="$2">
          <Label color="$brand">Luna</Label>
          <Caption color="$colorHover">Travel operator</Caption>
        </YStack>

        {navItems.map(item => {
          const active = pathname === item.href
          return (
            <Link key={item.href} href={item.href} style={{ textDecoration: 'none' }}>
              <YStack
                paddingHorizontal="$3"
                paddingVertical="$2"
                borderRadius="$2"
                backgroundColor={active ? '$brandMuted' : 'transparent'}
                hoverStyle={{ backgroundColor: '$backgroundHover' }}
              >
                <Body color={active ? '$brand' : '$color'}>{item.label}</Body>
              </YStack>
            </Link>
          )
        })}
      </YStack>

      <YStack flex={1} backgroundColor="$background" padding="$8" overflow="scroll">
        {children}
      </YStack>
    </XStack>
  )
}
