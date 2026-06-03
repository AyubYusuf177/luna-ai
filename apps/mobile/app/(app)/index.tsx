import React from 'react'
import { router } from 'expo-router'
import { YStack, XStack, Heading, Body, Caption, Button, Card, Badge } from '@luna/ui'

export default function HomeScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$5">
      <YStack gap="$1">
        <Caption color="$colorHover">Good morning</Caption>
        <Heading size="md">Your Luna</Heading>
      </YStack>

      <YStack gap="$3">
        <Card pressable onPress={() => router.push('/(app)/integrations')}>
          <XStack justifyContent="space-between" alignItems="center">
            <Body fontWeight="600">Integrations</Body>
            <Badge status="pending">Set up</Badge>
          </XStack>
          <Caption color="$colorHover">Connect Gmail and Calendar to unlock Luna.</Caption>
        </Card>

        <Card pressable onPress={() => router.push('/(app)/channels')}>
          <XStack justifyContent="space-between" alignItems="center">
            <Body fontWeight="600">Messaging channels</Body>
            <Badge status="pending">Set up</Badge>
          </XStack>
          <Caption color="$colorHover">Connect SMS or WhatsApp to start texting Luna.</Caption>
        </Card>

        <Card pressable onPress={() => router.push('/(app)/trips')}>
          <XStack justifyContent="space-between" alignItems="center">
            <Body fontWeight="600">Trips</Body>
            <Badge status="info">0 active</Badge>
          </XStack>
          <Caption color="$colorHover">Your upcoming and past trips.</Caption>
        </Card>
      </YStack>

      <Button
        variant="primary"
        size="lg"
        onPress={() => router.push('/(app)/text')}
      >
        Text Luna
      </Button>
    </YStack>
  )
}
