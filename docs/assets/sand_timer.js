/**
 * Deadliner — Dynamic Hourglass & Kinetic Sand Particle Engine (v2.0)
 * 
 * Interactive time-physics animation synchronized with page scroll depth:
 * 1. Rich kinetic sand particle system:
 *    - Ambient drifting sand grains passing BEHIND solid architectural cards.
 *    - Interactive sparkling cursor trail (mouse wand physics).
 *    - Kinetic cascade waterfall on scroll down.
 *    - Click impulse shockwave.
 * 2. Precision vector hourglass HUD (Refined Minimalist Capsule):
 *    - Seamless 42x80px frosted glass capsule.
 *    - Mathematically symmetric top & bottom sand bulb simulations (100% full at scroll ends).
 *    - Animated trickle & dune impact splash sparks.
 *    - Amber gold -> Tomato Red cutoff alert transition.
 *    - 3D flip inversion + smooth back-to-top on click.
 * 
 * Zero external libraries. 60-120fps Retina Canvas. Fully throttled.
 */

(function () {
  'use strict';

  // Check user preference for reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Language detection (EN vs UK)
  const isUk = document.documentElement.lang === 'uk' || window.location.pathname.includes('/uk/');
  const i18n = {
    tooltip: isUk ? 'Опівнічний дедлайн • Клікніть, щоб перевернути час' : 'Midnight Cutoff • Click to invert time',
    cutoff: isUk ? '00:00 ДЕДЛАЙН' : '00:00 CUTOFF'
  };

  /* ==========================================================================
     1. Ambient & Interactive Sand Particle System
     ========================================================================== */
  class SandParticlesSystem {
    constructor() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'sandCanvas';
      this.canvas.className = 'ambient-sand-canvas';
      this.ctx = this.canvas.getContext('2d');
      document.body.prepend(this.canvas);

      this.particles = [];
      this.trailParticles = [];
      this.maxTrail = 35;
      this.particleCount = window.innerWidth < 768 ? 50 : 110;

      this.lastScrollY = window.scrollY || 0;
      this.scrollVelocity = 0;
      this.targetScrollVelocity = 0;

      this.mouse = { x: -1000, y: -1000, lastX: -1000, lastY: -1000, active: false };

      this.resize();
      this.initParticles();
      this.bindEvents();
    }

    resize() {
      this.dpr = Math.min(window.devicePixelRatio || 1, 2);
      this.width = window.innerWidth;
      this.height = window.innerHeight;
      this.canvas.width = this.width * this.dpr;
      this.canvas.height = this.height * this.dpr;
      this.ctx.scale(this.dpr, this.dpr);
    }

    initParticles() {
      this.particles = [];
      const colors = [
        { r: 227, g: 179, b: 65,  a: 0.45 }, // Amber gold sand
        { r: 245, g: 200, b: 90,  a: 0.55 }, // Bright gold glint
        { r: 255, g: 82,  b: 82,  a: 0.35 }, // Cutoff tomato red
        { r: 255, g: 255, b: 255, a: 0.28 }, // Stardust white
        { r: 88,  g: 166, b: 255, a: 0.30 }  // Cyan glint
      ];

      for (let i = 0; i < this.particleCount; i++) {
        const c = colors[Math.floor(Math.random() * colors.length)];
        this.particles.push({
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          radius: Math.random() * 1.2 + 0.6,
          baseVy: Math.random() * 0.45 + 0.25,
          vx: (Math.random() - 0.5) * 0.3,
          vy: 0,
          color: c,
          baseAlpha: c.a,
          swaySpeed: Math.random() * 0.02 + 0.008,
          swayOffset: Math.random() * Math.PI * 2
        });
      }
    }

    bindEvents() {
      window.addEventListener('resize', () => this.resize(), { passive: true });

      // Kinetic scroll dynamics
      window.addEventListener('scroll', () => {
        const currentY = window.scrollY || 0;
        const delta = currentY - this.lastScrollY;
        this.lastScrollY = currentY;

        // Boost velocity proportional to scroll speed
        this.targetScrollVelocity = Math.max(-5, Math.min(delta * 0.16, 12));

        // When scrolling down rapidly, cascade a gentle shower of sand grains from the top
        if (delta > 8 && this.particles.length < this.particleCount + 25) {
          const spawnCount = Math.min(Math.floor(delta / 6), 4);
          for (let k = 0; k < spawnCount; k++) {
            this.particles.push({
              x: Math.random() * this.width,
              y: -4,
              radius: Math.random() * 1.2 + 0.7,
              baseVy: Math.random() * 0.6 + 0.4,
              vx: (Math.random() - 0.5) * 0.4,
              vy: Math.random() * 2 + 1,
              color: { r: 227, g: 179, b: 65, a: 0.55 },
              baseAlpha: 0.55,
              swaySpeed: 0.02,
              swayOffset: Math.random() * Math.PI * 2,
              transient: true
            });
          }
        }
      }, { passive: true });

      // Interactive mouse trail & physics
      window.addEventListener('mousemove', (e) => {
        const mx = e.clientX;
        const my = e.clientY;

        if (this.mouse.active) {
          const distMoved = Math.hypot(mx - this.mouse.lastX, my - this.mouse.lastY);
          // Spawn sparkling sand dust along cursor trajectory
          if (distMoved > 10 && this.trailParticles.length < this.maxTrail) {
            this.trailParticles.push({
              x: mx + (Math.random() - 0.5) * 8,
              y: my + (Math.random() - 0.5) * 8,
              vx: (Math.random() - 0.5) * 1.2,
              vy: Math.random() * 0.8 + 0.4, // Gentle downward drift
              radius: Math.random() * 1.3 + 0.7,
              life: 38,
              maxLife: 38,
              color: Math.random() > 0.3 ? { r: 245, g: 200, b: 90 } : { r: 255, g: 100, b: 100 }
            });
            this.mouse.lastX = mx;
            this.mouse.lastY = my;
          }
        } else {
          this.mouse.lastX = mx;
          this.mouse.lastY = my;
        }

        this.mouse.x = mx;
        this.mouse.y = my;
        this.mouse.active = true;
      }, { passive: true });

      window.addEventListener('mouseleave', () => {
        this.mouse.active = false;
      });

      // Click shockwave impulse
      window.addEventListener('click', (e) => {
        // Only trigger shockwave if not clicking interactive UI buttons
        if (e.target.closest('a, button, input, .hourglass-hud')) return;
        this.shockwave(e.clientX, e.clientY);
      }, { passive: true });
    }

    shockwave(cx, cy) {
      // Repel ambient particles radially
      for (let p of this.particles) {
        const dx = p.x - cx;
        const dy = p.y - cy;
        const dist = Math.hypot(dx, dy);
        if (dist < 180 && dist > 0) {
          const force = (180 - dist) / 180;
          p.vx += (dx / dist) * force * 5.5;
          p.vy += (dy / dist) * force * 5.5;
        }
      }

      // Spawn ripple micro-sparks
      for (let i = 0; i < 14; i++) {
        const angle = Math.random() * Math.PI * 2;
        const spd = Math.random() * 3.5 + 1;
        this.trailParticles.push({
          x: cx,
          y: cy,
          vx: Math.cos(angle) * spd,
          vy: Math.sin(angle) * spd,
          radius: Math.random() * 1.4 + 0.8,
          life: 30,
          maxLife: 30,
          color: { r: 227, g: 179, b: 65 }
        });
      }
    }

    burst(x, y, count = 25) {
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 4.5 + 1.5;
        this.trailParticles.push({
          x: x,
          y: y,
          radius: Math.random() * 1.5 + 0.8,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 1.8,
          color: { r: 245, g: 200, b: 90 },
          life: 45,
          maxLife: 45
        });
      }
    }

    update(time) {
      // Smooth decay of scroll velocity impulse
      this.scrollVelocity += (this.targetScrollVelocity - this.scrollVelocity) * 0.14;
      this.targetScrollVelocity *= 0.93;

      this.ctx.clearRect(0, 0, this.width, this.height);

      /* --- 1. Render Interactive Mouse Trail Particles --- */
      for (let i = this.trailParticles.length - 1; i >= 0; i--) {
        const tp = this.trailParticles[i];
        tp.life--;
        tp.vx *= 0.95;
        tp.vy += 0.08; // Gentle gravity
        tp.x += tp.vx;
        tp.y += tp.vy;

        const alpha = (tp.life / tp.maxLife) * 0.85;
        this.ctx.beginPath();
        this.ctx.arc(tp.x, tp.y, tp.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = `rgba(${tp.color.r}, ${tp.color.g}, ${tp.color.b}, ${alpha})`;
        this.ctx.shadowColor = `rgba(${tp.color.r}, ${tp.color.g}, ${tp.color.b}, 0.6)`;
        this.ctx.shadowBlur = 6;
        this.ctx.fill();
        this.ctx.shadowBlur = 0;

        if (tp.life <= 0) {
          this.trailParticles.splice(i, 1);
        }
      }

      /* --- 2. Render Ambient Drifting Sand Particles --- */
      for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];

        // Horizontal sway
        p.swayOffset += p.swaySpeed;
        const sway = Math.sin(p.swayOffset) * 0.3;

        // Downward kinetic velocity + friction on radial perturbations
        p.vx *= 0.97;
        p.vy = p.baseVy + this.scrollVelocity;
        p.x += p.vx + sway;
        p.y += p.vy;

        // Cursor magnetic dispersion
        if (this.mouse.active) {
          const dx = p.x - this.mouse.x;
          const dy = p.y - this.mouse.y;
          const dist = Math.hypot(dx, dy);
          const maxDist = 90;
          if (dist < maxDist && dist > 0) {
            const force = (maxDist - dist) / maxDist;
            p.x += (dx / dist) * force * 2.8;
            p.y += (dy / dist) * force * 2.8;
          }
        }

        // Screen boundary wrap
        if (p.y > this.height + 6) {
          if (p.transient) {
            this.particles.splice(i, 1);
            continue;
          }
          p.y = -6;
          p.x = Math.random() * this.width;
        } else if (p.y < -6) {
          p.y = this.height + 6;
          p.x = Math.random() * this.width;
        }
        if (p.x > this.width + 6) p.x = -6;
        else if (p.x < -6) p.x = this.width + 6;

        // Render ambient grain
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.baseAlpha})`;
        this.ctx.fill();
      }
    }
  }

  /* ==========================================================================
     2. Refined Minimalist Hourglass HUD (Sleek Glass Capsule)
     ========================================================================== */
  class HourglassHUD {
    constructor(sandParticles) {
      this.sandParticles = sandParticles;
      this.hud = document.createElement('aside');
      this.hud.id = 'hourglassHud';
      this.hud.className = 'hourglass-hud';
      this.hud.setAttribute('role', 'button');
      this.hud.setAttribute('tabindex', '0');
      this.hud.setAttribute('aria-label', i18n.tooltip);
      this.hud.title = i18n.tooltip;

      this.hud.innerHTML = `
        <div class="hourglass-canvas-wrap">
          <canvas id="hourglassCanvas" width="64" height="100"></canvas>
        </div>
        <span class="hud-pct" id="hudPct">0%</span>
        <div class="hud-tooltip-card">${i18n.tooltip}</div>
      `;

      document.body.appendChild(this.hud);

      this.canvas = document.getElementById('hourglassCanvas');
      this.ctx = this.canvas.getContext('2d');
      this.pctEl = document.getElementById('hudPct');
      this.dpr = Math.min(window.devicePixelRatio || 1, 2);

      // Canvas dimensions (32x50 CSS points, scaled for Retina)
      this.cssW = 32;
      this.cssH = 50;
      this.canvas.width = this.cssW * this.dpr;
      this.canvas.height = this.cssH * this.dpr;
      this.canvas.style.width = `${this.cssW}px`;
      this.canvas.style.height = `${this.cssH}px`;
      this.ctx.scale(this.dpr, this.dpr);

      this.scrollProgress = 0;
      this.targetProgress = 0;
      this.fallingGrains = [
        { y: 0.1, speed: 0.055 },
        { y: 0.35, speed: 0.065 },
        { y: 0.65, speed: 0.06 },
        { y: 0.9, speed: 0.07 }
      ];

      this.splashParticles = [];
      this.isFlipping = false;

      this.bindEvents();
    }

    bindEvents() {
      // Calculate scroll progress
      const updateScroll = () => {
        const docH = document.documentElement.scrollHeight - window.innerHeight;
        this.targetProgress = docH > 0 ? Math.min(Math.max(window.scrollY / docH, 0), 1) : 0;
      };

      window.addEventListener('scroll', updateScroll, { passive: true });
      window.addEventListener('resize', updateScroll, { passive: true });
      updateScroll();

      // 3D tilt on mouse hover
      this.hud.addEventListener('mousemove', (e) => {
        const rect = this.hud.getBoundingClientRect();
        const nx = (e.clientX - rect.left) / rect.width - 0.5;
        const ny = (e.clientY - rect.top) / rect.height - 0.5;
        if (!this.isFlipping) {
          this.hud.style.transform = `translateY(-2px) perspective(300px) rotateY(${nx * 14}deg) rotateX(${-ny * 14}deg)`;
        }
      });

      this.hud.addEventListener('mouseleave', () => {
        if (!this.isFlipping) {
          this.hud.style.transform = '';
        }
      });

      // Click to invert time & scroll to top
      const triggerFlip = () => {
        if (this.isFlipping) return;
        this.isFlipping = true;
        this.hud.style.transform = '';
        this.hud.classList.add('flipping');

        // Particle burst
        const rect = this.hud.getBoundingClientRect();
        this.sandParticles.burst(rect.left + rect.width / 2, rect.top + rect.height / 2, 30);

        // Smooth back to top
        window.scrollTo({ top: 0, behavior: 'smooth' });

        setTimeout(() => {
          this.hud.classList.remove('flipping');
          this.isFlipping = false;
        }, 750);
      };

      this.hud.addEventListener('click', triggerFlip);
      this.hud.addEventListener('keydown', (e) => {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          triggerFlip();
        }
      });
    }

    render() {
      // Smooth interpolation for liquid sand feeling
      this.scrollProgress += (this.targetProgress - this.scrollProgress) * 0.12;
      const p = this.scrollProgress;

      // Update telemetry badge
      if (p >= 0.94) {
        this.pctEl.textContent = '00:00';
        this.hud.classList.add('deadline-urgent');
      } else {
        this.pctEl.textContent = `${Math.round(p * 100)}%`;
        this.hud.classList.remove('deadline-urgent');
      }

      const w = this.cssW;
      const h = this.cssH;
      const ctx = this.ctx;
      ctx.clearRect(0, 0, w, h);

      // Glass Hourglass Coordinates
      const cx = w / 2; // 16
      const topPlateY = 4;
      const botPlateY = h - 4; // 46
      const waistY = h / 2; // 25
      const bulbW = 11.5;   // Top/bottom rim half-width
      const waistHalfW = 2.2; // Neck half-width
      const coneTopY = topPlateY + 1.5; // 5.5
      const coneBotY = botPlateY - 1.5; // 44.5
      const coneHeight = waistY - coneTopY; // 19.5

      // Color interpolation: Warm Amber Gold -> Tomato Red as deadline approaches
      const urgentFactor = Math.max(0, Math.min((p - 0.72) / 0.28, 1));
      const sandR = Math.round(227 + (255 - 227) * urgentFactor);
      const sandG = Math.round(179 + (82 - 179) * urgentFactor);
      const sandB = Math.round(65 + (82 - 65) * urgentFactor);
      const sandColor = `rgb(${sandR}, ${sandG}, ${sandB})`;
      const sandColorAlpha = (a) => `rgba(${sandR}, ${sandG}, ${sandB}, ${a})`;

      /* ---------------- 1. Top Sand Bulb ---------------- */
      // Remaining fraction in top cone (1 at top, 0 at bottom)
      const topRemaining = Math.max(0, 1 - p);
      if (topRemaining > 0.008) {
        const surfY = coneTopY + (1 - topRemaining) * coneHeight;
        const progressFromWaist = (waistY - surfY) / coneHeight;
        const surfHalfW = waistHalfW + (bulbW - waistHalfW) * progressFromWaist;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(cx - surfHalfW, surfY);
        ctx.lineTo(cx + surfHalfW, surfY);
        ctx.lineTo(cx + waistHalfW, waistY);
        ctx.lineTo(cx - waistHalfW, waistY);
        ctx.closePath();

        const topGrad = ctx.createLinearGradient(0, surfY, 0, waistY);
        topGrad.addColorStop(0, sandColorAlpha(0.95));
        topGrad.addColorStop(1, sandColorAlpha(0.75));
        ctx.fillStyle = topGrad;
        ctx.fill();
        ctx.restore();
      }

      /* ---------------- 2. Bottom Sand Bulb (100% Symmetrical Math) ---------------- */
      // Accumulated fraction in bottom cone (0 at top, 1 at bottom)
      const botFilled = Math.min(1, p);
      if (botFilled > 0.005) {
        // Sand surface level in bottom cone: rises from coneBotY up to waistY
        const surfY = coneBotY - botFilled * coneHeight;
        const progressFromWaist = (surfY - waistY) / coneHeight; // 0 at waist, 1 at base
        const surfHalfW = waistHalfW + (bulbW - waistHalfW) * progressFromWaist;
        
        // Gentle dune peak curve in the middle (flattens as it tops out)
        const dunePeak = (botFilled > 0.02 && botFilled < 0.98) ? Math.sin(botFilled * Math.PI) * 2.2 : 0;

        ctx.save();
        ctx.beginPath();
        // Start at bottom-left rim
        ctx.moveTo(cx - bulbW, coneBotY);
        // Across bottom rim to bottom-right
        ctx.lineTo(cx + bulbW, coneBotY);
        // Up the right slanted cone wall to sand surface
        ctx.lineTo(cx + surfHalfW, surfY);
        // Across the sand dune surface to left wall
        ctx.quadraticCurveTo(cx, surfY - dunePeak, cx - surfHalfW, surfY);
        // Down the left slanted cone wall back to bottom-left rim
        ctx.lineTo(cx - bulbW, coneBotY);
        ctx.closePath();

        const botGrad = ctx.createLinearGradient(0, surfY - dunePeak, 0, coneBotY);
        botGrad.addColorStop(0, sandColorAlpha(0.95));
        botGrad.addColorStop(1, sandColorAlpha(0.70));
        ctx.fillStyle = botGrad;
        ctx.fill();
        ctx.restore();
      }

      /* ---------------- 3. Animated Falling Stream ---------------- */
      if (topRemaining > 0.01) {
        const targetY = coneBotY - botFilled * coneHeight;

        // Continuous luminous stream line
        ctx.beginPath();
        ctx.moveTo(cx, waistY);
        ctx.lineTo(cx, targetY);
        ctx.strokeStyle = sandColorAlpha(0.7);
        ctx.lineWidth = 1.0;
        ctx.stroke();

        // Animated falling micro-grains
        ctx.fillStyle = sandColorAlpha(0.95);
        for (let grain of this.fallingGrains) {
          grain.y += grain.speed;
          if (grain.y > 1) grain.y = 0;
          const gy = waistY + grain.y * (targetY - waistY);
          ctx.beginPath();
          ctx.arc(cx, gy, 0.7, 0, Math.PI * 2);
          ctx.fill();
        }

        // Dune impact splash sparks
        if (Math.random() < 0.45 && targetY > waistY) {
          this.splashParticles.push({
            x: cx,
            y: targetY,
            vx: (Math.random() - 0.5) * 1.1,
            vy: -Math.random() * 1.0 - 0.3,
            life: 8,
            color: sandColor
          });
        }
      }

      // Render & update splash particles
      for (let i = this.splashParticles.length - 1; i >= 0; i--) {
        const sp = this.splashParticles[i];
        sp.x += sp.vx;
        sp.y += sp.vy;
        sp.vy += 0.2;
        sp.life--;
        ctx.beginPath();
        ctx.arc(sp.x, sp.y, 0.55, 0, Math.PI * 2);
        ctx.fillStyle = sp.color;
        ctx.fill();
        if (sp.life <= 0) this.splashParticles.splice(i, 1);
      }

      /* ---------------- 4. Hairline Vector Glass Silhouette ---------------- */
      ctx.save();

      // Top and bottom cap plates
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.38)';
      ctx.lineWidth = 1.2;
      ctx.lineCap = 'round';

      ctx.beginPath();
      ctx.moveTo(cx - bulbW - 1.5, topPlateY);
      ctx.lineTo(cx + bulbW + 1.5, topPlateY);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(cx - bulbW - 1.5, botPlateY);
      ctx.lineTo(cx + bulbW + 1.5, botPlateY);
      ctx.stroke();

      // Conical glass walls
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.22)';
      ctx.lineWidth = 1.0;
      ctx.beginPath();

      // Left glass wall
      ctx.moveTo(cx - bulbW, coneTopY);
      ctx.lineTo(cx - waistHalfW, waistY);
      ctx.lineTo(cx - bulbW, coneBotY);

      // Right glass wall
      ctx.moveTo(cx + bulbW, coneTopY);
      ctx.lineTo(cx + waistHalfW, waistY);
      ctx.lineTo(cx + bulbW, coneBotY);
      ctx.stroke();

      // Delicate specular reflection highlight on upper-left curve
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.36)';
      ctx.lineWidth = 0.9;
      ctx.beginPath();
      ctx.moveTo(cx - bulbW + 1.2, coneTopY + 1.5);
      ctx.lineTo(cx - waistHalfW - 0.8, waistY - 2.5);
      ctx.stroke();

      ctx.restore();
    }
  }

  /* ==========================================================================
     3. Engine Initialization & Animation Loop
     ========================================================================== */
  function init() {
    if (prefersReducedMotion) {
      return; // Respect reduced motion preferences
    }

    const sandSystem = new SandParticlesSystem();
    const hourglassHUD = new HourglassHUD(sandSystem);

    let isVisible = true;
    document.addEventListener('visibilitychange', () => {
      isVisible = !document.hidden;
    });

    function loop(time) {
      if (isVisible) {
        sandSystem.update(time);
        hourglassHUD.render();
      }
      requestAnimationFrame(loop);
    }

    requestAnimationFrame(loop);
  }

  // Run when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
