import React from 'react'
import { YStack, Heading, Body, Caption } from '@luna/ui'

export default function TripsScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$4">
      <YStack gap="$1">
        <Heading size="md">Trips</Heading>
        <Caption color="$colorHover">Upcoming, active, and past trips.</Caption>
      </YStack>
      <Body color="$colorHover">
        No trips yet. Text Luna to start planning your first one.
      </Body>
    </YStack>
  )
}
