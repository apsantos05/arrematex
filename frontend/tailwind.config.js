/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        brand: "#f5a623",
        "brand-light": "#ffc147",
        "bg-deep": "#1a1a2e",
        "bg-surface": "#16213e",
        "bg-elevated": "#1e2d4a",
      },
      fontFamily: {
        sans: ["Barlow", "Inter", "ui-sans-serif", "system-ui"],
      },
    },
  },
  plugins: [],
};
