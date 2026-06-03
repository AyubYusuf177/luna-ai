import React, { useState } from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Theme } from '@tamagui/core'
import { YStack } from '../src/primitives/Stack'
import { Input } from '../src/primitives/Input'
import { Caption } from '../src/primitives/Text'

const meta = {
  title: 'Primitives/Input',
  component: Input,
  parameters: { layout: 'centered' },
  argTypes: {
    disabled: { control: 'boolean' },
  },
} satisfies Meta<typeof Input>

export default meta
type Story = StoryObj<typeof meta>

export const Default: Story = {
  args: {
    label: 'Destination',
    placeholder: 'e.g. Tokyo, Japan',
    helperText: 'Where would you like to travel?',
  },
}

const ControlledInput = () => {
  const [value, setValue] = useState('')
  return (
    <Input
      label="Destination"
      placeholder="e.g. Tokyo, Japan"
      value={value}
      onChange={setValue}
      helperText="Type to see the controlled state."
    />
  )
}

export const Controlled: Story = {
  render: () => (
    <YStack padding="$4" minWidth={320}>
      <ControlledInput />
    </YStack>
  ),
}

export const StateMatrix: Story = {
  render: () => (
    <YStack gap="$5" padding="$4" minWidth={340}>
      <YStack gap="$2">
        <Caption>Default</Caption>
        <Input label="Origin" placeholder="London Heathrow" />
      </YStack>

      <YStack gap="$2">
        <Caption>With helper text</Caption>
        <Input
          label="Dates"
          placeholder="e.g. 12–19 Jun"
          helperText="Flexible dates improve options."
        />
      </YStack>

      <YStack gap="$2">
        <Caption>Error state</Caption>
        <Input
          label="Budget"
          placeholder="£500"
          errorText="Please enter a valid budget."
        />
      </YStack>

      <YStack gap="$2">
        <Caption>Disabled</Caption>
        <Input
          label="Passenger name"
          placeholder="Locked"
          disabled
          helperText="This field is read-only."
        />
      </YStack>
    </YStack>
  ),
}

export const DarkMode: Story = {
  render: () => (
    <Theme name="dark">
      <YStack backgroundColor="$background" padding="$6" gap="$4" borderRadius="$3" minWidth={340}>
        <Caption color="$colorHover">Dark mode inputs</Caption>
        <Input label="Destination" placeholder="e.g. Tokyo" />
        <Input label="Budget" placeholder="£500" errorText="Invalid value." />
        <Input label="Locked" placeholder="Read only" disabled />
      </YStack>
    </Theme>
  ),
}
