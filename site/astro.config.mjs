import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import astroLit from '@semantic-ui/astro-lit';
import mdx from '@astrojs/mdx';
import { FontaineTransform } from 'fontaine';

export default defineConfig({
  site: 'https://daggerobelus.com',
  trailingSlash: 'always',
  server: {
    host: true,
  },
  integrations: [astroLit(), mdx()],
  vite: {
    plugins: [
      tailwindcss(),
      FontaineTransform.vite({
        fallbacks: ['Georgia', 'Times New Roman', 'serif'],
      }),
    ],
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
