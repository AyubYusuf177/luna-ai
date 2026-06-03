import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Theme } from '@tamagui/core'
import { YStack } from '../src/primitives/Stack'
import { Heading, Body, Label, Caption, Mono } from '../src/primitives/Text'

const meta = {
  title: 'Primitives/Text',
  parameters: { layout: 'centered' },
} satisfies Meta

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  render: () => (
    <YStack gap="$3" maxWidth={480} padding="$4">
      <Heading size="lg">Heading large</Heading>
      <Heading size="md">Heading medium</Heading>
      <Heading size="sm">Heading small</Heading>
      <Body>Body text — the primary reading text used across messages and descriptions.</Body>
      <Label>Label text</Label>
      <Caption>Caption — supplementary context, timestamps, helper copy.</Caption>
      <Mono>mono: REF-2024-LON-TYO-001</Mono>
    </YStack>
  ),
}

export const StateMatrix: Story = {
  render: () => (
    <YStack gap="$5" maxWidth={520} padding="$4">
      <YStack gap="$1">
        <Caption color="$colorHover">Heading sizes</Caption>
        <Heading size="lg">Large — 30px / 700</Heading>
        <Heading size="md">Medium — 23px / 700</Heading>
        <Heading size="sm">Small — 16px / 700</Heading>
      </YStack>

      <YStack gap="$1">
        <Caption color="$colorHover">Body weights</Caption>
        <Body>Regular 400 — default reading weight</Body>
        <Body fontWeight="500">Medium 500 — emphasis without bold</Body>
        <Body fontWeight="600">Semibold 600 — strong emphasis</Body>
      </YStack>

      <YStack gap="$1">
        <Caption color="$colorHover">Supporting roles</Caption>
        <Label>Label — form fields, section titles</Label>
        <Caption>Caption — helper text, timestamps, metadata</Caption>
        <Mono>Mono — booking refs, codes: ABC-123</Mono>
      </YStack>

      <YStack gap="$1">
        <Caption color="$colorHover">Truncation</Caption>
        <Body numberOfLines={1} maxWidth={260}>
          Long text that will be truncated at a fixed width — lorem ipsum dolor sit amet.
        </Body>
      </YStack>
    </YStack>
  ),
}

export const DarkMode: Story = {
  render: () => (
    <Theme name="dark">
      <YStack backgroundColor="$background" padding="$6" gap="$3" borderRadius="$3" maxWidth={480}>
        <Heading size="md">Dark mode typography</Heading>
        <Body>Body text renders on the dark surface with full contrast.</Body>
        <Label>Label text</Label>
        <Caption>Caption — subdued, secondary</Caption>
        <Mono>Mono: REF-2024-LON-TYO</Mono>
      </YStack>
    </Theme>
  ),
}
