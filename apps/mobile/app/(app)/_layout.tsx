import React from 'react'
import { Tabs } from 'expo-router'

export default function AppLayout() {
  return (
    <Tabs
      screenOptions={{
        headerShown: false,
        tabBarStyle: {
          backgroundColor: '#1c1917',
          borderTopColor: '#292524',
        },
        tabBarActiveTintColor: '#9333ea',
        tabBarInactiveTintColor: '#57534e',
        tabBarLabelStyle: { fontSize: 11, fontWeight: '500' },
      }}
    >
      <Tabs.Screen name="index" options={{ title: 'Home' }} />
      <Tabs.Screen name="trips" options={{ title: 'Trips' }} />
      <Tabs.Screen name="settings" options={{ title: 'Settings' }} />
      {/* Accessible via router.push but hidden from tab bar */}
      <Tabs.Screen name="integrations" options={{ href: null }} />
      <Tabs.Screen name="channels" options={{ href: null }} />
      <Tabs.Screen name="actions" options={{ href: null }} />
      <Tabs.Screen name="vault" options={{ href: null }} />
      <Tabs.Screen name="text" options={{ href: null }} />
    </Tabs>
  )
}
