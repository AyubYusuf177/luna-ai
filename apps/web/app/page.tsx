'use client'
import React, { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { YStack } from '@luna/ui'

const ONBOARDING_KEY = 'luna:onboarding_complete'

export default function RootPage() {
  const router = useRouter()

  useEffect(() => {
    if (typeof window !== 'undefined') {
      const done = localStorage.getItem(ONBOARDING_KEY)
      if (done === 'true') {
        router.replace('/dashboard')
      } else {
        router.replace('/sign-in')
      }
    }
  }, [router])

  return <YStack flex={1} minHeight="100vh" backgroundColor="$background" />
}
