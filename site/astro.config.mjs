import { defineConfig } from 'astro/config';
import tailwind from '@astrojs/tailwind';

export default defineConfig({
  site: 'https://daggerobelus.com',
  trailingSlash: 'always',
  integrations: [tailwind()],
  vite: {
    resolve: {
      preserveSymlinks: true,
    },
    server: {
      fs: {
        allow: ['..'],
      },
    },
  },
});
