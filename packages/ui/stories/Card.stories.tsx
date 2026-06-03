import React from 'react'
import type { Meta, StoryObj } from '@storybook/react'
import { Theme } from '@tamagui/core'
import { XStack, YStack } from '../src/primitives/Stack'
import { Card } from '../src/primitives/Card'
import { Body, Heading, Caption, Label } from '../src/primitives/Text'
import { Badge } from '../src/primitives/Badge'
import { Button } from '../src/primitives/Button'

const meta = {
  title: 'Primitives/Card',
  component: Card,
  parameters: { layout: 'centered' },
  argTypes: {
    pressable: { control: 'boolean' },
    elevated:  { control: 'boolean' },
  },
} satisfies Meta<typeof Card>

export default meta
type Story = StoryObj<typeof meta>

const FlightCard = ({ pressable }: { pressable?: boolean }) => (
  <Card
    pressable={pressable}
    header={
      <XStack justifyContent="space-between" alignItems="center">
        <Label>London → Tokyo</Label>
        <Badge status="confirmed">Confirmed</Badge>
      </XStack>
    }
    footer={
      <XStack justifyContent="flex-end">
        <Button variant="ghost" size="sm">View details</Button>
      </XStack>
    }
  >
    <YStack gap="$1">
      <Heading size="sm">£542 return</Heading>
      <Caption>12 Jun – 19 Jun · Economy · Japan Airlines</Caption>
    </YStack>
  </Card>
)

export const Default: Story = {
  args: { pressable: false, elevated: false },
  render: (args) => (
    <YStack padding="$4" minWidth={360}>
      <FlightCard pressable={args.pressable} />
    </YStack>
  ),
}

export const StateMatrix: Story = {
  render: () => (
    <YStack gap="$4" padding="$4" maxWidth={420}>
      <YStack gap="$2">
        <Caption>Default</Caption>
        <Card>
          <Body>Simple card with body content only.</Body>
        </Card>
      </YStack>

      <YStack gap="$2">
        <Caption>Pressable</Caption>
        <FlightCard pressable />
      </YStack>

      <YStack gap="$2">
        <Caption>Elevated</Caption>
        <Card elevated header={<Label>Elevation shadow</Label>}>
          <Body>Elevated surface with shadow depth.</Body>
        </Card>
      </YStack>

      <YStack gap="$2">
        <Caption>Header + Footer</Caption>
        <Card
          header={<Label>Trip: Rome weekender</Label>}
          footer={<Button variant="secondary" size="sm">Manage trip</Button>}
        >
          <Body>Card with header, body, and footer sections.</Body>
        </Card>
      </YStack>
    </YStack>
  ),
}

export const DarkMode: Story = {
  render: () => (
    <Theme name="dark">
      <YStack backgroundColor="$background" padding="$6" gap="$4" borderRadius="$3" minWidth={400}>
        <Caption color="$colorHover">Dark mode cards</Caption>
        <FlightCard />
        <Card elevated>
          <Body>Elevated card in dark mode.</Body>
        </Card>
      </YStack>
    </Theme>
  ),
}
