/**
 * Hero Section Component
 *
 * A commanding, centered hero section with:
 * - Animated aurora gradient mesh background (encryption data flow aesthetic)
 * - Elegant serif typography for headlines
 * - Ghost buttons and primary CTA
 * - Smooth, heavy Framer Motion animations
 */

import { motion } from 'framer-motion';
import { Shield, Lock, Sparkles } from 'lucide-react';
import GhostButton from './GhostButton';

// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION VARIANTS - Heavy, smooth, sophisticated motion
// ═══════════════════════════════════════════════════════════════════════════════

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.15,
      delayChildren: 0.3,
    },
  },
};

const itemVariants = {
  hidden: {
    opacity: 0,
    y: 30,
  },
  visible: {
    opacity: 1,
    y: 0,
    transition: {
      duration: 0.8,
      ease: [0.16, 1, 0.3, 1], // Luxury easing - smooth and heavy
    },
  },
};

const floatingVariants = {
  animate: {
    y: [-5, 5, -5],
    transition: {
      duration: 6,
      repeat: Infinity,
      ease: "easeInOut",
    },
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// AURORA MESH BACKGROUND - Abstract encryption data flow
// ═══════════════════════════════════════════════════════════════════════════════

const AuroraMesh = () => (
  <div className="absolute inset-0 overflow-hidden">
    {/* Primary teal aurora - top left */}
    <motion.div
      className="absolute -top-1/4 -left-1/4 w-[800px] h-[800px] rounded-full"
      style={{
        background: 'radial-gradient(circle, rgba(20, 184, 166, 0.15) 0%, transparent 70%)',
        filter: 'blur(80px)',
      }}
      animate={{
        x: [0, 100, 0],
        y: [0, 50, 0],
        scale: [1, 1.1, 1],
      }}
      transition={{
        duration: 20,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />

    {/* Gold aurora - top right */}
    <motion.div
      className="absolute -top-1/4 -right-1/4 w-[600px] h-[600px] rounded-full"
      style={{
        background: 'radial-gradient(circle, rgba(245, 158, 11, 0.08) 0%, transparent 70%)',
        filter: 'blur(80px)',
      }}
      animate={{
        x: [0, -80, 0],
        y: [0, 80, 0],
        scale: [1, 1.2, 1],
      }}
      transition={{
        duration: 25,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />

    {/* Secondary teal aurora - bottom */}
    <motion.div
      className="absolute -bottom-1/4 left-1/3 w-[700px] h-[700px] rounded-full"
      style={{
        background: 'radial-gradient(circle, rgba(20, 184, 166, 0.1) 0%, transparent 70%)',
        filter: 'blur(100px)',
      }}
      animate={{
        x: [0, 60, 0],
        y: [0, -40, 0],
        scale: [1, 1.15, 1],
      }}
      transition={{
        duration: 18,
        repeat: Infinity,
        ease: "easeInOut",
      }}
    />

    {/* Encryption data particles */}
    <div className="absolute inset-0">
      {[...Array(20)].map((_, i) => (
        <motion.div
          key={i}
          className="absolute w-1 h-1 bg-accent-teal/30 rounded-full"
          style={{
            left: `${Math.random() * 100}%`,
            top: `${Math.random() * 100}%`,
          }}
          animate={{
            opacity: [0, 0.6, 0],
            scale: [0, 1, 0],
            y: [0, -100],
          }}
          transition={{
            duration: 4 + Math.random() * 4,
            repeat: Infinity,
            delay: Math.random() * 5,
            ease: "easeOut",
          }}
        />
      ))}
    </div>

    {/* Grid overlay - tech aesthetic */}
    <div
      className="absolute inset-0 opacity-[0.02]"
      style={{
        backgroundImage: `
          linear-gradient(rgba(20, 184, 166, 0.5) 1px, transparent 1px),
          linear-gradient(90deg, rgba(20, 184, 166, 0.5) 1px, transparent 1px)
        `,
        backgroundSize: '100px 100px',
      }}
    />
  </div>
);

// ═══════════════════════════════════════════════════════════════════════════════
// HERO COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

const Hero = () => {
  return (
    <section className="relative min-h-screen flex items-center justify-center overflow-hidden bg-vault-obsidian">
      {/* Aurora Mesh Background */}
      <AuroraMesh />

      {/* Gradient overlay for depth */}
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-vault-obsidian/50 to-vault-obsidian" />

      {/* Content Container */}
      <motion.div
        className="relative z-10 section-container text-center"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Trust Badge */}
        <motion.div
          variants={itemVariants}
          className="inline-flex items-center gap-3 px-5 py-2.5 mb-10 rounded-full border border-white/10 bg-white/[0.03] backdrop-blur-sm"
        >
          <motion.div
            variants={floatingVariants}
            animate="animate"
          >
            <Shield className="w-4 h-4 text-accent-teal" />
          </motion.div>
          <span className="text-sm font-medium text-neutral-300 tracking-wide">
            Enterprise-Grade Security
          </span>
          <div className="w-2 h-2 rounded-full bg-accent-teal animate-pulse" />
        </motion.div>

        {/* Main Headline - Elegant Serif */}
        <motion.h1
          variants={itemVariants}
          className="font-serif font-semibold text-white mb-8 leading-[1.1]"
        >
          <span className="block">Protect Your</span>
          <span className="block text-gradient">
            Digital Legacy
          </span>
        </motion.h1>

        {/* Subheadline */}
        <motion.p
          variants={itemVariants}
          className="max-w-2xl mx-auto text-lg md:text-xl text-neutral-400 mb-14 leading-relaxed font-light"
        >
          Advanced AI-powered privacy protection that shields your conversations
          from unauthorized access. Your data, encrypted and invisible.
        </motion.p>

        {/* CTA Buttons */}
        <motion.div
          variants={itemVariants}
          className="flex flex-col sm:flex-row items-center justify-center gap-5"
        >
          {/* Primary CTA */}
          <motion.button
            className="btn-primary group"
            whileHover={{ scale: 1.02 }}
            whileTap={{ scale: 0.98 }}
            transition={{ duration: 0.2 }}
          >
            <Lock className="w-4 h-4 mr-3 group-hover:rotate-12 transition-transform duration-300" />
            Start Protection
          </motion.button>

          {/* Ghost Button */}
          <GhostButton icon={Sparkles}>
            View Demo
          </GhostButton>
        </motion.div>

        {/* Stats Row */}
        <motion.div
          variants={itemVariants}
          className="mt-20 pt-12 border-t border-white/5"
        >
          <div className="flex flex-wrap justify-center gap-12 md:gap-20">
            {[
              { value: '256-bit', label: 'Encryption' },
              { value: '99.9%', label: 'Uptime' },
              { value: '0', label: 'Data Breaches' },
            ].map((stat, index) => (
              <motion.div
                key={stat.label}
                className="text-center"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  delay: 1.2 + index * 0.1,
                  duration: 0.6,
                  ease: [0.16, 1, 0.3, 1],
                }}
              >
                <div className="text-3xl md:text-4xl font-serif font-semibold text-white mb-2">
                  {stat.value}
                </div>
                <div className="text-sm text-neutral-500 uppercase tracking-widest">
                  {stat.label}
                </div>
              </motion.div>
            ))}
          </div>
        </motion.div>
      </motion.div>

      {/* Bottom fade gradient */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-vault-obsidian to-transparent" />
    </section>
  );
};

export default Hero;
