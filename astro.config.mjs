// @ts-check
import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';

export default defineConfig({
  site: 'https://interieurguy.nl',
  trailingSlash: 'always',
  compressHTML: true,
  integrations: [mdx()],
});
