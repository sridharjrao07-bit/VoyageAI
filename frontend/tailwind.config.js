/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        sage: {
          50: '#f4f6ef',
          100: '#e8ecde',
          200: '#d1d9be',
          300: '#b3c094',
          400: '#8a9a5b',
          500: '#6b7a42',
          600: '#556233',
          700: '#3f4a27',
          800: '#2d3520',
          900: '#1e2315',
        },
        terracotta: {
          400: '#c17f59',
          500: '#a86b48',
          600: '#8f5b3d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        serif: ['Lora', 'serif'],
      },
    },
  },
  plugins: [],
}
