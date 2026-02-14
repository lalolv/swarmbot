/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{vue,js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Dark theme base
        void: "#050508",
        abyss: "#0a0a0f",
        depth: "#12121a",
        surface: "#1a1a25",
        panel: "#252532",
        
        // Neon accents
        neon: {
          cyan: "#00f0ff",
          purple: "#b829ff",
          pink: "#ff2d95",
          green: "#00ff88",
          yellow: "#ffee00",
          orange: "#ff6b35",
        },
        
        // Semantic
        primary: "#00f0ff",
        secondary: "#b829ff",
        success: "#00ff88",
        warning: "#ffee00",
        danger: "#ff2d95",
        info: "#00f0ff",
      },
      
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },
      
      boxShadow: {
        'neon-cyan': '0 0 20px rgba(0, 240, 255, 0.3), 0 0 40px rgba(0, 240, 255, 0.1)',
        'neon-purple': '0 0 20px rgba(184, 41, 255, 0.3), 0 0 40px rgba(184, 41, 255, 0.1)',
        'neon-pink': '0 0 20px rgba(255, 45, 149, 0.3), 0 0 40px rgba(255, 45, 149, 0.1)',
        'glass': '0 8px 32px 0 rgba(0, 0, 0, 0.37)',
        'glow': '0 0 60px rgba(0, 240, 255, 0.15)',
      },
      
      backdropBlur: {
        'xs': '2px',
      },
      
      keyframes: {
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'pulse-glow': {
          '0%, 100%': { opacity: '1', boxShadow: '0 0 20px rgba(0, 240, 255, 0.5)' },
          '50%': { opacity: '0.8', boxShadow: '0 0 40px rgba(0, 240, 255, 0.8)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition: '200% 0' },
        },
        'fade-in': {
          '0%': { opacity: '0', transform: 'scale(0.95)' },
          '100%': { opacity: '1', transform: 'scale(1)' },
        },
        'slide-down': {
          '0%': { opacity: '0', transform: 'translateY(-10px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'grid-flow': {
          '0%': { transform: 'translateY(0)' },
          '100%': { transform: 'translateY(40px)' },
        },
      },
      
      animation: {
        'float': 'float 6s ease-in-out infinite',
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'shimmer': 'shimmer 3s linear infinite',
        'fade-in': 'fade-in 0.3s ease-out',
        'slide-down': 'slide-down 0.2s ease-out',
        'grid-flow': 'grid-flow 20s linear infinite',
      },
      
      fontFamily: {
        display: ['Space Grotesk', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
        body: ['Inter', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
