import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import astroLit from '@semantic-ui/astro-lit';
import mdx from '@astrojs/mdx';
import { FontaineTransform } from 'fontaine';

export default defineConfig({
  site: 'https://www.daggerobelus.com',
  trailingSlash: 'always',
  redirects: {
    '/contact': '/about/#the-author',
    '/contact/': '/about/#the-author',
  },
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
