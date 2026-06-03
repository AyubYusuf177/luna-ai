'use client'
import React from 'react'
import { YStack, Heading, Body, Caption } from '@luna/ui'

export default function VaultPage() {
  return (
    <YStack gap="$4" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Travel vault</Heading>
        <Caption color="$colorHover">Your travel preferences, history, and saved context.</Caption>
      </YStack>
      <Body color="$colorHover">
        Your travel profile builds up here as Luna learns your preferences — home airports, seat preferences, hotel style, and past destinations.
      </Body>
    </YStack>
  )
}
