import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Theme } from '@tamagui/core'
import { XStack, YStack } from '../src/primitives/Stack'
// XStack and YStack are defined in our Stack primitive
import { Body, Caption } from '../src/primitives/Text'

const meta = {
  title: 'Primitives/Stack',
  parameters: { layout: 'centered' },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

const Box = ({ label }: { label: string }) => (
  <XStack
    backgroundColor="$brandMuted"
    borderRadius="$2"
    padding="$3"
    alignItems="center"
    justifyContent="center"
    minWidth={64}
  >
    <Caption color="$brand">{label}</Caption>
  </XStack>
)

export const Horizontal: Story = {
  render: () => (
    <XStack gap="$3" alignItems="center">
      <Box label="A" />
      <Box label="B" />
      <Box label="C" />
    </XStack>
  ),
}

export const Vertical: Story = {
  render: () => (
    <YStack gap="$3">
      <Box label="A" />
      <Box label="B" />
      <Box label="C" />
    </YStack>
  ),
}

export const StateMatrix: Story = {
  render: () => (
    <YStack gap="$6" padding="$4" maxWidth={480}>
      <YStack gap="$2">
        <Caption>XStack — horizontal, gap $3</Caption>
        <XStack gap="$3">
          <Box label="A" /><Box label="B" /><Box label="C" />
        </XStack>
      </YStack>

      <YStack gap="$2">
        <Caption>XStack — space-between</Caption>
        <XStack justifyContent="space-between" width="100%">
          <Box label="Left" /><Box label="Right" />
        </XStack>
      </YStack>

      <YStack gap="$2">
        <Caption>YStack — vertical, gap $2</Caption>
        <YStack gap="$2">
          <Box label="Top" /><Box label="Middle" /><Box label="Bottom" />
        </YStack>
      </YStack>

      <YStack gap="$2">
        <Caption>Nested</Caption>
        <XStack gap="$3">
          <YStack gap="$2"><Box label="1" /><Box label="2" /></YStack>
          <YStack gap="$2"><Box label="3" /><Box label="4" /></YStack>
        </XStack>
      </YStack>
    </YStack>
  ),
}

export const DarkMode: Story = {
  render: () => (
    <Theme name="dark">
      <YStack backgroundColor="$background" padding="$6" gap="$4" borderRadius="$3">
        <Body>Dark mode stack layout</Body>
        <XStack gap="$3">
          <Box label="A" /><Box label="B" /><Box label="C" />
        </XStack>
      </YStack>
    </Theme>
  ),
}
