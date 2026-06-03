import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card, Badge } from '@luna/ui'

const integrations = [
  { name: 'Gmail', desc: 'Read travel confirmation emails automatically.', status: 'pending' as const },
  { name: 'Google Calendar', desc: 'Add trip events and reminders.', status: 'pending' as const },
  { name: 'Google Places', desc: 'Find hotels, restaurants, and experiences.', status: 'pending' as const },
]

export default function IntegrationsScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$4">
      <YStack gap="$1">
        <Heading size="md">Integrations</Heading>
        <Caption color="$colorHover">Connect services to unlock Luna's full capabilities.</Caption>
      </YStack>

      <YStack gap="$3">
        {integrations.map(item => (
          <Card key={item.name} pressable>
            <XStack justifyContent="space-between" alignItems="center">
              <Body fontWeight="600">{item.name}</Body>
              <Badge status={item.status}>Connect</Badge>
            </XStack>
            <Caption color="$colorHover">{item.desc}</Caption>
          </Card>
        ))}
      </YStack>
    </YStack>
  )
}
