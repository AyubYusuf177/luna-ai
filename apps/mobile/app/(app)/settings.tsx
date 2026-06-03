import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card } from '@luna/ui'

const sections = [
  { label: 'Account', desc: 'Name, email, and profile.' },
  { label: 'Notifications', desc: 'Alerts, reminders, and proactive messages.' },
  { label: 'Communication tone', desc: 'How Luna speaks to you.' },
  { label: 'Privacy', desc: 'Data, permissions, and deletion.' },
]

export default function SettingsScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$4">
      <Heading size="md">Settings</Heading>

      <YStack gap="$2">
        {sections.map(section => (
          <Card key={section.label} pressable>
            <Body fontWeight="600">{section.label}</Body>
            <Caption color="$colorHover">{section.desc}</Caption>
          </Card>
        ))}
      </YStack>
    </YStack>
  )
}
