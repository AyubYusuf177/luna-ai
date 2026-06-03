import React from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Button, Caption } from '@luna/ui'

const TOTAL = 7
const STEP = 1

function Progress() {
  return (
    <XStack justifyContent="center" gap="$2">
      {Array.from({ length: TOTAL }).map((_, i) => (
        <YStack
          key={i}
          height={4}
          width={i === STEP ? 24 : 8}
          borderRadius="$5"
          backgroundColor={i === STEP ? '$brand' : '$borderColor'}
        />
      ))}
    </XStack>
  )
}

export default function MeetScreen() {
  const next = () => router.push('/(onboarding)/trust')

  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$2">
        <Heading size="md">Create your account</Heading>
        <Body color="$colorHover" marginBottom="$4">
          Sign in to get started with Luna.
        </Body>

        <Button variant="primary" size="lg" onPress={next}>
          Continue with Apple
        </Button>
        <Button variant="secondary" size="lg" onPress={next}>
          Continue with Google
        </Button>
        <Button variant="ghost" size="lg" onPress={next}>
          Continue with Email
        </Button>
      </YStack>

      <YStack padding="$6" paddingBottom="$12" alignItems="center">
        <Caption color="$colorHover" textAlign="center">
          By continuing you agree to Luna's Terms and Privacy Policy.
        </Caption>
      </YStack>
    </YStack>
  )
}
