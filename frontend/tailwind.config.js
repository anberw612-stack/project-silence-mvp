/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      // ═══════════════════════════════════════════════════════════════════════════
      // THE VAULT COLOR PALETTE
      // A sophisticated dark theme conveying trust, security, and luxury
      // ═══════════════════════════════════════════════════════════════════════════
      colors: {
        // Primary Backgrounds - Deep, rich blacks with subtle undertones
        vault: {
          obsidian: '#0B0C10',      // Primary background - warm black
          midnight: '#0F172A',      // Secondary background - cool deep blue
          charcoal: '#1C1C1E',      // Card backgrounds
          slate: '#1E293B',         // Elevated surfaces
        },
        // Accent Colors - Tech & Premium indicators
        accent: {
          teal: '#14B8A6',          // Electric Teal - tech elements, links, active states
          'teal-glow': '#0D9488',   // Darker teal for glows
          'teal-light': '#2DD4BF',  // Light teal for highlights
          gold: '#F59E0B',          // Champagne Gold - premium status, warnings
          'gold-light': '#FBBF24',  // Light gold for highlights
        },
        // Neutral scale - for text and subtle elements
        neutral: {
          50: '#FAFAFA',
          100: '#F4F4F5',
          200: '#E4E4E7',
          300: '#D4D4D8',
          400: '#A1A1AA',
          500: '#71717A',
          600: '#52525B',
          700: '#3F3F46',
          800: '#27272A',
          900: '#18181B',
        }
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // TYPOGRAPHY - Elegant serif for headings, clean sans for body
      // ═══════════════════════════════════════════════════════════════════════════
      fontFamily: {
        // Elegant serif for headings - conveys luxury and timelessness
        serif: ['Playfair Display', 'Cinzel', 'Georgia', 'serif'],
        // Modern sans-serif for body - clean and readable
        sans: ['Inter', 'Geist', 'system-ui', '-apple-system', 'sans-serif'],
        // Monospace for technical elements
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // SPACING - Luxury breathes. 2x padding for generous whitespace
      // ═══════════════════════════════════════════════════════════════════════════
      spacing: {
        '18': '4.5rem',
        '22': '5.5rem',
        '26': '6.5rem',
        '30': '7.5rem',
        '34': '8.5rem',
        '38': '9.5rem',
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // ANIMATIONS - Smooth, heavy, sophisticated motion
      // ═══════════════════════════════════════════════════════════════════════════
      animation: {
        'aurora': 'aurora 15s ease infinite',
        'float': 'float 6s ease-in-out infinite',
        'glow-pulse': 'glow-pulse 3s ease-in-out infinite',
        'fade-in-up': 'fade-in-up 0.8s ease-out forwards',
        'border-glow': 'border-glow 2s ease-in-out infinite',
      },
      keyframes: {
        aurora: {
          '0%, 100%': {
            backgroundPosition: '0% 50%',
            backgroundSize: '200% 200%'
          },
          '50%': {
            backgroundPosition: '100% 50%',
            backgroundSize: '200% 200%'
          },
        },
        float: {
          '0%, 100%': { transform: 'translateY(0)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'glow-pulse': {
          '0%, 100%': { opacity: '0.4' },
          '50%': { opacity: '0.8' },
        },
        'fade-in-up': {
          '0%': {
            opacity: '0',
            transform: 'translateY(20px)'
          },
          '100%': {
            opacity: '1',
            transform: 'translateY(0)'
          },
        },
        'border-glow': {
          '0%, 100%': {
            boxShadow: '0 0 5px rgba(20, 184, 166, 0.3), inset 0 0 5px rgba(20, 184, 166, 0.1)'
          },
          '50%': {
            boxShadow: '0 0 20px rgba(20, 184, 166, 0.5), inset 0 0 10px rgba(20, 184, 166, 0.2)'
          },
        },
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // BACKDROP & BLUR - Glassmorphism effects
      // ═══════════════════════════════════════════════════════════════════════════
      backdropBlur: {
        xs: '2px',
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // BOX SHADOWS - Subtle glows and depth
      // ═══════════════════════════════════════════════════════════════════════════
      boxShadow: {
        'glow-teal': '0 0 30px rgba(20, 184, 166, 0.3)',
        'glow-teal-sm': '0 0 15px rgba(20, 184, 166, 0.2)',
        'glow-gold': '0 0 30px rgba(245, 158, 11, 0.3)',
        'inner-glow': 'inset 0 1px 0 0 rgba(255, 255, 255, 0.05)',
        'glass': '0 8px 32px rgba(0, 0, 0, 0.4)',
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // GRADIENTS - Aurora mesh backgrounds
      // ═══════════════════════════════════════════════════════════════════════════
      backgroundImage: {
        'aurora-mesh': 'radial-gradient(ellipse at 20% 0%, rgba(20, 184, 166, 0.15) 0%, transparent 50%), radial-gradient(ellipse at 80% 0%, rgba(245, 158, 11, 0.1) 0%, transparent 50%), radial-gradient(ellipse at 50% 100%, rgba(20, 184, 166, 0.1) 0%, transparent 50%)',
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'gradient-conic': 'conic-gradient(from 180deg at 50% 50%, var(--tw-gradient-stops))',
      },

      // ═══════════════════════════════════════════════════════════════════════════
      // BORDER RADIUS - Soft, modern curves
      // ═══════════════════════════════════════════════════════════════════════════
      borderRadius: {
        '4xl': '2rem',
        '5xl': '2.5rem',
      },
    },
  },
  plugins: [],
}
