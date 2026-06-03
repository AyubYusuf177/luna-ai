import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Theme } from '@tamagui/core'
import { XStack, YStack } from '../src/primitives/Stack'
import { Button } from '../src/primitives/Button'
import { Caption } from '../src/primitives/Text'

const meta = {
  title: 'Primitives/Button',
  component: Button,
  parameters: { layout: 'centered' },
  argTypes: {
    variant: {
      control: 'select',
      options: ['primary', 'secondary', 'ghost', 'destructive'],
    },
    size: {
      control: 'select',
      options: ['sm', 'md', 'lg'],
    },
    disabled: { control: 'boolean' },
    loading:  { control: 'boolean' },
  },
} satisfies Meta<typeof Button>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    variant: 'primary',
    size: 'md',
    children: 'Book flight',
  },
}

export const StateMatrix: Story = {
  render: () => (
    <YStack gap="$5" padding="$4">
      <YStack gap="$2">
        <Caption>Variants</Caption>
        <XStack gap="$3" flexWrap="wrap">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
        </XStack>
      </YStack>

      <YStack gap="$2">
        <Caption>Sizes</Caption>
        <XStack gap="$3" alignItems="center">
          <Button size="sm">Small</Button>
          <Button size="md">Medium</Button>
          <Button size="lg">Large</Button>
        </XStack>
      </YStack>

      <YStack gap="$2">
        <Caption>States</Caption>
        <XStack gap="$3" flexWrap="wrap">
          <Button variant="primary" disabled>Disabled</Button>
          <Button variant="primary" loading>Loading</Button>
          <Button variant="secondary" disabled>Disabled</Button>
          <Button variant="destructive">Cancel trip</Button>
        </XStack>
      </YStack>
    </YStack>
  ),
}

export const DarkMode: Story = {
  render: () => (
    <Theme name="dark">
      <YStack backgroundColor="$background" padding="$6" gap="$4" borderRadius="$3">
        <Caption color="$colorHover">Dark mode buttons</Caption>
        <XStack gap="$3" flexWrap="wrap">
          <Button variant="primary">Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="ghost">Ghost</Button>
        </XStack>
        <XStack gap="$3">
          <Button variant="primary" disabled>Disabled</Button>
          <Button variant="primary" loading>Loading</Button>
        </XStack>
      </YStack>
    </Theme>
  ),
}
