import React, { useState } from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Button, Caption } from '@luna/ui'

const TOTAL = 7
const STEP = 3

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

const options = [
  'Find cheaper flights',
  'Plan new trips',
  'Organise existing trips',
  'Discover events & experiences',
  'Reminders & itineraries',
]

export default function FocusScreen() {
  const [selected, setSelected] = useState<Set<string>>(new Set())

  const toggle = (item: string) => {
    setSelected(prev => {
      const next = new Set(prev)
      if (next.has(item)) next.delete(item)
      else next.add(item)
      return next
    })
  }

  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$4">
        <Heading size="md">What matters most to you?</Heading>
        <Caption color="$colorHover">Select all that apply.</Caption>

        <YStack gap="$2" marginTop="$2">
          {options.map(option => {
            const active = selected.has(option)
            return (
              <YStack
                key={option}
                borderWidth={1}
                borderColor={active ? '$brand' : '$borderColor'}
                borderRadius="$3"
                padding="$4"
                backgroundColor={active ? '$brandMuted' : '$background'}
                pressStyle={{ opacity: 0.8 }}
                onPress={() => toggle(option)}
              >
                <Body color={active ? '$brand' : '$color'}>{option}</Body>
              </YStack>
            )
          })}
        </YStack>
      </YStack>

      <YStack padding="$6" paddingBottom="$12">
        <Button
          variant="primary"
          size="lg"
          onPress={() => router.push('/(onboarding)/tone')}
        >
          Continue
        </Button>
      </YStack>
    </YStack>
  )
}
