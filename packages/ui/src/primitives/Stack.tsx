import { Stack, styled } from '@tamagui/core'

export { Stack } from '@tamagui/core'
export type { StackProps } from '@tamagui/core'

export const XStack = styled(Stack, {
  flexDirection: 'row',
})

export const YStack = styled(Stack, {
  flexDirection: 'column',
})

export type XStackProps = React.ComponentProps<typeof XStack>
export type YStackProps = React.ComponentProps<typeof YStack>

import type React from 'react'
