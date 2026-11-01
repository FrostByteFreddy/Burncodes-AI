import type { Locale } from '@/site';
import de from './de';
import fr from './fr';
import en from './en';

export type Content = typeof de;
export const content: Record<Locale, Content> = { de, fr, en };
