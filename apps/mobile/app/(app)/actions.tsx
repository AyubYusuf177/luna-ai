import React from 'react'
import { YStack, Heading, Body, Caption } from '@luna/ui'

export default function ActionsScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$4">
      <YStack gap="$1">
        <Heading size="md">Actions</Heading>
        <Caption color="$colorHover">Pending approvals and Luna's suggested next steps.</Caption>
      </YStack>
      <Body color="$colorHover">
        No pending actions. Luna will surface things here when she needs your input.
      </Body>
    </YStack>
  )
}
