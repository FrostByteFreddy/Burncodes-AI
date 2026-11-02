// Facts about the company and prices, in one place. Empty legal fields show as
// a visible gap on /impressum and /datenschutz until they are filled in.
export const site = {
  url: 'https://ai.burn.codes',
  dashboard: '/dashboard/',
  signup: '/dashboard/signup',
  legal: {
    company: '',
    address: '',
    email: '',
    uid: '',
    hosting: '',
    retention: '',
  },
  // CHF. Rates per 1M tokens as in backend/shared/ai_models.py; keep in sync.
  price: {
    minTopUp: 5,
    // Median of real charges: 0.087 (84 answers, November 2026)
    answerRappen: 10,
    rates: {
      answer: { input: 8, output: 17.5 },
      learnLite: { input: 1, output: 6 },
      learnArgon: { input: 8, output: 40 },
      learnArgonFromDec: { input: 16, output: 80 },
      embed: 0.8,
    },
  },
};

export const LOCALES = ['de', 'fr', 'en'] as const;
export type Locale = (typeof LOCALES)[number];

// Each page exists per language: /preise/, /fr/preise/, /en/preise/
export const localePath = (lang: Locale, path = '/') => (lang === 'de' ? path : `/${lang}${path}`);
export const langPaths = () => [
  { params: { lang: undefined }, props: { lang: 'de' as Locale } },
  { params: { lang: 'fr' }, props: { lang: 'fr' as Locale } },
  { params: { lang: 'en' }, props: { lang: 'en' as Locale } },
];
