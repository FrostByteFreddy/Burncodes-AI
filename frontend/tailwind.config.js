import { theme } from './src/theme';

/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        ...theme.colors,
      },
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};