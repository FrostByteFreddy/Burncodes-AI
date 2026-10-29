// Swiss number and money formatting, as the design system specifies:
// apostrophe thousands (1’375), "CHF 18.40", a real minus sign.
export function formatNumber(n, decimals = 0) {
  const value = Number(n) || 0;
  const [int, frac] = Math.abs(value).toFixed(decimals).split('.');
  const grouped = int.replace(/\B(?=(\d{3})+(?!\d))/g, '’');
  return (value < 0 ? '−' : '') + (frac ? `${grouped}.${frac}` : grouped);
}

export const formatCHF = (n) => `CHF ${formatNumber(n, 2)}`;
