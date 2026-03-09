/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
        },
        delta: {
          novel: '#10b981',    // green
          related: '#f59e0b',  // amber
          duplicate: '#6b7280', // gray
        }
      },
    },
  },
  plugins: [],
}
