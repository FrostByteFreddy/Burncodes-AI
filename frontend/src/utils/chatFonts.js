// Fonts the chat widget can use. All are bundled from @fontsource, so they're
// served from our own domain (no requests to Google), and each loads only when
// a chatbot uses it.
const SANS = 'system-ui, -apple-system, "Segoe UI", Roboto, sans-serif';
const SERIF = 'Georgia, "Times New Roman", serif';

export const DEFAULT_FONT = 'atkinson';

export const CHAT_FONTS = {
  atkinson:     { name: 'Atkinson Hyperlegible', stack: `"Atkinson Hyperlegible Next", ${SANS}`,
    load: () => Promise.all([import('@fontsource/atkinson-hyperlegible-next/400.css'), import('@fontsource/atkinson-hyperlegible-next/600.css'), import('@fontsource/atkinson-hyperlegible-next/700.css')]) },
  inter:        { name: 'Inter', stack: `"Inter", ${SANS}`,
    load: () => Promise.all([import('@fontsource/inter/400.css'), import('@fontsource/inter/600.css'), import('@fontsource/inter/700.css')]) },
  roboto:       { name: 'Roboto', stack: `"Roboto", ${SANS}`,
    load: () => Promise.all([import('@fontsource/roboto/400.css'), import('@fontsource/roboto/600.css'), import('@fontsource/roboto/700.css')]) },
  open_sans:    { name: 'Open Sans', stack: `"Open Sans", ${SANS}`,
    load: () => Promise.all([import('@fontsource/open-sans/400.css'), import('@fontsource/open-sans/600.css'), import('@fontsource/open-sans/700.css')]) },
  lato:         { name: 'Lato', stack: `"Lato", ${SANS}`,
    load: () => Promise.all([import('@fontsource/lato/400.css'), import('@fontsource/lato/700.css')]) },
  source_sans:  { name: 'Source Sans 3', stack: `"Source Sans 3", ${SANS}`,
    load: () => Promise.all([import('@fontsource/source-sans-3/400.css'), import('@fontsource/source-sans-3/600.css'), import('@fontsource/source-sans-3/700.css')]) },
  nunito:       { name: 'Nunito', stack: `"Nunito", ${SANS}`,
    load: () => Promise.all([import('@fontsource/nunito/400.css'), import('@fontsource/nunito/600.css'), import('@fontsource/nunito/700.css')]) },
  montserrat:   { name: 'Montserrat', stack: `"Montserrat", ${SANS}`,
    load: () => Promise.all([import('@fontsource/montserrat/400.css'), import('@fontsource/montserrat/600.css'), import('@fontsource/montserrat/700.css')]) },
  poppins:      { name: 'Poppins', stack: `"Poppins", ${SANS}`,
    load: () => Promise.all([import('@fontsource/poppins/400.css'), import('@fontsource/poppins/600.css'), import('@fontsource/poppins/700.css')]) },
  merriweather: { name: 'Merriweather', stack: `"Merriweather", ${SERIF}`,
    load: () => Promise.all([import('@fontsource/merriweather/400.css'), import('@fontsource/merriweather/700.css')]) },
  lora:         { name: 'Lora', stack: `"Lora", ${SERIF}`,
    load: () => Promise.all([import('@fontsource/lora/400.css'), import('@fontsource/lora/600.css'), import('@fontsource/lora/700.css')]) },
  system:       { name: null, stack: SANS, load: () => Promise.resolve() },
};

const fontOf = (key) => CHAT_FONTS[key] || CHAT_FONTS[DEFAULT_FONT];

// Starts loading the font's files (once) and returns its CSS font-family
const loading = {};
export function loadChatFont(key) {
  const font = fontOf(key);
  const k = CHAT_FONTS[key] ? key : DEFAULT_FONT;
  loading[k] ||= font.load().catch(() => { delete loading[k]; });
  return font.stack;
}
