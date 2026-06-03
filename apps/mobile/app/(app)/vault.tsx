import React from 'react'
import { YStack, Heading, Body, Caption } from '@luna/ui'

export default function VaultScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$4">
      <YStack gap="$1">
        <Heading size="md">Travel vault</Heading>
        <Caption color="$colorHover">Your travel preferences, documents, and history.</Caption>
      </YStack>
      <Body color="$colorHover">
        Your travel profile will build up here as Luna learns your preferences.
      </Body>
    </YStack>
  )
}
