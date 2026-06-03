import React, { useState } from 'react'
import { XStack, YStack } from './Stack'
import { Label, Caption } from './Text'

export interface InputProps {
  label?: string
  placeholder?: string
  helperText?: string
  errorText?: string
  value?: string
  defaultValue?: string
  disabled?: boolean
  onChange?: (value: string) => void
}

export function Input({
  label,
  placeholder,
  helperText,
  errorText,
  value,
  defaultValue,
  disabled = false,
  onChange,
}: InputProps) {
  const [focused, setFocused] = useState(false)
  const hasError = Boolean(errorText)

  return (
    <YStack gap="$1" opacity={disabled ? 0.5 : 1}>
      {label && <Label>{label}</Label>}

      <XStack
        borderWidth={1}
        borderRadius="$2"
        paddingHorizontal="$3"
        paddingVertical="$2"
        borderColor={hasError ? '$error' : focused ? '$borderColorFocus' : '$borderColor'}
        backgroundColor="$background"
        alignItems="center"
      >
        <input
          value={value}
          defaultValue={defaultValue}
          placeholder={placeholder}
          disabled={disabled}
          onFocus={() => setFocused(true)}
          onBlur={() => setFocused(false)}
          onChange={e => onChange?.(e.target.value)}
          style={{
            flex: 1,
            width: '100%',
            background: 'transparent',
            border: 'none',
            outline: 'none',
            fontSize: 14,
            lineHeight: '20px',
            color: 'inherit',
            fontFamily: 'inherit',
          }}
        />
      </XStack>

      {(errorText || helperText) && (
        <Caption color={hasError ? '$error' : '$colorHover'}>
          {errorText ?? helperText}
        </Caption>
      )}
    </YStack>
  )
}
