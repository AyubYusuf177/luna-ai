import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Theme } from '@tamagui/core'
import { XStack, YStack } from '../src/primitives/Stack'
import { Badge } from '../src/primitives/Badge'
import { Caption, Label } from '../src/primitives/Text'

const meta = {
  title: 'Primitives/Badge',
  component: Badge,
  parameters: { layout: 'centered' },
  argTypes: {
    status: {
      control: 'select',
      options: ['default', 'confirmed', 'pending', 'cancelled', 'info', 'brand'],
    },
  },
} satisfies Meta<typeof Badge>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    status: 'confirmed',
    children: 'Confirmed',
  },
}

export const StateMatrix: Story = {
  render: () => (
    <YStack gap="$5" padding="$4">
      <YStack gap="$2">
        <Caption>All status variants</Caption>
        <XStack gap="$2" flexWrap="wrap">
          <Badge status="default">Default</Badge>
          <Badge status="confirmed">Confirmed</Badge>
          <Badge status="pending">Pending</Badge>
          <Badge status="cancelled">Cancelled</Badge>
          <Badge status="info">Info</Badge>
          <Badge status="brand">Luna</Badge>
        </XStack>
      </YStack>

      <YStack gap="$2">
        <Caption>Travel context examples</Caption>
        <XStack gap="$2" flexWrap="wrap">
          <Badge status="confirmed">Flight booked</Badge>
          <Badge status="pending">Awaiting confirmation</Badge>
          <Badge status="cancelled">Trip cancelled</Badge>
          <Badge status="info">Price drop alert</Badge>
          <Badge status="brand">Luna pick</Badge>
        </XStack>
      </YStack>

      <YStack gap="$3">
        <Caption>Inline with label</Caption>
        <XStack gap="$2" alignItems="center">
          <Label>London → Tokyo</Label>
          <Badge status="confirmed">Confirmed</Badge>
        </XStack>
        <XStack gap="$2" alignItems="center">
          <Label>Rome weekender</Label>
          <Badge status="pending">Pending</Badge>
        </XStack>
        <XStack gap="$2" alignItems="center">
          <Label>NYC business trip</Label>
          <Badge status="cancelled">Cancelled</Badge>
        </XStack>
      </YStack>
    </YStack>
  ),
}

export const DarkMode: Story = {
  render: () => (
    <Theme name="dark">
      <YStack backgroundColor="$background" padding="$6" gap="$3" borderRadius="$3">
        <Caption color="$colorHover">Dark mode badges</Caption>
        <XStack gap="$2" flexWrap="wrap">
          <Badge status="default">Default</Badge>
          <Badge status="confirmed">Confirmed</Badge>
          <Badge status="pending">Pending</Badge>
          <Badge status="cancelled">Cancelled</Badge>
          <Badge status="info">Info</Badge>
          <Badge status="brand">Luna</Badge>
        </XStack>
      </YStack>
    </Theme>
  ),
}
