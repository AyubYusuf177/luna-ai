'use client'
import React from 'react'
import { YStack, Heading, Body, Caption } from '@luna/ui'

export default function ActionsPage() {
  return (
    <YStack gap="$4" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Actions</Heading>
        <Caption color="$colorHover">Pending approvals and Luna's suggested next steps.</Caption>
      </YStack>
      <Body color="$colorHover">
        No pending actions. Luna will surface things here when she needs your input — confirmations, booking approvals, or proactive suggestions.
      </Body>
    </YStack>
  )
}
