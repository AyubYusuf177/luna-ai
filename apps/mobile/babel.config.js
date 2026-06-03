module.exports = function (api) {
  api.cache(true)
  return {
    presets: ['babel-preset-expo'],
    plugins: [
      [
        '@tamagui/babel-plugin',
        {
          components: ['@tamagui/core'],
          config: '../../packages/tokens/src/index.ts',
          disableExtraction: true,
        },
      ],
    ],
  }
}
