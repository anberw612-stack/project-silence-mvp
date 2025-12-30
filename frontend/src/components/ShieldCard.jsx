/**
 * Shield Card Component
 *
 * A secure glass pane feature card with:
 * - Glassmorphism effect (backdrop-blur + subtle transparency)
 * - Teal border glow on hover (suggesting active protection)
 * - Smooth, heavy Framer Motion animations
 * - Cut-glass aesthetic with ultra-thin borders
 */

import { motion } from 'framer-motion';

// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION VARIANTS
// ═══════════════════════════════════════════════════════════════════════════════

const cardVariants = {
  hidden: {
    opacity: 0,
    y: 30,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.8,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

const iconContainerVariants = {
  rest: {
    scale: 1,
    rotate: 0,
  },
  hover: {
    scale: 1.1,
    rotate: 5,
    transition: {
      duration: 0.4,
      ease: [0.16, 1, 0.3, 1],
    },
  },
};

const glowVariants = {
  rest: {
    opacity: 0,
    scale: 0.8,
  },
  hover: {
    opacity: 1,
    scale: 1,
    transition: {
      duration: 0.4,
      ease: "easeOut",
    },
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// SHIELD CARD COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

const ShieldCard = ({
  icon: Icon,
  title,
  description,
  status = null, // 'active', 'premium', or null
  delay = 0,
}) => {
  return (
    <motion.div
      className="relative group"
      variants={cardVariants}
      initial="hidden"
      whileInView="visible"
      viewport={{ once: true, margin: "-50px" }}
      transition={{ delay }}
    >
      {/* Glow effect on hover - appears behind the card */}
      <motion.div
        className="absolute -inset-1 rounded-2xl bg-gradient-to-r from-accent-teal/20 via-accent-teal/10 to-accent-teal/20 blur-xl"
        variants={glowVariants}
        initial="rest"
        whileHover="hover"
        animate="rest"
      />

      {/* Main Card */}
      <motion.div
        className="relative h-full overflow-hidden rounded-2xl"
        initial="rest"
        whileHover="hover"
        animate="rest"
      >
        {/* Glass background */}
        <div className="absolute inset-0 bg-white/[0.03] backdrop-blur-md" />

        {/* Border - ultra thin with glow on hover */}
        <div className="absolute inset-0 rounded-2xl border border-white/[0.08] group-hover:border-accent-teal/30 transition-colors duration-500" />

        {/* Inner glow gradient */}
        <div className="absolute inset-0 bg-gradient-to-br from-white/[0.05] via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

        {/* Content */}
        <div className="relative p-8 md:p-10">
          {/* Status indicator */}
          {status && (
            <div className="absolute top-6 right-6">
              <div className={`
                flex items-center gap-2 px-3 py-1.5 rounded-full text-xs font-medium tracking-wide uppercase
                ${status === 'active'
                  ? 'bg-accent-teal/10 text-accent-teal border border-accent-teal/20'
                  : 'bg-accent-gold/10 text-accent-gold border border-accent-gold/20'
                }
              `}>
                <div className={`w-1.5 h-1.5 rounded-full ${status === 'active' ? 'bg-accent-teal' : 'bg-accent-gold'} animate-pulse`} />
                {status === 'active' ? 'Active' : 'Premium'}
              </div>
            </div>
          )}

          {/* Icon container with glow */}
          <motion.div
            className="relative mb-8"
            variants={iconContainerVariants}
          >
            {/* Icon glow background */}
            <div className="absolute inset-0 w-16 h-16 rounded-xl bg-accent-teal/20 blur-xl opacity-0 group-hover:opacity-100 transition-opacity duration-500" />

            {/* Icon container */}
            <div className="relative w-16 h-16 rounded-xl bg-gradient-to-br from-accent-teal/20 to-accent-teal/5 border border-accent-teal/20 flex items-center justify-center group-hover:border-accent-teal/40 transition-colors duration-500">
              <Icon className="w-7 h-7 text-accent-teal" strokeWidth={1.5} />
            </div>
          </motion.div>

          {/* Title */}
          <h3 className="font-serif font-semibold text-white mb-4 text-xl md:text-2xl group-hover:text-accent-teal-light transition-colors duration-300">
            {title}
          </h3>

          {/* Description */}
          <p className="text-neutral-400 leading-relaxed text-base">
            {description}
          </p>

          {/* Bottom accent line - appears on hover */}
          <motion.div
            className="absolute bottom-0 left-8 right-8 h-px"
            initial={{ scaleX: 0, opacity: 0 }}
            whileHover={{ scaleX: 1, opacity: 1 }}
            transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            style={{
              background: 'linear-gradient(90deg, transparent, rgba(20, 184, 166, 0.5), transparent)',
            }}
          />
        </div>

        {/* Corner accents - geometric tech aesthetic */}
        <div className="absolute top-4 left-4 w-3 h-3 border-t border-l border-white/10 group-hover:border-accent-teal/40 transition-colors duration-500" />
        <div className="absolute top-4 right-4 w-3 h-3 border-t border-r border-white/10 group-hover:border-accent-teal/40 transition-colors duration-500" />
        <div className="absolute bottom-4 left-4 w-3 h-3 border-b border-l border-white/10 group-hover:border-accent-teal/40 transition-colors duration-500" />
        <div className="absolute bottom-4 right-4 w-3 h-3 border-b border-r border-white/10 group-hover:border-accent-teal/40 transition-colors duration-500" />
      </motion.div>
    </motion.div>
  );
};

export default ShieldCard;
