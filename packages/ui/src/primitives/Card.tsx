import React from 'react'
import { styled } from '@tamagui/core'
import { YStack } from './Stack'

const CardFrame = styled(YStack, {
  backgroundColor: '$background',
  borderWidth: 1,
  borderColor: '$borderColor',
  borderRadius: '$3',
  overflow: 'hidden',

  variants: {
    pressable: {
      true: {
        cursor: 'pointer',
        hoverStyle: {
          borderColor: '$borderColorHover',
          backgroundColor: '$backgroundHover',
        },
        pressStyle: {
          scale: 0.99,
          backgroundColor: '$backgroundPress',
        },
      },
    },
    elevated: {
      true: {
        shadowColor: '$shadowColor',
        shadowOffset: { width: 0, height: 2 },
        shadowOpacity: 1,
        shadowRadius: 8,
      },
    },
  } as const,
})

const CardHeader = styled(YStack, {
  paddingHorizontal: '$4',
  paddingVertical: '$3',
  borderBottomWidth: 1,
  borderBottomColor: '$borderColor',
})

const CardBody = styled(YStack, {
  padding: '$4',
})

const CardFooter = styled(YStack, {
  paddingHorizontal: '$4',
  paddingVertical: '$3',
  borderTopWidth: 1,
  borderTopColor: '$borderColor',
})

export interface CardProps {
  children?: React.ReactNode
  pressable?: boolean
  elevated?: boolean
  header?: React.ReactNode
  footer?: React.ReactNode
  onPress?: () => void
}

export function Card({ children, pressable, elevated, header, footer, onPress }: CardProps) {
  return (
    <CardFrame pressable={pressable} elevated={elevated} onPress={onPress}>
      {header && <CardHeader>{header}</CardHeader>}
      <CardBody>{children}</CardBody>
      {footer && <CardFooter>{footer}</CardFooter>}
    </CardFrame>
  )
}

export { CardFrame, CardHeader, CardBody, CardFooter }
