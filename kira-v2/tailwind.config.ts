import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg: {
          primary: "var(--bg-primary)",
          secondary: "var(--bg-secondary)",
        },
        surface: {
          primary: "var(--surface-primary)",
          card: "var(--surface-card)",
          elevated: "var(--surface-elevated)",
        },
        border: {
          primary: "var(--border-primary)",
          soft: "var(--border-soft)",
        },
        text: {
          primary: "var(--text-primary)",
          secondary: "var(--text-secondary)",
          muted: "var(--text-muted)",
          disabled: "var(--text-disabled)",
        },
      },
      borderRadius: {
        md: "12px",
      },
      maxWidth: {
        content: "1280px",
      },
      spacing: {
        section: "48px",
        card: "32px",
      },
    },
  },
  plugins: [],
} satisfies Config;
