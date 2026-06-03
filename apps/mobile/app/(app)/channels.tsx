import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card, Badge } from '@luna/ui'

export default function ChannelsScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$4">
      <YStack gap="$1">
        <Heading size="md">Messaging channels</Heading>
        <Caption color="$colorHover">
          SMS and WhatsApp are how you talk to Luna every day.
        </Caption>
      </YStack>

      <YStack gap="$3">
        <Card pressable>
          <XStack justifyContent="space-between" alignItems="center">
            <Body fontWeight="600">SMS</Body>
            <Badge status="pending">Set up</Badge>
          </XStack>
          <Caption color="$colorHover">Text Luna directly from your phone number.</Caption>
        </Card>

        <Card pressable>
          <XStack justifyContent="space-between" alignItems="center">
            <Body fontWeight="600">WhatsApp</Body>
            <Badge status="pending">Set up</Badge>
          </XStack>
          <Caption color="$colorHover">
            Richer messages, images, and booking confirmations.
          </Caption>
        </Card>
      </YStack>
    </YStack>
  )
}
