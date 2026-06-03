import React from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Button, Badge } from '@luna/ui'

const TOTAL = 7
const STEP = 2

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

const points = [
  'Luna only reads travel data you explicitly share.',
  'Your messages are never sold or used for advertising.',
  'You can delete your data at any time from settings.',
]

export default function TrustScreen() {
  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$4">
        <Heading size="md">Your data, your terms.</Heading>
        <Body color="$colorHover">
          Luna handles your travel information with care.
        </Body>

        <YStack gap="$3" marginTop="$2">
          {points.map((point, i) => (
            <XStack key={i} gap="$3" alignItems="flex-start">
              <Badge status="confirmed">✓</Badge>
              <Body flex={1}>{point}</Body>
            </XStack>
          ))}
        </YStack>
      </YStack>

      <YStack padding="$6" paddingBottom="$12">
        <Button
          variant="primary"
          size="lg"
          onPress={() => router.push('/(onboarding)/focus')}
        >
          I understand, continue
        </Button>
      </YStack>
    </YStack>
  )
}
