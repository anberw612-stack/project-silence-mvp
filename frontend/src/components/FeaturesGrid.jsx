/**
 * Features Grid Component
 *
 * A sophisticated grid of Shield Cards showcasing:
 * - Staggered scroll animations
 * - Responsive grid layout with luxury spacing
 * - Section header with elegant typography
 */

import { motion } from 'framer-motion';
import {
  Shield,
  Lock,
  Eye,
  Fingerprint,
  Cpu,
  Globe,
  Zap,
  Key,
} from 'lucide-react';
import ShieldCard from './ShieldCard';

// ═══════════════════════════════════════════════════════════════════════════════
// FEATURES DATA
// ═══════════════════════════════════════════════════════════════════════════════

const features = [
  {
    icon: Shield,
    title: 'AI-Powered Protection',
    description: 'Advanced machine learning algorithms analyze and protect your conversations in real-time, detecting potential threats before they materialize.',
    status: 'active',
  },
  {
    icon: Lock,
    title: 'End-to-End Encryption',
    description: 'Military-grade 256-bit encryption ensures your data remains unreadable to anyone except intended recipients.',
    status: null,
  },
  {
    icon: Eye,
    title: 'Privacy Obfuscation',
    description: 'Intelligent decoy generation creates false trails, making your real data invisible within a sea of plausible alternatives.',
    status: 'premium',
  },
  {
    icon: Fingerprint,
    title: 'Biometric Access',
    description: 'Multi-factor authentication with biometric verification ensures only you can access your protected vault.',
    status: null,
  },
  {
    icon: Cpu,
    title: 'Neural Processing',
    description: 'On-device AI processing means your sensitive data never leaves your secure environment.',
    status: 'active',
  },
  {
    icon: Globe,
    title: 'Global Compliance',
    description: 'Full compliance with GDPR, CCPA, and international privacy regulations across all jurisdictions.',
    status: null,
  },
];

// ═══════════════════════════════════════════════════════════════════════════════
// ANIMATION VARIANTS
// ═══════════════════════════════════════════════════════════════════════════════

const sectionVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
};

const headerVariants = {
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

// ═══════════════════════════════════════════════════════════════════════════════
// FEATURES GRID COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

const FeaturesGrid = () => {
  return (
    <section className="relative bg-vault-midnight py-32 md:py-40 overflow-hidden">
      {/* Background gradient */}
      <div className="absolute inset-0">
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />

        {/* Subtle radial gradient */}
        <div
          className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[1000px] h-[1000px] rounded-full opacity-30"
          style={{
            background: 'radial-gradient(circle, rgba(20, 184, 166, 0.05) 0%, transparent 70%)',
          }}
        />
      </div>

      <motion.div
        className="relative z-10 section-container"
        variants={sectionVariants}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: "-100px" }}
      >
        {/* Section Header */}
        <motion.div
          className="text-center mb-20 md:mb-28"
          variants={headerVariants}
        >
          {/* Eyebrow text */}
          <motion.div
            className="inline-flex items-center gap-3 mb-8"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, ease: [0.16, 1, 0.3, 1] }}
          >
            <div className="h-px w-12 bg-gradient-to-r from-transparent to-accent-teal/50" />
            <span className="text-sm font-medium text-accent-teal tracking-[0.2em] uppercase">
              Security Features
            </span>
            <div className="h-px w-12 bg-gradient-to-l from-transparent to-accent-teal/50" />
          </motion.div>

          {/* Main heading */}
          <motion.h2
            className="font-serif font-semibold text-white mb-6"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.1, ease: [0.16, 1, 0.3, 1] }}
          >
            Uncompromising
            <span className="text-gradient"> Protection</span>
          </motion.h2>

          {/* Subheading */}
          <motion.p
            className="max-w-2xl mx-auto text-lg text-neutral-400 leading-relaxed"
            initial={{ opacity: 0, y: 30 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.8, delay: 0.2, ease: [0.16, 1, 0.3, 1] }}
          >
            Every layer of our platform is engineered to keep your data secure,
            private, and under your complete control.
          </motion.p>
        </motion.div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 lg:gap-10">
          {features.map((feature, index) => (
            <ShieldCard
              key={feature.title}
              icon={feature.icon}
              title={feature.title}
              description={feature.description}
              status={feature.status}
              delay={index * 0.1}
            />
          ))}
        </div>

        {/* Bottom CTA */}
        <motion.div
          className="text-center mt-20 md:mt-28"
          initial={{ opacity: 0, y: 30 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={{ once: true }}
          transition={{ duration: 0.8, delay: 0.6, ease: [0.16, 1, 0.3, 1] }}
        >
          <p className="text-neutral-500 mb-6">
            Need enterprise-grade security for your organization?
          </p>
          <motion.a
            href="#contact"
            className="inline-flex items-center gap-3 text-accent-teal hover:text-accent-teal-light transition-colors duration-300 group"
            whileHover={{ x: 5 }}
            transition={{ duration: 0.3 }}
          >
            <span className="text-sm font-medium tracking-wide uppercase">
              Contact Sales
            </span>
            <Key className="w-4 h-4 group-hover:rotate-12 transition-transform duration-300" />
          </motion.a>
        </motion.div>
      </motion.div>
    </section>
  );
};

export default FeaturesGrid;
