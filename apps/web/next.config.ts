import type { NextConfig } from 'next';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  transpilePackages: [
    '@opportunity-os/shared-types',
    '@opportunity-os/api-client',
    '@opportunity-os/design-tokens',
    '@opportunity-os/shared-config',
  ],
};

export default nextConfig;
