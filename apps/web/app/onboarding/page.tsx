'use client'
import React from 'react'
import { useRouter } from 'next/navigation'
import { YStack, XStack, Heading, Body, Button, Caption, Badge } from '@luna/ui'

const ONBOARDING_KEY = 'luna:onboarding_complete'

export default function OnboardingPage() {
  const router = useRouter()

  const complete = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem(ONBOARDING_KEY, 'true')
    }
    router.push('/dashboard')
  }

  return (
    <YStack flex={1} minHeight="100vh" backgroundColor="$background" padding="$6">
      <YStack
        maxWidth={560}
        width="100%"
        marginHorizontal="auto"
        paddingVertical="$12"
        gap="$6"
      >
        <Badge status="brand">Luna</Badge>

        <YStack gap="$3">
          <Heading size="lg">Your travel operator, inside your messages.</Heading>
          <Body color="$colorHover">
            Luna handles flights, hotels, reminders, and travel context — all through SMS or WhatsApp. The web is for setup and control. Your messages are where Luna works.
          </Body>
        </YStack>

        <YStack gap="$3">
          {[
            { label: 'Today', desc: 'Start texting Luna.', status: 'confirmed' as const },
            { label: 'Next', desc: 'Connect Gmail and Calendar.', status: 'pending' as const },
            { label: 'Later', desc: 'Enable proactive travel alerts.', status: 'info' as const },
          ].map(step => (
            <XStack key={step.label} gap="$3" alignItems="center">
              <Badge status={step.status}>{step.label}</Badge>
              <Body>{step.desc}</Body>
            </XStack>
          ))}
        </YStack>

        <Button variant="primary" size="lg" onPress={complete}>
          Enter Luna
        </Button>

        <Caption color="$colorHover">
          Full cinematic onboarding is on mobile. This is the web control plane — account, integrations, and settings.
        </Caption>
      </YStack>
    </YStack>
  )
}
