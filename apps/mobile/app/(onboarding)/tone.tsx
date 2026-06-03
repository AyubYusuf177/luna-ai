import React, { useState } from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Button, Caption } from '@luna/ui'

const TOTAL = 7
const STEP = 4

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

const tones = [
  { key: 'calm', label: 'Calm & Professional', desc: 'Clear, measured, always on point.' },
  { key: 'direct', label: 'Direct & Efficient', desc: 'Fast answers, no filler.' },
  { key: 'witty', label: 'Witty & Bold', desc: 'Smart, with a bit of edge.' },
  { key: 'luxury', label: 'Luxury Concierge', desc: 'Refined, attentive, never rushed.' },
]

export default function ToneScreen() {
  const [selected, setSelected] = useState<string | null>(null)

  return (
    <YStack flex={1} backgroundColor="$background">
      <YStack padding="$6" paddingTop="$14">
        <Progress />
      </YStack>

      <YStack flex={1} padding="$6" justifyContent="center" gap="$4">
        <Heading size="md">How should Luna speak to you?</Heading>
        <Caption color="$colorHover">You can change this later in settings.</Caption>

        <YStack gap="$2" marginTop="$2">
          {tones.map(tone => {
            const active = selected === tone.key
            return (
              <YStack
                key={tone.key}
                borderWidth={1}
                borderColor={active ? '$brand' : '$borderColor'}
                borderRadius="$3"
                padding="$4"
                gap="$1"
                backgroundColor={active ? '$brandMuted' : '$background'}
                pressStyle={{ opacity: 0.8 }}
                onPress={() => setSelected(tone.key)}
              >
                <Body fontWeight="600" color={active ? '$brand' : '$color'}>
                  {tone.label}
                </Body>
                <Caption color={active ? '$brand' : '$colorHover'}>
                  {tone.desc}
                </Caption>
              </YStack>
            )
          })}
        </YStack>
      </YStack>

      <YStack padding="$6" paddingBottom="$12">
        <Button
          variant="primary"
          size="lg"
          onPress={() => router.push('/(onboarding)/channels')}
        >
          Continue
        </Button>
      </YStack>
    </YStack>
  )
}
