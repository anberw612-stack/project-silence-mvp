/**
 * Ghost Button Component
 *
 * A sophisticated ghost button with:
 * - Thin borders with subtle backdrop filter
 * - No solid primary colors
 * - Teal glow on hover suggesting interaction
 * - Smooth, heavy Framer Motion animations
 */

import { motion } from 'framer-motion';

// ═══════════════════════════════════════════════════════════════════════════════
// GHOST BUTTON COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

const GhostButton = ({
  children,
  icon: Icon = null,
  onClick,
  size = 'default', // 'small', 'default', 'large'
  variant = 'default', // 'default', 'teal', 'gold'
  className = '',
  ...props
}) => {
  // Size variants
  const sizeClasses = {
    small: 'px-5 py-2.5 text-xs',
    default: 'px-8 py-4 text-sm',
    large: 'px-10 py-5 text-base',
  };

  // Color variants for hover states
  const variantClasses = {
    default: 'hover:border-accent-teal/50 hover:text-accent-teal-light hover:shadow-glow-teal-sm',
    teal: 'border-accent-teal/30 text-accent-teal hover:border-accent-teal/60 hover:shadow-glow-teal-sm',
    gold: 'hover:border-accent-gold/50 hover:text-accent-gold-light hover:shadow-glow-gold',
  };

  return (
    <motion.button
      className={`
        relative inline-flex items-center justify-center
        ${sizeClasses[size]}
        font-medium tracking-wide uppercase
        text-neutral-200
        border border-white/10
        rounded-lg
        backdrop-blur-sm bg-white/[0.02]
        transition-all duration-300
        ${variantClasses[variant]}
        focus:outline-none focus:ring-2 focus:ring-accent-teal/30 focus:ring-offset-2 focus:ring-offset-vault-obsidian
        overflow-hidden
        group
        ${className}
      `}
      onClick={onClick}
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      transition={{
        scale: {
          duration: 0.2,
          ease: [0.16, 1, 0.3, 1],
        },
      }}
      {...props}
    >
      {/* Subtle gradient overlay on hover */}
      <motion.div
        className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.02] to-transparent"
        initial={{ x: '-100%', opacity: 0 }}
        whileHover={{ x: '100%', opacity: 1 }}
        transition={{ duration: 0.6, ease: "easeInOut" }}
      />

      {/* Border glow effect */}
      <motion.div
        className="absolute inset-0 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300"
        style={{
          background: 'linear-gradient(135deg, rgba(20, 184, 166, 0.1) 0%, transparent 50%, rgba(20, 184, 166, 0.1) 100%)',
        }}
      />

      {/* Content */}
      <span className="relative flex items-center gap-3">
        {Icon && (
          <Icon
            className="w-4 h-4 transition-transform duration-300 group-hover:rotate-12"
            strokeWidth={1.5}
          />
        )}
        {children}
      </span>

      {/* Corner accents */}
      <span className="absolute top-0 left-0 w-2 h-2 border-t border-l border-white/0 group-hover:border-accent-teal/40 transition-colors duration-300" />
      <span className="absolute top-0 right-0 w-2 h-2 border-t border-r border-white/0 group-hover:border-accent-teal/40 transition-colors duration-300" />
      <span className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-white/0 group-hover:border-accent-teal/40 transition-colors duration-300" />
      <span className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-white/0 group-hover:border-accent-teal/40 transition-colors duration-300" />
    </motion.button>
  );
};

export default GhostButton;
