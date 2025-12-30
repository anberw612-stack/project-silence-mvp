/**
 * Confuser Landing Page
 *
 * A luxury fintech and cyber-security landing page featuring:
 * - The "Vault" dark theme aesthetic
 * - Glassmorphism and noise texture effects
 * - Sophisticated typography (serif headings, sans body)
 * - Heavy, smooth Framer Motion animations
 * - Aurora gradient mesh backgrounds
 */

import { Hero, FeaturesGrid, NoiseOverlay, Navbar } from './components';

function App() {
  return (
    <div className="relative min-h-screen bg-vault-obsidian text-neutral-100 overflow-x-hidden scrollbar-thin">
      {/* Noise texture overlay for premium feel */}
      <NoiseOverlay />

      {/* Fixed Navigation */}
      <Navbar />

      {/* Main Content */}
      <main>
        {/* Hero Section with Aurora Mesh */}
        <Hero />

        {/* Features Grid Section */}
        <section id="features">
          <FeaturesGrid />
        </section>
      </main>

      {/* Footer can be added here */}
    </div>
  );
}

export default App;
