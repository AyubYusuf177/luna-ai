import React, { useEffect, useState } from 'react'
import { Redirect } from 'expo-router'
import AsyncStorage from '@react-native-async-storage/async-storage'
import { YStack } from '@luna/ui'

const ONBOARDING_KEY = 'luna:onboarding_complete'

export default function Index() {
  const [target, setTarget] = useState<string | null>(null)

  useEffect(() => {
    AsyncStorage.getItem(ONBOARDING_KEY).then(val => {
      setTarget(val === 'true' ? '/(app)/' : '/(onboarding)/splash')
    })
  }, [])

  if (!target) {
    return <YStack flex={1} backgroundColor="$background" />
  }

  return <Redirect href={target as never} />
}
