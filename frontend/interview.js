(() => {
  const vid = document.getElementById('vid');
  const overlay = document.getElementById('overlay');
  const ctx = overlay.getContext('2d', { willReadFrequently: true });
  const indicator = document.getElementById('indicator');
  const btnSample = document.getElementById('useSample');
  const btnWebcam = document.getElementById('useWebcam');
  const btnToggle = document.getElementById('toggleDebug');
  const debugPanel = document.getElementById('debugPanel');
  const modeSel = document.getElementById('modeSel');
  const showOverlay = document.getElementById('showOverlay');

  let running = false;
  let detector = null;
  let faceMesh = null;
  let mode = 'motion';
  let meshErrorCount = 0;
  let lastNoseY = null;
  let lastY = null;
  let streak = 0;
  const THRESH = 8; // pixels of vertical movement for nod
  let debug = false;
  let lastTime = performance.now();
  let fps = 0;
  // Debug helpers
  let lastDebugTs = 0;
  let lastIndicator = '';
  function dbg(label, data) {
    if (!debug) return;
    const now = performance.now();
    if (now - lastDebugTs > 300) {
      try { console.log('[interview]', label, data); } catch {}
      lastDebugTs = now;
    }
  }
  // ROI selection state
  let roi = null; // {x,y,w,h}
  let dragging = false;
  let dragStart = null;

  function resizeCanvasToVideo() {
    if (vid.videoWidth && vid.videoHeight) {
      overlay.width = vid.videoWidth;
      overlay.height = vid.videoHeight;
    }
  }

  async function ensureDetector() {
    // Prefer MediaPipe FaceMesh if available
    if (window.FaceMesh && (modeSel.value === 'auto')) {
      faceMesh = new window.FaceMesh({ locateFile: (f) => `https://cdn.jsdelivr.net/npm/@mediapipe/face_mesh/${f}` });
      faceMesh.setOptions({ maxNumFaces: 1, refineLandmarks: true, minDetectionConfidence: 0.6, minTrackingConfidence: 0.6, selfieMode: true });
      faceMesh.onResults(onFaceMeshResults);
      detector = null;
      mode = 'facemesh'; dbg('ensureDetector', { mode });
      return;
    }
    if ('FaceDetector' in window && (modeSel.value === 'auto' || modeSel.value === 'facedetector')) {
      detector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 1 });
      faceMesh = null;
      mode = 'facedetector'; dbg('ensureDetector', { mode });
    } else {
      detector = null; // fallback to motion
      faceMesh = null;
      mode = 'motion'; dbg('ensureDetector', { mode });
    }
  }

  function fallbackToFaceDetector() {
    try {
      if ('FaceDetector' in window) {
        detector = new window.FaceDetector({ fastMode: true, maxDetectedFaces: 1 });
        faceMesh = null; mode = 'facedetector';
      } else {
        detector = null; faceMesh = null; mode = 'motion';
      }
    } catch {
      detector = null; faceMesh = null; mode = 'motion';
    }
  }

  function mouthMetrics(landmarks, w, h, faceBox) {
    // MediaPipe landmark indices: 13 (upper lip), 14 (lower lip), 61 (left corner), 291 (right corner)
    const l = landmarks;
    const up = l[13], low = l[14], lc = l[61], rc = l[291];
    if (!up || !low || !lc || !rc) return { open: 0, smile: 0 };
    const fy = (faceBox.maxY - faceBox.minY) * h;
    const fx = (faceBox.maxX - faceBox.minX) * w;
    const open = Math.abs((low.y - up.y)) * h / Math.max(1, fy);
    const smile = Math.hypot((rc.x - lc.x) * w, (rc.y - lc.y) * h) / Math.max(1, fx);
    return { open, smile };
  }

  function computeFaceBox(landmarks) {
    let minX=1, minY=1, maxX=0, maxY=0;
    for (const p of landmarks) { if (!p) continue; minX = Math.min(minX, p.x); maxX = Math.max(maxX, p.x); minY = Math.min(minY, p.y); maxY = Math.max(maxY, p.y); }
    return { minX, minY, maxX, maxY };
  }

  function onFaceMeshResults(res) {
    const w = overlay.width, h = overlay.height;
    ctx.clearRect(0, 0, w, h);
    // draw underlay frame for visualization
    ctx.drawImage(vid, 0, 0, w, h);
    const faces = res.multiFaceLandmarks;
    if (!faces || !faces[0]) {
      setIndicator('No face', false);
      lastNoseY = null; streak = 0;
      if (debug) { debugPanel.textContent = `mode=${mode} none fps=${fps.toFixed(1)} vw=${vid.videoWidth} vh=${vid.videoHeight}`; }
      dbg('facemesh:no-face', { vw: vid.videoWidth, vh: vid.videoHeight });
      return;
    }
    const lm = faces[0];
    // draw a few landmarks
    ctx.strokeStyle = 'rgba(183,110,121,0.9)';
    ctx.lineWidth = 2;
    const box = computeFaceBox(lm);
    ctx.strokeRect(box.minX*w, box.minY*h, (box.maxX-box.minX)*w, (box.maxY-box.minY)*h);

    const nose = lm[1] || lm[4];
    if (nose) {
      const y = nose.y * h;
      if (lastNoseY != null) {
        const dy = y - lastNoseY;
        if (Math.abs(dy) > THRESH) streak += 1; else streak = Math.max(0, streak - 1);
      }
      lastNoseY = y;
    }

    const mm = mouthMetrics(lm, w, h, box);
    const nod = streak >= 2;
    const mouthOpen = mm.open > 0.085; // tuned threshold
    const smile = mm.smile > 0.42;     // tuned threshold
    const states = [];
    if (nod) states.push('Nod');
    if (smile) states.push('Smile');
    if (mouthOpen) states.push('Mouth open');
    if (states.length) setIndicator(`Action: ${states.join(' | ')}`, true); else setIndicator('Tracking…', false);
    if (debug) {
      debugPanel.classList.remove('hidden');
      debugPanel.textContent = `mode=${mode} open=${mm.open.toFixed(3)} smile=${mm.smile.toFixed(3)} streak=${streak} fps=${fps.toFixed(1)}`;
    }
  }

  function setIndicator(text, on) {
    try { if (text !== lastIndicator) { dbg('indicator', { text, on }); lastIndicator = text; } } catch {}
    indicator.textContent = text;
    indicator.classList.toggle('positive', !!on);
  }

  async function analyze() {
    if (!running) return;
    try {
      resizeCanvasToVideo();
      const w = overlay.width;
      const h = overlay.height;
      dbg('frame', { mode, readyState: vid.readyState, vw: vid.videoWidth, vh: vid.videoHeight, fps: +fps.toFixed(1) });
      if (faceMesh) {
        // Only send frames when video has a valid size
        if (vid.readyState >= 2 && vid.videoWidth > 0 && vid.videoHeight > 0) {
          try {
            await faceMesh.send({ image: vid });
          } catch (e) {
            // Ignore transient MediaPipe ROI errors and continue
            if (debug) {
              debugPanel.classList.remove('hidden');
              debugPanel.textContent = `mode=${mode} error sending frame: ${e?.message || e}`;
            }
            meshErrorCount++;
            if (meshErrorCount >= 2) {
              // fall back to FaceDetector / motion to avoid repeated aborts
              fallbackToFaceDetector();
            }
          }
        } else {
          setIndicator('Loading video…', false);
        }
      } else if (detector) {
        ctx.drawImage(vid, 0, 0, w, h);
        // Use the video element directly for detection for better reliability
        const faces = await detector.detect(vid);
        if (faces && faces[0]) {
          const box = faces[0].boundingBox;
          // draw box mapped to canvas dimensions (video is same aspect)
          ctx.strokeStyle = 'rgba(183,110,121,0.9)';
          ctx.lineWidth = 2;
          ctx.strokeRect(box.x, box.y, box.width, box.height);
          dbg('facedetector:box', { x: box.x, y: box.y, w: box.width, h: box.height });
          const y = box.y + box.height / 2;
          if (lastY != null) {
            const dy = y - lastY;
            if (Math.abs(dy) > THRESH) {
              streak += 1;
            } else {
              streak = Math.max(0, streak - 1);
            }
            if (streak >= 2) {
              setIndicator('Action: Nod detected', true);
            } else {
              setIndicator('Tracking…', false);
            }
            if (debug) {
              debugPanel.classList.remove('hidden');
              debugPanel.textContent = `mode=face dy=${(y-lastY).toFixed(1)} streak=${streak} fps=${fps.toFixed(1)} box=(${Math.round(box.x)},${Math.round(box.y)}) ${Math.round(box.width)}x${Math.round(box.height)}`;
            }
          }
          lastY = y;
        } else {
          setIndicator('No face', false);
          lastY = null; streak = 0;
          if (debug) { debugPanel.textContent = `mode=face none fps=${fps.toFixed(1)}`; }
        }
      } else {
        // Simple motion fallback: average absolute difference between frames
        ctx.drawImage(vid, 0, 0, w, h);
        const img = ctx.getImageData(0, 0, w, h).data;
        if (!analyze.prev) analyze.prev = new Uint8ClampedArray(img);
        let diff = 0, n = img.length;
        // downsample by stepping pixels to speed up, use luma approximation
        for (let i = 0; i < n; i += 16) {
          const dr = img[i] - analyze.prev[i];
          const dg = img[i+1] - analyze.prev[i+1];
          const db = img[i+2] - analyze.prev[i+2];
          diff += Math.abs(0.299*dr + 0.587*dg + 0.114*db);
        }
        const avg = diff / (n/16);
        if (avg > 12) { setIndicator('Action: Movement', true); } else { setIndicator('Tracking…', false); }
        analyze.prev.set(img);
        if (debug) { debugPanel.classList.remove('hidden'); debugPanel.textContent = `mode=${mode} avg=${avg.toFixed(2)} fps=${fps.toFixed(1)}`; }

        // Compute center-of-motion within ROI (for nod) and draw ROI if any
        const r = roi || { x: Math.round(w*0.3), y: Math.round(h*0.2), w: Math.round(w*0.4), h: Math.round(h*0.6) };
        if (!roi && showOverlay && showOverlay.checked) {
          // hint default ROI
          ctx.strokeStyle = 'rgba(183,110,121,0.6)'; ctx.lineWidth = 2; ctx.strokeRect(r.x,r.y,r.w,r.h);
        }
        let sumY = 0, sumX = 0, sumW = 0;
        for (let yy = r.y|0; yy < (r.y + r.h)|0; yy += 4) {
          for (let xx = r.x|0; xx < (r.x + r.w)|0; xx += 4) {
            const idx = (yy*w + xx)*4;
            const dr = img[idx] - analyze.prev[idx];
            const dg = img[idx+1] - analyze.prev[idx+1];
            const db = img[idx+2] - analyze.prev[idx+2];
            const l = Math.abs(0.299*dr + 0.587*dg + 0.114*db);
            if (l > 12) { sumY += yy*l; sumX += xx*l; sumW += l; }
          }
        }
        if (sumW > 0) {
          const cy = sumY / sumW; const cx = sumX / sumW;
          if (lastY != null) {
            const dy = cy - lastY;
            if (Math.abs(dy) > 8) { streak += 1; } else { streak = Math.max(0, streak - 1); }
          }
          lastY = cy;
          if (showOverlay && showOverlay.checked) { ctx.fillStyle = 'rgba(183,110,121,0.35)'; ctx.beginPath(); ctx.arc(cx, cy, 6, 0, Math.PI*2); ctx.fill(); }
          if (streak >= 2) setIndicator('Action: Nod detected', true);
          dbg('motion:centroid', { cx: +cx.toFixed(1), cy: +cy.toFixed(1), streak });
        }
      }
    } catch (e) {
      // ignore per-frame errors
    }
    const now = performance.now();
    const dt = now - lastTime; lastTime = now; fps = 1000/dt;
    requestAnimationFrame(analyze);
  }

  async function useSample() {
    try {
      // Expect a local sample file placed at /sample.mp4
      vid.src = '/sample.mp4';
      await vid.play().catch(()=>{});
      running = true; requestAnimationFrame(analyze);
    } catch {}
  }

  async function useWebcam() {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: { width: 640, height: 360 } });
      vid.srcObject = stream;
      await vid.play();
      running = true; requestAnimationFrame(analyze);
    } catch (e) {
      setIndicator('Webcam blocked', false);
    }
  }

  btnSample.addEventListener('click', useSample);
  btnWebcam.addEventListener('click', useWebcam);
  btnToggle.addEventListener('click', () => { debug = !debug; if (!debug) debugPanel.classList.add('hidden'); });
  modeSel.addEventListener('change', async () => { await ensureDetector(); });
  // ROI drag selection on overlay
  overlay.addEventListener('mousedown', (e) => { dragging = true; dragStart = { x: e.offsetX, y: e.offsetY }; roi = { x: dragStart.x, y: dragStart.y, w: 0, h: 0 }; });
  overlay.addEventListener('mousemove', (e) => {
    if (!dragging) return;
    const x = Math.min(dragStart.x, e.offsetX);
    const y = Math.min(dragStart.y, e.offsetY);
    const wBox = Math.abs(e.offsetX - dragStart.x);
    const hBox = Math.abs(e.offsetY - dragStart.y);
    roi = { x, y, w: wBox, h: hBox };
  });
  overlay.addEventListener('mouseup', () => { dragging = false; });

  (async () => {
    await ensureDetector();
    vid.addEventListener('loadedmetadata', resizeCanvasToVideo);
    // Try sample first; if missing, fallback to webcam
    useSample();
    setTimeout(() => { if (!running) useWebcam(); }, 800);
  })();
})();
