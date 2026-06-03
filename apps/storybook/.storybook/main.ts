import type { StorybookConfig } from '@storybook/react-vite'

const config: StorybookConfig = {
  stories: ['../../../packages/ui/stories/**/*.stories.@(ts|tsx)'],

  addons: [
    '@storybook/addon-essentials',
    '@storybook/addon-themes',
  ],

  framework: {
    name: '@storybook/react-vite',
    options: {},
  },

  async viteFinal(config) {
    const { tamaguiPlugin } = await import('@tamagui/vite-plugin')

    return {
      ...config,
      plugins: [
        ...(config.plugins ?? []),
        tamaguiPlugin({
          components: ['@tamagui/core'],
          config: '../../../packages/tokens/src/index.ts',
          disableExtraction: true,
        }),
      ],
      define: {
        ...config.define,
        'process.env.TAMAGUI_TARGET': '"web"',
        __DEV__: JSON.stringify(false),
      },
    }
  },
}

export default config
