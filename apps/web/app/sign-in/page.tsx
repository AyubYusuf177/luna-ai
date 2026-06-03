'use client'
import React from 'react'
import { useRouter } from 'next/navigation'
import { YStack, Heading, Body, Button, Caption } from '@luna/ui'

export default function SignInPage() {
  const router = useRouter()
  const next = () => router.push('/onboarding')

  return (
    <YStack
      flex={1}
      minHeight="100vh"
      alignItems="center"
      justifyContent="center"
      backgroundColor="$background"
      padding="$6"
    >
      <YStack width="100%" maxWidth={400} gap="$4">
        <YStack gap="$2" marginBottom="$2">
          <Heading size="md">Welcome to Luna</Heading>
          <Body color="$colorHover">
            Your travel operator, inside your messages.
          </Body>
        </YStack>

        <Button variant="primary" size="lg" onPress={next}>
          Continue with Apple
        </Button>
        <Button variant="secondary" size="lg" onPress={next}>
          Continue with Google
        </Button>
        <Button variant="ghost" size="lg" onPress={next}>
          Continue with Email
        </Button>

        <Caption color="$colorHover" textAlign="center">
          By continuing you agree to Luna's Terms of Service and Privacy Policy.
        </Caption>
      </YStack>
    </YStack>
  )
}
