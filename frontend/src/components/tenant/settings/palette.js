// Palette helpers for the chat widget: friendly names for the base colours
// and a WCAG contrast check so people notice unreadable combinations.
import { useI18n } from 'vue-i18n';

export const BASE_COLOR_IDS = ['c_primary', 'c_secondary', 'c_black', 'c_white'];

export function usePaletteNames() {
  const { t } = useI18n();
  const nameOf = (c) => (BASE_COLOR_IDS.includes(c.id) ? t(`configure.colors.base.${c.id}`) : c.name);
  return { nameOf };
}

function luminance(hex) {
  const m = /^#?([0-9a-f]{6})$/i.exec(hex || '');
  if (!m) return 1;
  const n = parseInt(m[1], 16);
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255]
    .map((v) => { v /= 255; return v <= 0.03928 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4; })
    .reduce((sum, v, i) => sum + v * [0.2126, 0.7152, 0.0722][i], 0);
}

export function contrast(a, b) {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x);
  return (hi + 0.05) / (lo + 0.05);
}

// Black or white, whichever reads better on the given colour
export const readableOn = (hex) => (contrast(hex, '#000000') >= contrast(hex, '#FFFFFF') ? '#000000' : '#FFFFFF');

// Starter chip colours live at the top level of widget_config, the rest in component_styles
const TOP_LEVEL_STYLES = ['starter_background_color', 'starter_text_color'];
export const getStyle = (cfg, field) => (TOP_LEVEL_STYLES.includes(field) ? cfg[field] : cfg.component_styles?.[field]);
export function setStyle(cfg, field, colorId) {
  if (TOP_LEVEL_STYLES.includes(field)) cfg[field] = colorId;
  else cfg.component_styles[field] = colorId;
}
export const colorOf = (cfg, id) => cfg.color_palette.find((c) => c.id === id)?.value || id;

// Every style setting that points at a palette colour
const styleFields = (cfg) => [...TOP_LEVEL_STYLES, ...Object.keys(cfg.component_styles || {})];

function rgb(hex) {
  const n = parseInt((hex || '').replace('#', ''), 16) || 0;
  return [(n >> 16) & 255, (n >> 8) & 255, n & 255];
}

// Removes a colour; whatever used it takes the closest remaining one
export function removeColor(cfg, id) {
  const gone = cfg.color_palette.find((c) => c.id === id);
  if (!gone) return;
  cfg.color_palette = cfg.color_palette.filter((c) => c.id !== id);
  const [r, g, b] = rgb(gone.value);
  const nearest = cfg.color_palette.reduce((best, c) => {
    const [r2, g2, b2] = rgb(c.value);
    const d = (r - r2) ** 2 + (g - g2) ** 2 + (b - b2) ** 2;
    return d < best.d ? { id: c.id, d } : best;
  }, { id: 'c_primary', d: Infinity }).id;
  for (const f of styleFields(cfg)) if (getStyle(cfg, f) === id) setStyle(cfg, f, nearest);
}
