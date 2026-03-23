/** @type {import('tailwindcss').Config} */
export default {
  content: [
    './index.html',
    './src/**/*.{vue,js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      boxShadow: {
        soft: '0 10px 40px -18px rgba(15, 23, 42, 0.25)',
      },
    },
  },
  plugins: [],
}
