import React from 'react'
import { router } from 'expo-router'
import AsyncStorage from '@react-native-async-storage/async-storage'
import { YStack, XStack, Heading, Body, Button, Badge } from '@luna/ui'

const TOTAL = 7
const STEP = 6
const ONBOARDING_KEY = 'luna:onboarding_complete'

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

const steps = [
  { label: 'Today', desc: 'Start texting Luna.', status: 'confirmed' as const },
  { label: 'Next', desc: 'Connect Gmail and Calendar.', status: 'pending' as const },
  { label: 'Later', desc: 'Enable proactive travel alerts.', status: 'info' as const },
]

export default function NextScreen() {
  const finish = async () => {
    await AsyncStorage.setItem(ONBOARDING_KEY, 'true')
    router.replace('/(app)/')
  }

  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$4">
        <Heading size="md">Here's what happens next.</Heading>
        <Body color="$colorHover">
          Luna gets more useful the more you use her.
        </Body>

        <YStack gap="$3" marginTop="$2">
          {steps.map(step => (
            <XStack key={step.label} gap="$3" alignItems="flex-start">
              <Badge status={step.status}>{step.label}</Badge>
              <Body flex={1}>{step.desc}</Body>
            </XStack>
          ))}
        </YStack>
      </YStack>

      <YStack padding="$6" paddingBottom="$12">
        <Button variant="primary" size="lg" onPress={finish}>
          Start with Luna
        </Button>
      </YStack>
    </YStack>
  )
}
