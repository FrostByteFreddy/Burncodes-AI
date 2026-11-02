import { defineConfig } from 'astro/config';
import vue from '@astrojs/vue';
import sitemap from '@astrojs/sitemap';
import tailwindcss from '@tailwindcss/vite';

// Static HTML for search engines; only interactive parts hydrate in the browser
export default defineConfig({
  site: 'https://ai.burn.codes',
  trailingSlash: 'always',
  devToolbar: { enabled: false },
  integrations: [
    vue(),
    sitemap({
      filter: (page) => !/\/(impressum|datenschutz)\/$/.test(page),
      i18n: { defaultLocale: 'de', locales: { de: 'de-CH', fr: 'fr-CH', en: 'en' } },
    }),
  ],
  vite: { plugins: [tailwindcss()] },
});
