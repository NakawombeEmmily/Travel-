import type { Config } from "tailwindcss";

export default {
  darkMode: "class",
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Brand orange — defined once as design tokens
        primary: {
          50: "#FFF7ED",
          100: "#FFEDD5",
          200: "#FED7AA",
          300: "#FDBA74",
          400: "#FB923C",
          500: "#F97316", // main
          600: "#EA580C", // hover
          700: "#C2410C", // pressed / text
          800: "#9A3412",
          900: "#7C2D12",
          950: "#431407", // dark text on orange
        },
        surface: {
          light: "#FFFBF7",
          dark: "#1C1917",
        },
        neutral: {
          50: "#FAFAF9",
          100: "#F5F5F4",
          200: "#E7E5E4",
          300: "#D6D3D1",
          400: "#A8A29E",
          500: "#78716C",
          600: "#57534E",
          700: "#44403C",
          800: "#292524",
          900: "#1C1917",
        },
        status: {
          approved: "#16A34A",
          rejected: "#DC2626",
          pending: "#D97706",
          review: "#2563EB",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
} satisfies Config;
