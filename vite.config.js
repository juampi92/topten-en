import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';

const siteUrl =
  (process.env.SITE_URL || 'https://juampi92.github.io/topten-en/').replace(/\/$/, '') + '/';

export default defineConfig({
  plugins: [
    svelte(),
    {
      name: 'inject-site-url',
      transformIndexHtml(html) {
        return html.replaceAll('__SITE_URL__', siteUrl);
      },
    },
  ],
  base: process.env.BASE_PATH || '/',
  build: {
    outDir: 'build',
  },
});
