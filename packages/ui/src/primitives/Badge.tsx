import { styled, Text } from '@tamagui/core'
import { XStack } from './Stack'

const BadgeFrame = styled(XStack, {
  alignItems: 'center',
  justifyContent: 'center',
  paddingHorizontal: '$2',
  paddingVertical: '$1',
  borderRadius: '$5',

  variants: {
    status: {
      default:   { backgroundColor: '$backgroundStrong', borderWidth: 1, borderColor: '$borderColor' },
      confirmed: { backgroundColor: '$successMuted' },
      pending:   { backgroundColor: '$warningMuted' },
      cancelled: { backgroundColor: '$errorMuted' },
      info:      { backgroundColor: '$infoMuted' },
      brand:     { backgroundColor: '$brandMuted' },
    },
  } as const,
  defaultVariants: {
    status: 'default',
  },
})

const BadgeText = styled(Text, {
  fontFamily: '$body',
  fontSize: '$2',
  fontWeight: '600',
  letterSpacing: 0.3,

  variants: {
    status: {
      default:   { color: '$colorHover' },
      confirmed: { color: '$success' },
      pending:   { color: '$warning' },
      cancelled: { color: '$error' },
      info:      { color: '$info' },
      brand:     { color: '$brand' },
    },
  } as const,
  defaultVariants: {
    status: 'default',
  },
})

export type BadgeStatus = 'default' | 'confirmed' | 'pending' | 'cancelled' | 'info' | 'brand'

export interface BadgeProps {
  status?: BadgeStatus
  children?: string
}

export function Badge({ status = 'default', children }: BadgeProps) {
  return (
    <BadgeFrame status={status}>
      <BadgeText status={status}>{children}</BadgeText>
    </BadgeFrame>
  )
}
