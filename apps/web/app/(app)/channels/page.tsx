'use client'
import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card, Badge, Button } from '@luna/ui'

export default function ChannelsPage() {
  return (
    <YStack gap="$6" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Messaging channels</Heading>
        <Caption color="$colorHover">
          SMS and WhatsApp are how you talk to Luna every day. Set up your channel here.
        </Caption>
      </YStack>

      <YStack gap="$3">
        <Card
          header={
            <XStack justifyContent="space-between" alignItems="center">
              <Body fontWeight="600">SMS</Body>
              <Badge status="pending">Not connected</Badge>
            </XStack>
          }
        >
          <XStack justifyContent="space-between" alignItems="center">
            <Body color="$colorHover" flex={1}>
              Text Luna from your phone number. Works on any device, no app needed.
            </Body>
            <Button variant="secondary" size="sm">Set up</Button>
          </XStack>
        </Card>

        <Card
          header={
            <XStack justifyContent="space-between" alignItems="center">
              <Body fontWeight="600">WhatsApp</Body>
              <Badge status="pending">Not connected</Badge>
            </XStack>
          }
        >
          <XStack justifyContent="space-between" alignItems="center">
            <Body color="$colorHover" flex={1}>
              Richer messages with images, confirmations, and structured replies.
            </Body>
            <Button variant="secondary" size="sm">Set up</Button>
          </XStack>
        </Card>
      </YStack>
    </YStack>
  )
}
