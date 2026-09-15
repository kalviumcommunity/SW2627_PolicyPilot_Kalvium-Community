/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: [
    "./src/**/*.{js,jsx,ts,tsx}",
    "./src/components/**/*.{js,jsx,ts,tsx}",
    "./app/**/*.{js,jsx,ts,tsx}",
    "./components/**/*.{js,jsx,ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: "#00bfa6",
        secondary: "#f5f7fa",
        "user-msg": "#1e40af",
        "assistant-msg": "#334155",
        "error-bg": "#450a0a",
        "error-border": "#991b1b",
        "error-text": "#fca5a5",
        accent: "#00bfa6",
      },
    },
  },
  plugins: [],
};
