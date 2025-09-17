/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        'brand-black': '#000000',
        'brand-white': '#FFFFFF',
      },
      backgroundImage: {
        'accent-gradient': 'linear-gradient(145deg, #FF2095 5%, #2038D8 55%, #00AEE4 93%)',
      }
    },
  },
  plugins: [
    require('@tailwindcss/typography'),
  ],
};