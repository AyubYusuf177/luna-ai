'use client'
import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card, Badge, Button } from '@luna/ui'

const integrations = [
  { name: 'Gmail', desc: 'Read travel confirmation emails and build trip context automatically.', status: 'pending' as const },
  { name: 'Google Calendar', desc: 'Add flights, hotels, and travel events to your calendar.', status: 'pending' as const },
  { name: 'Google Places', desc: 'Find restaurants, hotels, and experiences near your destinations.', status: 'pending' as const },
]

export default function IntegrationsPage() {
  return (
    <YStack gap="$6" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Integrations</Heading>
        <Caption color="$colorHover">Connect services to unlock Luna's full capabilities.</Caption>
      </YStack>

      <YStack gap="$3">
        {integrations.map(item => (
          <Card
            key={item.name}
            header={
              <XStack justifyContent="space-between" alignItems="center">
                <Body fontWeight="600">{item.name}</Body>
                <Badge status={item.status}>Connect</Badge>
              </XStack>
            }
          >
            <XStack justifyContent="space-between" alignItems="center">
              <Body color="$colorHover" flex={1}>{item.desc}</Body>
              <Button variant="secondary" size="sm">Connect</Button>
            </XStack>
          </Card>
        ))}
      </YStack>
    </YStack>
  )
}
