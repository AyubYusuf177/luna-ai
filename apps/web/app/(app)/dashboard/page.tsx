'use client'
import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card, Badge } from '@luna/ui'

export default function DashboardPage() {
  return (
    <YStack gap="$6" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Dashboard</Heading>
        <Caption color="$colorHover">Your Luna overview.</Caption>
      </YStack>

      <YStack gap="$3">
        <Card header={<XStack justifyContent="space-between"><Body fontWeight="600">Integrations</Body><Badge status="pending">Not connected</Badge></XStack>}>
          <Body color="$colorHover">Connect Gmail and Calendar to unlock Luna's full capabilities.</Body>
        </Card>

        <Card header={<XStack justifyContent="space-between"><Body fontWeight="600">Messaging channels</Body><Badge status="pending">Not connected</Badge></XStack>}>
          <Body color="$colorHover">Connect SMS or WhatsApp to start texting Luna.</Body>
        </Card>

        <Card header={<XStack justifyContent="space-between"><Body fontWeight="600">Active trips</Body><Badge status="info">0</Badge></XStack>}>
          <Body color="$colorHover">No active trips. Text Luna to start planning.</Body>
        </Card>
      </YStack>
    </YStack>
  )
}
