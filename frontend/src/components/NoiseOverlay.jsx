/**
 * Noise Overlay Component
 *
 * A subtle SVG noise texture overlay that:
 * - Removes the "cheap digital" look
 * - Adds paper-like texture
 * - Fixed position covering the entire viewport
 * - Non-interactive (pointer-events: none)
 */

const NoiseOverlay = () => {
  return (
    <div
      className="fixed inset-0 pointer-events-none z-[9999]"
      style={{
        opacity: 0.035,
        backgroundImage: `url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noise'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noise)'/%3E%3C/svg%3E")`,
        backgroundRepeat: 'repeat',
      }}
      aria-hidden="true"
    />
  );
};

export default NoiseOverlay;
