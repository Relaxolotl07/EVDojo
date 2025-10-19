// Decorative constellation background
(() => {
  const container = document.querySelector('.bg-decor');
  if(!container) return;
  const canvas = container.querySelector('.bg-constellation');
  if(!canvas) return;
  const ctx = canvas.getContext('2d');
  let dpr = Math.max(1, Math.min(1.5, window.devicePixelRatio || 1));
  let width = 0, height = 0;

  function resize(){
    width = container.clientWidth;
    height = container.clientHeight;
    canvas.width = Math.floor(width * dpr);
    canvas.height = Math.floor(height * dpr);
    canvas.style.width = width + 'px';
    canvas.style.height = height + 'px';
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  const STAR_BASE = 90;
  let STAR_COUNT = STAR_BASE;
  let MAX_LINK = 130; // px
  const SPEED = 0.06;   // px/ms

  const stars = [];
  function init(){
    stars.length = 0;
    for(let i=0;i<STAR_COUNT;i++){
      stars.push({
        x: Math.random()*width,
        y: Math.random()*height,
        vx: (Math.random()*2-1) * SPEED,
        vy: (Math.random()*2-1) * SPEED,
        r: Math.random()*1.8 + 0.6,
        tw: Math.random()*0.5 + 0.5,
      });
    }
  }

  function step(dt){
    for(const s of stars){
      s.x += s.vx * dt;
      s.y += s.vy * dt;
      if(s.x < -10) s.x = width+10; else if(s.x > width+10) s.x = -10;
      if(s.y < -10) s.y = height+10; else if(s.y > height+10) s.y = -10;
    }
  }

  function draw(){
    ctx.clearRect(0,0,width,height);
    // stars
    for(let i=0;i<stars.length;i+= (scrolling || lowFps ? 2 : 1)){
      const s = stars[i];
      const alpha = 0.6 + 0.4*Math.sin(performance.now()*0.002*s.tw);
      ctx.beginPath();
      ctx.fillStyle = `rgba(255,255,255,${0.55*alpha})`;
      ctx.arc(s.x, s.y, s.r, 0, Math.PI*2);
      ctx.fill();
    }
    // links
    if(!(scrolling || lowFps)){
      for(let i=0;i<stars.length;i++){
        for(let j=i+1;j<stars.length;j++){
          const a = stars[i], b = stars[j];
          const dx = a.x-b.x, dy = a.y-b.y;
          const d = Math.hypot(dx,dy);
          if(d < MAX_LINK){
            const t = 1 - d / MAX_LINK;
            ctx.beginPath();
            ctx.strokeStyle = `rgba(200, 210, 255, ${0.25*t})`;
            ctx.lineWidth = 1;
            ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
            ctx.stroke();
          }
        }
      }
    }
  }

  let last = performance.now();
  let fpsEMA = 60;
  let lowFps = false;
  let scrolling = false;
  function loop(){
    const now = performance.now();
    const dt = now - last; last = now;
    step(dt);
    draw();
    // FPS adaptive quality
    const fps = 1000 / Math.max(1, dt);
    fpsEMA = fpsEMA*0.9 + fps*0.1;
    lowFps = fpsEMA < 40;
    if(lowFps){
      MAX_LINK = 100;
      STAR_COUNT = Math.max(50, Math.floor(STAR_BASE*0.75));
    } else {
      MAX_LINK = 130;
      STAR_COUNT = STAR_BASE;
    }
    requestAnimationFrame(loop);
  }

  const ro = new ResizeObserver(() => { resize(); init(); });
  ro.observe(container);
  resize();
  init();
  // Pause when not visible
  let running = true;
  function start(){ if(!running){ running=true; last=performance.now(); requestAnimationFrame(loop); } }
  function stop(){ running=false; }
  document.addEventListener('visibilitychange', () => {
    if(document.visibilityState === 'hidden'){ stop(); }
    else { start(); }
  });
  // Scroll throttle
  let scrollTO = null;
  window.addEventListener('scroll', () => {
    scrolling = true;
    document.body.classList.add('perf-throttle');
    clearTimeout(scrollTO);
    scrollTO = setTimeout(() => { scrolling = false; document.body.classList.remove('perf-throttle'); }, 250);
  }, { passive: true });
  loop();
})();
