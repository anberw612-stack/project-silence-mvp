/**
 * Navbar Component
 *
 * A sophisticated navigation bar with:
 * - Glassmorphism effect
 * - Ghost navigation links
 * - Logo with subtle animation
 * - Fixed position with backdrop blur
 */

import { motion } from 'framer-motion';
import { Shield, Menu, X } from 'lucide-react';
import { useState } from 'react';
import GhostButton from './GhostButton';

// ═══════════════════════════════════════════════════════════════════════════════
// NAVBAR COMPONENT
// ═══════════════════════════════════════════════════════════════════════════════

const Navbar = () => {
  const [isOpen, setIsOpen] = useState(false);

  const navLinks = [
    { name: 'Features', href: '#features' },
    { name: 'Security', href: '#security' },
    { name: 'Pricing', href: '#pricing' },
    { name: 'About', href: '#about' },
  ];

  return (
    <motion.nav
      className="fixed top-0 left-0 right-0 z-50"
      initial={{ y: -100, opacity: 0 }}
      animate={{ y: 0, opacity: 1 }}
      transition={{ duration: 0.8, ease: [0.16, 1, 0.3, 1] }}
    >
      {/* Navbar background with glass effect */}
      <div className="absolute inset-0 bg-vault-obsidian/80 backdrop-blur-md border-b border-white/[0.05]" />

      <div className="relative max-w-7xl mx-auto px-6 md:px-12">
        <div className="flex items-center justify-between h-20">
          {/* Logo */}
          <motion.a
            href="/"
            className="flex items-center gap-3 group"
            whileHover={{ scale: 1.02 }}
            transition={{ duration: 0.2 }}
          >
            <div className="relative">
              {/* Logo glow */}
              <div className="absolute inset-0 bg-accent-teal/20 rounded-lg blur-lg opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              <div className="relative w-10 h-10 rounded-lg bg-gradient-to-br from-accent-teal/20 to-accent-teal/5 border border-accent-teal/30 flex items-center justify-center group-hover:border-accent-teal/50 transition-colors duration-300">
                <Shield className="w-5 h-5 text-accent-teal" strokeWidth={1.5} />
              </div>
            </div>
            <span className="font-serif font-semibold text-xl text-white tracking-tight">
              Confuser
            </span>
          </motion.a>

          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center gap-10">
            {/* Nav Links */}
            <ul className="flex items-center gap-8">
              {navLinks.map((link, index) => (
                <motion.li
                  key={link.name}
                  initial={{ opacity: 0, y: -10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    delay: 0.3 + index * 0.1,
                    duration: 0.5,
                    ease: [0.16, 1, 0.3, 1],
                  }}
                >
                  <a
                    href={link.href}
                    className="text-sm text-neutral-400 hover:text-accent-teal transition-colors duration-300 tracking-wide"
                  >
                    {link.name}
                  </a>
                </motion.li>
              ))}
            </ul>

            {/* CTA Button */}
            <motion.div
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: 0.7, duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
            >
              <GhostButton size="small" variant="teal">
                Get Started
              </GhostButton>
            </motion.div>
          </div>

          {/* Mobile Menu Button */}
          <button
            className="md:hidden relative w-10 h-10 flex items-center justify-center text-neutral-400 hover:text-white transition-colors"
            onClick={() => setIsOpen(!isOpen)}
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      <motion.div
        className="md:hidden absolute top-full left-0 right-0 bg-vault-obsidian/95 backdrop-blur-md border-b border-white/[0.05]"
        initial={{ height: 0, opacity: 0 }}
        animate={{
          height: isOpen ? 'auto' : 0,
          opacity: isOpen ? 1 : 0,
        }}
        transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
        style={{ overflow: 'hidden' }}
      >
        <div className="px-6 py-6 space-y-4">
          {navLinks.map((link) => (
            <a
              key={link.name}
              href={link.href}
              className="block text-neutral-300 hover:text-accent-teal transition-colors duration-300 py-2"
              onClick={() => setIsOpen(false)}
            >
              {link.name}
            </a>
          ))}
          <div className="pt-4">
            <GhostButton size="small" variant="teal" className="w-full">
              Get Started
            </GhostButton>
          </div>
        </div>
      </motion.div>
    </motion.nav>
  );
};

export default Navbar;
