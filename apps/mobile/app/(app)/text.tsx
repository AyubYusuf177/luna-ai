import React from 'react'
import { YStack, Heading, Body, Caption, Button, Card, Badge } from '@luna/ui'

export default function TextLunaScreen() {
  return (
    <YStack flex={1} backgroundColor="$background" padding="$6" paddingTop="$14" gap="$5">
      <YStack gap="$1">
        <Heading size="md">Text Luna</Heading>
        <Caption color="$colorHover">Luna lives in your messages.</Caption>
      </YStack>

      <Card>
        <Body fontWeight="600" marginBottom="$1">Luna's number</Body>
        <Body color="$brand" fontFamily="$mono">+1 (628) 432-1017</Body>
        <Caption color="$colorHover" marginTop="$2">
          Send any travel question or request directly to this number.
        </Caption>
      </Card>

      <YStack gap="$3">
        <Body color="$colorHover">Try asking Luna:</Body>
        {[
          '"Find me a flight to Tokyo in October under £600"',
          '"What\'s the weather in Lisbon next week?"',
          '"Remind me to check in for my Rome flight on Friday"',
        ].map(prompt => (
          <Card key={prompt}>
            <Caption color="$colorHover" fontFamily="$mono">{prompt}</Caption>
          </Card>
        ))}
      </YStack>

      <Button variant="secondary" size="lg">
        Open in Messages
      </Button>
    </YStack>
  )
}
