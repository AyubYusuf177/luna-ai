import React from 'react'
import { styled, Text } from '@tamagui/core'
import { XStack } from './Stack'

const ButtonFrame = styled(XStack, {
  alignItems: 'center',
  justifyContent: 'center',
  borderRadius: '$3',
  cursor: 'pointer',
  userSelect: 'none',

  variants: {
    variant: {
      primary: {
        backgroundColor: '$brand',
        hoverStyle: { backgroundColor: '$brandHover' },
        pressStyle: { backgroundColor: '$brandPress', scale: 0.98 },
      },
      secondary: {
        backgroundColor: '$background',
        borderWidth: 1,
        borderColor: '$borderColor',
        hoverStyle: { backgroundColor: '$backgroundHover', borderColor: '$borderColorHover' },
        pressStyle: { backgroundColor: '$backgroundPress', scale: 0.98 },
      },
      ghost: {
        backgroundColor: 'transparent',
        hoverStyle: { backgroundColor: '$backgroundHover' },
        pressStyle: { backgroundColor: '$backgroundPress', scale: 0.98 },
      },
      destructive: {
        backgroundColor: '$error',
        hoverStyle: { opacity: 0.88 },
        pressStyle: { opacity: 0.80, scale: 0.98 },
      },
    },
    size: {
      sm: { height: 32, paddingHorizontal: '$3', gap: '$1' },
      md: { height: 40, paddingHorizontal: '$4', gap: '$2' },
      lg: { height: 48, paddingHorizontal: '$6', gap: '$2' },
    },
    disabled: {
      true: {
        opacity: 0.38,
        cursor: 'not-allowed',
        pointerEvents: 'none',
      },
    },
  } as const,

  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
})

const ButtonLabel = styled(Text, {
  fontFamily: '$body',
  fontWeight: '600',
  variants: {
    variant: {
      primary:     { color: '$brandText' },
      secondary:   { color: '$color' },
      ghost:       { color: '$color' },
      destructive: { color: '$brandText' },
    },
    size: {
      sm: { fontSize: '$3' },
      md: { fontSize: '$4' },
      lg: { fontSize: '$5' },
    },
  } as const,
  defaultVariants: {
    variant: 'primary',
    size: 'md',
  },
})

export interface ButtonProps {
  variant?: 'primary' | 'secondary' | 'ghost' | 'destructive'
  size?: 'sm' | 'md' | 'lg'
  disabled?: boolean
  loading?: boolean
  children?: React.ReactNode
  onPress?: () => void
}

export function Button({
  variant = 'primary',
  size = 'md',
  disabled = false,
  loading = false,
  children,
  onPress,
}: ButtonProps) {
  return (
    <ButtonFrame
      variant={variant}
      size={size}
      disabled={disabled || loading}
      onPress={onPress}
    >
      {loading ? (
        <ButtonLabel variant={variant} size={size} opacity={0.7}>
          •••
        </ButtonLabel>
      ) : (
        <ButtonLabel variant={variant} size={size}>
          {children}
        </ButtonLabel>
      )}
    </ButtonFrame>
  )
}
