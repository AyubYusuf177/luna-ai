'use client'
import React from 'react'
import { YStack, Heading, Body, Caption } from '@luna/ui'

export default function TripsPage() {
  return (
    <YStack gap="$4" maxWidth={720}>
      <YStack gap="$1">
        <Heading size="md">Trips</Heading>
        <Caption color="$colorHover">Upcoming, active, and past trips.</Caption>
      </YStack>
      <Body color="$colorHover">
        No trips yet. Text Luna to start planning your first trip — she'll build the itinerary and surface it here.
      </Body>
    </YStack>
  )
}
