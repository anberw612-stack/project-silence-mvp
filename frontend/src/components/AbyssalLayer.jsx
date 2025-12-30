import { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';

/**
 * The Abyssal Layer (Phase 2: Disintegration & Interaction)
 * 
 * A visual overlay that creates a deep-sea sediment effect and handles "Shatter, Fall, Evaporate"
 * interactions for query submission.
 * 
 * Visual States:
 * 1. Sediment: Ambient background particles (deep sea oil/sediment).
 * 2. Debris: White/bright particles from "shattered" text input.
 * 3. Splash: Shockwave effect when debris hits the liquid surface.
 * 4. Evaporate: "Boiling" particles released after debris merges.
 * 
 * Mechanics:
 * - pointer-events: none for interaction safety.
 * - Window-level mouse tracking.
 * - Physics: Gravity, Drag, Buoyancy, Spring Forces.
 */
const AbyssalLayer = forwardRef((props, ref) => {
    const canvasRef = useRef(null);
    const mouseRef = useRef({ x: -1000, y: -1000 });
    const animationRef = useRef(null);

    // Particle Systems
    const sedimentRef = useRef([]); // Background layer
    const debrisRef = useRef([]);   // Falling text pieces
    const bubblesRef = useRef([]);  // Evaporation effect

    // Configuration
    const CONFIG = {
        // Sediment (Background)
        SEDIMENT_COUNT: 130,
        ZONE_HEIGHT_RATIO: 0.22, // Bottom 22%
        SEDIMENT_DRAG: 0.96,

        // Debris (Shatter)
        DEBRIS_GRAVITY: 0.25,
        DEBRIS_DRAG: 0.98,
        SPLASH_FORCE: 8.0,

        // Colors
        COLOR_CYAN: [100, 255, 255],     // High/Energy
        COLOR_NAVY: [20, 40, 100],       // Deep/Sediment
        COLOR_WHITE: [255, 255, 255],    // Fresh Debris

        // Evaporation
        BOIL_DELAY_MS: 400,
        BUBBLE_RISE_SPEED: 0.8
    };

    /**
     * External Interface for "Shatter" Effect
     */
    useImperativeHandle(ref, () => ({
        /**
         * Triggers the shatter effect at specific coordinates (usually the input box).
         * @param {number} x - Center X of the input
         * @param {number} y - Center Y of the input
         * @param {number} width - Width of the area to shatter
         */
        triggerShatter: (x, y, width = 300) => {
            createDebris(x, y, width);
        },

        /**
         * Triggers the evaporation "boil" effect from the bottom.
         */
        triggerEvaporation: () => {
            createEvaporation();
        }
    }));

    // Create debris particles from "shattered" text
    const createDebris = (originX, originY, spreadWidth) => {
        const particleCount = 60 + Math.random() * 40; // 60-100 particles

        for (let i = 0; i < particleCount; i++) {
            debrisRef.current.push({
                x: originX + (Math.random() - 0.5) * spreadWidth,
                y: originY + (Math.random() - 0.5) * 40,
                vx: (Math.random() - 0.5) * 4,
                vy: (Math.random() * -3) - 1,   // Initial upward pop
                size: 1.5 + Math.random() * 3,
                color: [...CONFIG.COLOR_WHITE, 1.0], // Start white opacity 1.0
                life: 1.0,
                state: 'falling' // falling -> splashing -> merging
            });
        }
    };

    // Create rising bubbles (response simulation)
    const createEvaporation = () => {
        const zoneTop = window.innerHeight * (1 - CONFIG.ZONE_HEIGHT_RATIO);
        const bubbleCount = 40;

        for (let i = 0; i < bubbleCount; i++) {
            bubblesRef.current.push({
                x: Math.random() * window.innerWidth,
                y: zoneTop + (Math.random() * 50),
                vx: (Math.random() - 0.5) * 0.5,
                vy: -1 - Math.random() * 2,
                size: 1 + Math.random() * 3,
                color: [...CONFIG.COLOR_CYAN, 0], // Start invisible
                life: 0,
                maxLife: 100 + Math.random() * 100
            });
        }
    };

    useEffect(() => {
        const canvas = canvasRef.current;
        if (!canvas) return;

        const ctx = canvas.getContext('2d');

        // Resize handler
        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        // Initialize Sediment (Background)
        const initSediment = () => {
            const particles = [];
            const zoneTop = window.innerHeight * (1 - CONFIG.ZONE_HEIGHT_RATIO);
            const zoneHeight = window.innerHeight * CONFIG.ZONE_HEIGHT_RATIO;

            for (let i = 0; i < CONFIG.SEDIMENT_COUNT; i++) {
                const baseY = zoneTop + Math.random() * zoneHeight;
                particles.push({
                    x: Math.random() * window.innerWidth,
                    y: baseY,
                    baseY: baseY,
                    vx: 0,
                    vy: 0,
                    size: 2 + Math.random() * 4,
                    phase: Math.random() * Math.PI * 2,
                    phaseSpeed: 0.005 + Math.random() * 0.01,
                    color: [...CONFIG.COLOR_NAVY, 0.4],
                    targetColor: [...CONFIG.COLOR_NAVY, 0.4],
                });
            }
            sedimentRef.current = particles;
        };

        // Physics Helpers
        const lerp = (a, b, t) => a + (b - a) * t;

        const applyForceToSediment = (x, y, force, radius) => {
            sedimentRef.current.forEach(p => {
                const dx = p.x - x;
                const dy = p.y - y;
                const dist = Math.sqrt(dx * dx + dy * dy);

                if (dist < radius) {
                    const f = (1 - dist / radius) * force;
                    p.vx += (dx / dist) * f;
                    p.vy += (dy / dist) * f;
                }
            });
        };

        // Animation Loop
        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const zoneTop = canvas.height * (1 - CONFIG.ZONE_HEIGHT_RATIO);
            const mouse = mouseRef.current;

            // 1. UPDATE SEDIMENT (Background)
            sedimentRef.current.forEach(p => {
                // Buoyancy
                p.phase += p.phaseSpeed;
                const targetY = p.baseY + Math.sin(p.phase) * 15;
                p.vy += (targetY - p.y) * 0.01; // Spring to base

                // Mouse Gravity
                const dx = mouse.x - p.x;
                const dy = mouse.y - p.y;
                const dist = Math.sqrt(dx * dx + dy * dy);
                if (dist < 300) {
                    const force = 0.00015 * Math.pow((300 - dist) / 300, 2) * 100;
                    p.vx += (dx / dist) * force;
                    p.vy += (dy / dist) * force;
                }

                // Drag & Move
                p.vx *= CONFIG.SEDIMENT_DRAG;
                p.vy *= CONFIG.SEDIMENT_DRAG;
                p.x += p.vx;
                p.y += p.vy;

                // Draw
                ctx.beginPath();
                const [r, g, b, a] = p.color;

                // Dynamic color lerp
                const currentYRatio = (p.y - zoneTop) / (canvas.height - zoneTop); // 0=top, 1=bottom
                const tc = currentYRatio < 0.2 ? CONFIG.COLOR_CYAN : CONFIG.COLOR_NAVY;

                p.color[0] = lerp(r, tc[0], 0.02);
                p.color[1] = lerp(g, tc[1], 0.02);
                p.color[2] = lerp(b, tc[2], 0.02);

                const gradient = ctx.createRadialGradient(p.x, p.y, 0, p.x, p.y, p.size * 2);
                gradient.addColorStop(0, `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},${a})`);
                gradient.addColorStop(1, `rgba(${Math.round(r)},${Math.round(g)},${Math.round(b)},0)`);

                ctx.fillStyle = gradient;
                ctx.arc(p.x, p.y, p.size * 2, 0, Math.PI * 2);
                ctx.fill();

                // Wrap
                if (p.x < 0) p.x = canvas.width;
                if (p.x > canvas.width) p.x = 0;
            });

            // 2. UPDATE DEBRIS (Shattered Text)
            for (let i = debrisRef.current.length - 1; i >= 0; i--) {
                const p = debrisRef.current[i];

                // Gravity
                p.vy += CONFIG.DEBRIS_GRAVITY;
                p.vx *= CONFIG.DEBRIS_DRAG;
                p.x += p.vx;
                p.y += p.vy;

                // Collision with Liquid Surface
                if (p.state === 'falling' && p.y > zoneTop) {
                    p.state = 'merged';
                    // SPLASH: Push sediment down
                    applyForceToSediment(p.x, p.y, CONFIG.SPLASH_FORCE, 100);

                    // Slow down
                    p.vy *= 0.1;

                    // Trigger color change to blue
                    p.color = [...CONFIG.COLOR_CYAN, 1.0];
                }

                // Draw Debris
                ctx.beginPath();
                const [r, g, b, a] = p.color;

                // Fade out if submerged deep
                if (p.state === 'merged') {
                    p.color[3] = lerp(a, 0, 0.05); // Rapid dissolve
                }

                ctx.fillStyle = `rgba(${r},${g},${b},${p.color[3]})`;
                ctx.rect(p.x, p.y, p.size, p.size); // Debris is square/sharp
                ctx.fill();

                // Remove dead debris
                if (p.color[3] < 0.01 || p.y > canvas.height) {
                    debrisRef.current.splice(i, 1);
                }
            }

            // 3. UPDATE BUBBLES (Evaporation)
            for (let i = bubblesRef.current.length - 1; i >= 0; i--) {
                const p = bubblesRef.current[i];
                p.life++;

                // Rise
                p.vy -= 0.05; // Accelerate up
                p.y += p.vy;
                p.x += Math.sin(p.life * 0.1) * 0.5; // Bubble wobble

                // Fade in then out
                if (p.life < 20) p.color[3] = lerp(p.color[3], 0.6, 0.1);
                else if (p.life > p.maxLife - 30) p.color[3] = lerp(p.color[3], 0, 0.1);

                ctx.beginPath();
                ctx.fillStyle = `rgba(${CONFIG.COLOR_CYAN.join(',')}, ${p.color[3]})`;
                ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
                ctx.fill();

                if (p.life > p.maxLife) bubblesRef.current.splice(i, 1);
            }

            animationRef.current = requestAnimationFrame(animate);
        };

        // Mouse Listeners
        const handleMouseMove = (e) => { mouseRef.current = { x: e.clientX, y: e.clientY }; };

        resize();
        initSediment();
        animate();

        window.addEventListener('resize', resize);
        window.addEventListener('mousemove', handleMouseMove);

        return () => {
            cancelAnimationFrame(animationRef.current);
            window.removeEventListener('resize', resize);
            window.removeEventListener('mousemove', handleMouseMove);
        };
    }, []);

    return (
        <canvas
            ref={canvasRef}
            style={{
                position: 'fixed',
                inset: 0,
                width: '100vw',
                height: '100vh',
                pointerEvents: 'none',
                zIndex: 0, // Behind UI
                background: 'transparent',
            }}
            aria-hidden="true"
        />
    );
});

export default AbyssalLayer;
