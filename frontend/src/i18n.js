import { createI18n } from "vue-i18n";
import en from "./locales/en.json";
import de from "./locales/de.json";
import fr from "./locales/fr.json";

const i18n = createI18n({
  legacy: false, // Use Composition API
  globalInjection: true, // Enable $t in templates
  locale: "en", // Default locale
  fallbackLocale: "en",
  messages: {
    en,
    de,
    fr,
  },
});

export default i18n;
