import type { NextConfig } from 'next'

const nextConfig: NextConfig = {
  transpilePackages: ['@luna/ui', '@luna/tokens', '@tamagui/core'],
}

export default nextConfig
