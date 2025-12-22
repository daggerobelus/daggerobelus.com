/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      colors: {
        cream: '#fff7f4',
        ink: '#121212',
      },
      fontFamily: {
        serif: ['Georgia', 'Times New Roman', 'serif'],
        mono: ['SF Mono', 'Monaco', 'monospace'],
      },
      maxWidth: {
        'content': '72rem',
      },
    },
  },
  plugins: [],
};
