import type { NextConfig } from 'next';

const securityHeaders = [
  { key: 'X-Frame-Options', value: 'DENY' },
  { key: 'X-Content-Type-Options', value: 'nosniff' },
  { key: 'Referrer-Policy', value: 'strict-origin-when-cross-origin' },
  { key: 'Permissions-Policy', value: 'camera=(self), microphone=(self), geolocation=()' },
];

const nextConfig: NextConfig = {
  output:
    process.env.STANDALONE === 'true' || process.env.DOCKER_BUILD === 'true'
      ? 'standalone'
      : undefined,
  reactStrictMode: true,
  transpilePackages: [
    '@opportunity-os/shared-types',
    '@opportunity-os/api-client',
    '@opportunity-os/design-tokens',
    '@opportunity-os/shared-config',
  ],
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: securityHeaders,
      },
    ];
  },
};

export default nextConfig;
