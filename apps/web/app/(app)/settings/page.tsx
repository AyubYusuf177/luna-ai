'use client'
import React from 'react'
import { YStack, XStack, Heading, Body, Caption, Card } from '@luna/ui'

const sections = [
  { label: 'Account', desc: 'Name, email, and profile details.' },
  { label: 'Notifications', desc: 'Email and in-app alerts from Luna.' },
  { label: 'Communication tone', desc: 'How Luna speaks to you in messages.' },
  { label: 'Privacy', desc: 'Data access, permissions, and account deletion.' },
]

export default function SettingsPage() {
  return (
    <YStack gap="$6" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Settings</Heading>
        <Caption color="$colorHover">Account and preferences.</Caption>
      </YStack>

      <YStack gap="$2">
        {sections.map(section => (
          <Card key={section.label} pressable>
            <XStack justifyContent="space-between" alignItems="center">
              <YStack gap="$1">
                <Body fontWeight="600">{section.label}</Body>
                <Caption color="$colorHover">{section.desc}</Caption>
              </YStack>
              <Caption color="$colorHover">→</Caption>
            </XStack>
          </Card>
        ))}
      </YStack>
    </YStack>
  )
}
