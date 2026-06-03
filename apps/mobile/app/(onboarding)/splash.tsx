import React from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Button, Badge } from '@luna/ui'

const TOTAL = 7
const STEP = 0

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

export default function SplashScreen() {
  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$4">
        <Badge status="brand">Luna</Badge>
        <Heading size="lg">
          Your travel operator, inside your messages.
        </Heading>
        <Body color="$colorHover">
          Luna lives in your phone. Not in an app.
        </Body>
      </YStack>

      <YStack padding="$6" paddingBottom="$12">
        <Button
          variant="primary"
          size="lg"
          onPress={() => router.push('/(onboarding)/meet')}
        >
          Get started
        </Button>
      </YStack>
    </YStack>
  )
}
