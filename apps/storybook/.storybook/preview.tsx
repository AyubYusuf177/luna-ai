import React from 'react'
import type { Preview, Decorator } from '@storybook/react'
import { TamaguiProvider } from '@tamagui/core'
import config from '@luna/tokens'

const withTamagui: Decorator = (Story, context) => {
  const scheme = context.globals['theme'] === 'dark' ? 'dark' : 'light'
  return (
    <TamaguiProvider config={config} defaultTheme={scheme}>
      <Story />
    </TamaguiProvider>
  )
}

const preview: Preview = {
  decorators: [withTamagui],

  globalTypes: {
    theme: {
      description: 'Color scheme',
      defaultValue: 'light',
      toolbar: {
        title: 'Theme',
        icon: 'circlehollow',
        items: [
          { value: 'light', title: 'Light', icon: 'sun' },
          { value: 'dark',  title: 'Dark',  icon: 'moon' },
        ],
        dynamicTitle: true,
      },
    },
  },

  parameters: {
    controls: { expanded: true },
    backgrounds: { disable: true },
    layout: 'centered',
  },
}

export default preview
