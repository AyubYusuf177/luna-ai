import React from 'react'
import { Stack } from 'expo-router'

export default function OnboardingLayout() {
  return (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: '#0c0a09' },
        animation: 'slide_from_right',
      }}
    />
  )
}
