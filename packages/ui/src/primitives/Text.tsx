import { styled, Text as TamaguiText } from '@tamagui/core'

const Base = styled(TamaguiText, {
  fontFamily: '$body',
  color: '$color',
})

export const Heading = styled(Base, {
  fontWeight: '700',
  variants: {
    size: {
      sm: { fontSize: '$6', lineHeight: '$6' },
      md: { fontSize: '$8', lineHeight: '$8' },
      lg: { fontSize: '$9', lineHeight: '$9' },
    },
  } as const,
  defaultVariants: {
    size: 'md',
  },
})

export const Body = styled(Base, {
  fontSize: '$5',
  lineHeight: '$6',
  fontWeight: '400',
})

export const Label = styled(Base, {
  fontSize: '$4',
  lineHeight: '$5',
  fontWeight: '600',
})

export const Caption = styled(Base, {
  fontSize: '$3',
  lineHeight: '$4',
  fontWeight: '400',
  color: '$colorHover',
})

export const Mono = styled(Base, {
  fontFamily: '$mono',
  fontSize: '$4',
  lineHeight: '$5',
  fontWeight: '400',
})
