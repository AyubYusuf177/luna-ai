import React from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Button, Badge, Card } from '@luna/ui'

const TOTAL = 7
const STEP = 5

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

export default function ChannelsScreen() {
  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$4">
        <Heading size="md">Luna lives in your messages.</Heading>
        <Body color="$colorHover">
          Day to day, you text Luna. She searches, plans, and follows up — all through SMS or WhatsApp.
        </Body>

        <YStack gap="$3" marginTop="$2">
          <Card>
            <XStack gap="$3" alignItems="center">
              <Badge status="info">SMS</Badge>
              <YStack flex={1}>
                <Body fontWeight="600">Text message</Body>
                <Body color="$colorHover" fontSize="$3">Works on any phone, no app required.</Body>
              </YStack>
            </XStack>
          </Card>

          <Card>
            <XStack gap="$3" alignItems="center">
              <Badge status="confirmed">WA</Badge>
              <YStack flex={1}>
                <Body fontWeight="600">WhatsApp</Body>
                <Body color="$colorHover" fontSize="$3">Richer messages, images, and confirmations.</Body>
              </YStack>
            </XStack>
          </Card>
        </YStack>
      </YStack>

      <YStack padding="$6" paddingBottom="$12">
        <Button
          variant="primary"
          size="lg"
          onPress={() => router.push('/(onboarding)/next')}
        >
          Continue
        </Button>
      </YStack>
    </YStack>
  )
}
