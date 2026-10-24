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
