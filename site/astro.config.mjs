import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import astroLit from '@semantic-ui/astro-lit';
import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://daggerobelus.com',
  trailingSlash: 'always',
  integrations: [astroLit(), mdx()],
  vite: {
    plugins: [tailwindcss()],
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
