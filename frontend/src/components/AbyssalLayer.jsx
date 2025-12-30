import { useRef, useEffect, useImperativeHandle, forwardRef } from 'react';

/**
 * The Abyssal Layer (HOTFIX: Render Debugging)
 * 
 * fixes:
 * - Z-Index raised to 9999 (with pointer-events: none) to ensure visibility above backgrounds.
 * - DEBUG MODE: Particles forced to Bright RED (#FF0000) and full opacity.
 * - Added console logs to verify animation loop.
 */
const AbyssalLayer = forwardRef((props, ref) => {
    const canvasRef = useRef(null);
    const mouseRef = useRef({ x: -1000, y: -1000 });
    const animationRef = useRef(null);
    const frameCountRef = useRef(0);

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

        // Colors (DEBUG MODE: FORCE RED)
        // Was: COLOR_CYAN: [100, 255, 255]
        // Was: COLOR_NAVY: [20, 40, 100]
        COLOR_CYAN: [255, 0, 0],     // RED (High/Energy)
        COLOR_NAVY: [200, 0, 0],     // DARK RED (Deep/Sediment)
        COLOR_WHITE: [255, 255, 255],// White remains for debris

        // Evaporation
        BOIL_DELAY_MS: 400,
        BUBBLE_RISE_SPEED: 0.8
    };

    /**
     * External Interface for "Shatter" Effect
     */
    useImperativeHandle(ref, () => ({
        triggerShatter: (x, y, width = 300) => {
            console.log("💥 [AbyssalLayer] Shatter triggered at", x, y);
            createDebris(x, y, width);
        },
        triggerEvaporation: () => {
            console.log("💨 [AbyssalLayer] Evaporation triggered");
            createEvaporation();
        }
    }));

    // Create debris particles from "shattered" text
    const createDebris = (originX, originY, spreadWidth) => {
        const particleCount = 60 + Math.random() * 40;
        for (let i = 0; i < particleCount; i++) {
            debrisRef.current.push({
                x: originX + (Math.random() - 0.5) * spreadWidth,
                y: originY + (Math.random() - 0.5) * 40,
                vx: (Math.random() - 0.5) * 4,
                vy: (Math.random() * -3) - 1,
                size: 1.5 + Math.random() * 3,
                color: [...CONFIG.COLOR_WHITE, 1.0],
                life: 1.0,
                state: 'falling'
            });
        }
    };

    // Create rising bubbles
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
                color: [...CONFIG.COLOR_CYAN, 0],
                life: 0,
                maxLife: 100 + Math.random() * 100
            });
        }
    };

    useEffect(() => {
        console.log("🌊 [AbyssalLayer] Mounting & Initializing...");
        const canvas = canvasRef.current;
        if (!canvas) {
            console.error("❌ [AbyssalLayer] Canvas ref is null!");
            return;
        }

        const ctx = canvas.getContext('2d');

        // Resize handler
        const resize = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
            console.log("📏 [AbyssalLayer] Resized to", canvas.width, canvas.height);
        };

        // Initialize Sediment (Background)
        const initSediment = () => {
            const particles = [];
            const zoneTop = window.innerHeight * (1 - CONFIG.ZONE_HEIGHT_RATIO);
            const zoneHeight = window.innerHeight * CONFIG.ZONE_HEIGHT_RATIO;

            console.log(`🔹 [AbyssalLayer] Init Sediment: 130 particles in zone y=${Math.round(zoneTop)} to ${window.innerHeight}`);

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
                    color: [...CONFIG.COLOR_NAVY, 1.0], // DEBUG: Full opacity 1.0
                    targetColor: [...CONFIG.COLOR_NAVY, 1.0],
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
            frameCountRef.current++;
            if (frameCountRef.current % 300 === 0) {
                console.log("⏱️ [AbyssalLayer] Animation Loop Running... Frame:", frameCountRef.current);
            }

            ctx.clearRect(0, 0, canvas.width, canvas.height);

            const zoneTop = canvas.height * (1 - CONFIG.ZONE_HEIGHT_RATIO);
            const mouse = mouseRef.current;

            // 1. UPDATE SEDIMENT (Background)
            sedimentRef.current.forEach(p => {
                // Buoyancy
                p.phase += p.phaseSpeed;
                const targetY = p.baseY + Math.sin(p.phase) * 15;
                p.vy += (targetY - p.y) * 0.01;

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

            // 2. UPDATE DEBRIS
            for (let i = debrisRef.current.length - 1; i >= 0; i--) {
                const p = debrisRef.current[i];
                p.vy += CONFIG.DEBRIS_GRAVITY;
                p.vx *= CONFIG.DEBRIS_DRAG;
                p.x += p.vx;
                p.y += p.vy;

                if (p.state === 'falling' && p.y > zoneTop) {
                    p.state = 'merged';
                    applyForceToSediment(p.x, p.y, CONFIG.SPLASH_FORCE, 100);
                    p.vy *= 0.1;
                    p.color = [...CONFIG.COLOR_CYAN, 1.0];
                }

                ctx.beginPath();
                const [r, g, b, a] = p.color;
                if (p.state === 'merged') {
                    p.color[3] = lerp(a, 0, 0.05);
                }
                ctx.fillStyle = `rgba(${r},${g},${b},${p.color[3]})`;
                ctx.rect(p.x, p.y, p.size, p.size);
                ctx.fill();

                if (p.color[3] < 0.01 || p.y > canvas.height) {
                    debrisRef.current.splice(i, 1);
                }
            }

            // 3. UPDATE BUBBLES
            for (let i = bubblesRef.current.length - 1; i >= 0; i--) {
                const p = bubblesRef.current[i];
                p.life++;
                p.vy -= 0.05;
                p.y += p.vy;
                p.x += Math.sin(p.life * 0.1) * 0.5;

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
        const handleMouseMove = (e) => {
            mouseRef.current = { x: e.clientX, y: e.clientY };
        };

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
                zIndex: 9999, // FIX: Very high z-index
                background: 'transparent', // FIX: Ensure transparent background
            }}
            aria-hidden="true"
        />
    );
});

export default AbyssalLayer;
