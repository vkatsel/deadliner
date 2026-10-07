/**
 * Deadliner — Dynamic Hourglass & Kinetic Sand Particle Engine
 * 
 * Interactive time-physics animation synchronized with page scroll depth:
 * 1. Ambient kinetic sand particle stream responding to scrolling inertia & cursor physics.
 * 2. Precision vector hourglass HUD tracking scroll progress & midnight cutoff.
 * 3. 1-click time inversion (3D flip + smooth back-to-top scroll).
 * 
 * Zero dependencies. High-DPI Canvas. 60fps requestAnimationFrame.
 */

(function () {
  'use strict';

  // Check user preference for reduced motion
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Language detection (EN vs UK)
  const isUk = document.documentElement.lang === 'uk' || window.location.pathname.includes('/uk/');
  const i18n = {
    tooltip: isUk ? 'Опівнічний дедлайн • Клікніть, щоб перевернути час' : 'Midnight Cutoff • Click to invert time',
    cutoff: isUk ? '00:00 ДЕДЛАЙН' : '00:00 CUTOFF',
    timeRemaining: isUk ? 'ДО ДЕДЛАЙНУ' : 'T-MINUS'
  };

  /* ==========================================================================
     1. Ambient Kinetic Sand Particle System
     ========================================================================== */
  class SandParticlesSystem {
    constructor() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'sandCanvas';
      this.canvas.className = 'ambient-sand-canvas';
      this.ctx = this.canvas.getContext('2d');
      document.body.prepend(this.canvas);

      this.particles = [];
      this.particleCount = window.innerWidth < 768 ? 35 : 60;
      this.lastScrollY = window.scrollY || 0;
      this.scrollVelocity = 0;
      this.targetScrollVelocity = 0;
      this.mouse = { x: -1000, y: -1000, active: false };

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
        { r: 227, g: 179, b: 65, a: 0.45 }, // Amber sand
        { r: 255, g: 82,  b: 82, a: 0.35 }, // Cutoff tomato red
        { r: 255, g: 255, b: 255, a: 0.25 }, // Stardust white
        { r: 88,  g: 166, b: 255, a: 0.30 }  // Cyan glint
      ];

      for (let i = 0; i < this.particleCount; i++) {
        const c = colors[Math.floor(Math.random() * colors.length)];
        this.particles.push({
          x: Math.random() * this.width,
          y: Math.random() * this.height,
          radius: Math.random() * 1.1 + 0.6,
          baseVy: Math.random() * 0.5 + 0.3,
          vx: (Math.random() - 0.5) * 0.35,
          vy: 0,
          color: c,
          baseAlpha: c.a,
          swaySpeed: Math.random() * 0.02 + 0.01,
          swayOffset: Math.random() * Math.PI * 2
        });
      }
    }

    bindEvents() {
      window.addEventListener('resize', () => this.resize(), { passive: true });

      window.addEventListener('scroll', () => {
        const currentY = window.scrollY || 0;
        const delta = currentY - this.lastScrollY;
        this.lastScrollY = currentY;
        // Boost velocity proportional to scroll speed
        this.targetScrollVelocity = Math.max(-4, Math.min(delta * 0.14, 10));
      }, { passive: true });

      window.addEventListener('mousemove', (e) => {
        this.mouse.x = e.clientX;
        this.mouse.y = e.clientY;
        this.mouse.active = true;
      }, { passive: true });

      window.addEventListener('mouseleave', () => {
        this.mouse.active = false;
      });
    }

    burst(x, y, count = 20) {
      for (let i = 0; i < count; i++) {
        const angle = Math.random() * Math.PI * 2;
        const speed = Math.random() * 4 + 1.5;
        this.particles.push({
          x: x,
          y: y,
          radius: Math.random() * 1.4 + 0.8,
          baseVy: 0.5,
          vx: Math.cos(angle) * speed,
          vy: Math.sin(angle) * speed - 1.5,
          color: { r: 227, g: 179, b: 65, a: 0.8 },
          baseAlpha: 0.8,
          temporary: true,
          life: 45
        });
      }
    }

    update(time) {
      // Smooth scroll velocity decay
      this.scrollVelocity += (this.targetScrollVelocity - this.scrollVelocity) * 0.15;
      this.targetScrollVelocity *= 0.92;

      this.ctx.clearRect(0, 0, this.width, this.height);

      for (let i = this.particles.length - 1; i >= 0; i--) {
        const p = this.particles[i];

        if (p.temporary) {
          p.life--;
          p.vx *= 0.94;
          p.vy += 0.15; // Gravity
          p.x += p.vx;
          p.y += p.vy;
          const alpha = (p.life / 45) * p.baseAlpha;
          this.ctx.beginPath();
          this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
          this.ctx.fillStyle = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${alpha})`;
          this.ctx.fill();

          if (p.life <= 0) {
            this.particles.splice(i, 1);
          }
          continue;
        }

        // Horizontal sway
        p.swayOffset += p.swaySpeed;
        const sway = Math.sin(p.swayOffset) * 0.25;

        // Downward kinetic velocity
        p.vy = p.baseVy + this.scrollVelocity;
        p.x += p.vx + sway;
        p.y += p.vy;

        // Gentle cursor magnetic repulsion
        if (this.mouse.active) {
          const dx = p.x - this.mouse.x;
          const dy = p.y - this.mouse.y;
          const dist = Math.hypot(dx, dy);
          const maxDist = 80;
          if (dist < maxDist && dist > 0) {
            const force = (maxDist - dist) / maxDist;
            p.x += (dx / dist) * force * 2.2;
            p.y += (dy / dist) * force * 2.2;
          }
        }

        // Screen wrap
        if (p.y > this.height + 5) {
          p.y = -5;
          p.x = Math.random() * this.width;
        } else if (p.y < -5) {
          p.y = this.height + 5;
          p.x = Math.random() * this.width;
        }
        if (p.x > this.width + 5) p.x = -5;
        else if (p.x < -5) p.x = this.width + 5;

        // Render grain
        this.ctx.beginPath();
        this.ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2);
        this.ctx.fillStyle = `rgba(${p.color.r}, ${p.color.g}, ${p.color.b}, ${p.baseAlpha})`;
        this.ctx.fill();
      }
    }
  }

  /* ==========================================================================
     2. Vector Hourglass HUD & Scroll Telemetry
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
          <canvas id="hourglassCanvas" width="72" height="104"></canvas>
        </div>
        <div class="hourglass-telemetry">
          <span class="hud-pct" id="hudPct">0%</span>
          <span class="hud-sub">${i18n.timeRemaining}</span>
        </div>
        <div class="hud-tooltip-card">${i18n.tooltip}</div>
      `;

      document.body.appendChild(this.hud);

      this.canvas = document.getElementById('hourglassCanvas');
      this.ctx = this.canvas.getContext('2d');
      this.pctEl = document.getElementById('hudPct');
      this.dpr = Math.min(window.devicePixelRatio || 1, 2);

      // Canvas dimensions (36x52 CSS points, scaled for Retina)
      this.cssW = 36;
      this.cssH = 52;
      this.canvas.width = this.cssW * this.dpr;
      this.canvas.height = this.cssH * this.dpr;
      this.canvas.style.width = `${this.cssW}px`;
      this.canvas.style.height = `${this.cssH}px`;
      this.ctx.scale(this.dpr, this.dpr);

      this.scrollProgress = 0;
      this.targetProgress = 0;
      this.fallingGrains = [
        { y: 0.1, speed: 0.045 },
        { y: 0.35, speed: 0.055 },
        { y: 0.65, speed: 0.05 },
        { y: 0.9, speed: 0.06 }
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

      // Click to invert time & scroll to top
      const triggerFlip = () => {
        if (this.isFlipping) return;
        this.isFlipping = true;
        this.hud.classList.add('flipping');

        // Particle burst
        const rect = this.hud.getBoundingClientRect();
        this.sandParticles.burst(rect.left + rect.width / 2, rect.top + rect.height / 2, 25);

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
      // Smooth interpolation for fluid liquid-sand feel
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

      // Coordinates
      const cx = w / 2;
      const topPlateY = 4;
      const botPlateY = h - 4;
      const bulbW = 13.5;
      const waistY = h / 2;
      const waistHalfW = 2.4;
      const coneTopY = topPlateY + 3;
      const coneBotY = botPlateY - 3;

      // Color interpolation: Gold -> Tomato Red as deadline approaches
      const isUrgent = p > 0.72;
      const urgentFactor = Math.max(0, Math.min((p - 0.72) / 0.28, 1));
      const sandR = Math.round(227 + (255 - 227) * urgentFactor);
      const sandG = Math.round(179 + (82 - 179) * urgentFactor);
      const sandB = Math.round(65 + (82 - 65) * urgentFactor);
      const sandColor = `rgb(${sandR}, ${sandG}, ${sandB})`;
      const sandColorAlpha = (a) => `rgba(${sandR}, ${sandG}, ${sandB}, ${a})`;

      /* ---------------- Top Sand Bulb ---------------- */
      const topRemaining = Math.max(0, 1 - p);
      if (topRemaining > 0.01) {
        // Sand surface in top cone
        const topH = (waistY - coneTopY);
        const surfY = coneTopY + (1 - topRemaining) * topH;
        const surfRatio = (waistY - surfY) / topH;
        const surfHalfW = waistHalfW + (bulbW - waistHalfW) * surfRatio;

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

      /* ---------------- Bottom Sand Bulb ---------------- */
      const botFilled = Math.min(1, p);
      if (botFilled > 0.005) {
        const botH = (coneBotY - waistY);
        const pileHeight = botFilled * botH;
        const surfY = coneBotY - pileHeight;
        const surfRatio = pileHeight / botH;
        const surfHalfW = bulbW - (bulbW - waistHalfW) * surfRatio;
        const peak = botFilled < 0.95 ? 2.2 : 0.5;

        ctx.save();
        ctx.beginPath();
        ctx.moveTo(cx - surfHalfW, coneBotY - (1 - surfRatio) * 0); // bottom left
        ctx.lineTo(cx - surfHalfW, surfY);
        // Sand dune conical curve
        ctx.quadraticCurveTo(cx, surfY - peak, cx + surfHalfW, surfY);
        ctx.lineTo(cx + bulbW, coneBotY);
        ctx.lineTo(cx - bulbW, coneBotY);
        ctx.closePath();

        const botGrad = ctx.createLinearGradient(0, surfY - peak, 0, coneBotY);
        botGrad.addColorStop(0, sandColorAlpha(0.95));
        botGrad.addColorStop(1, sandColorAlpha(0.7));
        ctx.fillStyle = botGrad;
        ctx.fill();
        ctx.restore();
      }

      /* ---------------- Falling Trickle Stream ---------------- */
      if (topRemaining > 0.01) {
        const botH = (coneBotY - waistY);
        const pileHeight = botFilled * botH;
        const targetY = coneBotY - pileHeight;

        // Continuous thin stream line
        ctx.beginPath();
        ctx.moveTo(cx, waistY);
        ctx.lineTo(cx, targetY);
        ctx.strokeStyle = sandColorAlpha(0.65);
        ctx.lineWidth = 1.1;
        ctx.stroke();

        // Animated falling micro-grains
        ctx.fillStyle = sandColorAlpha(0.95);
        for (let grain of this.fallingGrains) {
          grain.y += grain.speed;
          if (grain.y > 1) grain.y = 0;
          const gy = waistY + grain.y * (targetY - waistY);
          ctx.beginPath();
          ctx.arc(cx, gy, 0.75, 0, Math.PI * 2);
          ctx.fill();
        }

        // Dune impact splash sparks
        if (Math.random() < 0.45 && targetY > waistY) {
          this.splashParticles.push({
            x: cx,
            y: targetY,
            vx: (Math.random() - 0.5) * 1.2,
            vy: -Math.random() * 1.1 - 0.4,
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
        ctx.arc(sp.x, sp.y, 0.6, 0, Math.PI * 2);
        ctx.fillStyle = sp.color;
        ctx.fill();
        if (sp.life <= 0) this.splashParticles.splice(i, 1);
      }

      /* ---------------- Glass Architecture (Hairline Vectors) ---------------- */
      ctx.save();

      // Top and bottom cap plates
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.4)';
      ctx.lineWidth = 1.5;
      ctx.lineCap = 'round';

      ctx.beginPath();
      ctx.moveTo(cx - bulbW - 2, topPlateY);
      ctx.lineTo(cx + bulbW + 2, topPlateY);
      ctx.stroke();

      ctx.beginPath();
      ctx.moveTo(cx - bulbW - 2, botPlateY);
      ctx.lineTo(cx + bulbW + 2, botPlateY);
      ctx.stroke();

      // Conical glass contours
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.2)';
      ctx.lineWidth = 1.2;
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
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.35)';
      ctx.lineWidth = 1;
      ctx.beginPath();
      ctx.moveTo(cx - bulbW + 1.5, coneTopY + 2);
      ctx.lineTo(cx - waistHalfW - 1, waistY - 3);
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
