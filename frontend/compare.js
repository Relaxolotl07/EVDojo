(() => {
  // Shared compare loader for expert.html and admin.html
  function setup(prefix) {
    const topicEl = document.getElementById(prefix + 'Topic') || document.getElementById('topic');
    const raterEl = document.getElementById(prefix + 'Id') || document.getElementById('rater');
    const loadBtn = document.getElementById(prefix + 'Load') || document.getElementById('load');
    const wrap = document.getElementById(prefix + 'Pair') || document.getElementById('pair');
    const aSub = document.getElementById(prefix + 'ASubject') || document.getElementById('aSubject');
    const aBody = document.getElementById(prefix + 'ABody') || document.getElementById('aBody');
    const bSub = document.getElementById(prefix + 'BSubject') || document.getElementById('bSubject');
    const bBody = document.getElementById(prefix + 'BBody') || document.getElementById('bBody');
    const goal = document.getElementById(prefix + 'Goal') || document.getElementById('goal');
    const pickA = document.getElementById(prefix + 'PickA') || document.getElementById('pickA');
    const pickB = document.getElementById(prefix + 'PickB') || document.getElementById('pickB');
    const abstain = document.getElementById(prefix + 'Abstain') || document.getElementById('abstain');
    const reasonEl = document.getElementById(prefix + 'Reason');
    const barEl = document.getElementById(prefix + 'Bar');
    const chipsEl = document.getElementById(prefix + 'Chips');

    let queue = [];
    let idx = 0;

    function setProgress() {
      if (!barEl) return;
      const total = queue.length || 1;
      const pct = Math.min(100, Math.round((idx / total) * 100));
      barEl.style.width = pct + '%';
    }

    function renderChips() {
      if (!chipsEl) return;
      const TAGS = ["clearer ask","shorter","less pressure","friendlier","too vague","too long"];
      chipsEl.innerHTML = '';
      TAGS.forEach(tag => {
        const c = document.createElement('div');
        c.className = 'chip'; c.textContent = tag;
        c.onclick = () => c.classList.toggle('active');
        chipsEl.appendChild(c);
      });
    }

    function collectTags() {
      if (chipsEl) {
        return Array.from(chipsEl.querySelectorAll('.chip.active')).map(n => n.textContent.trim()).filter(Boolean);
      }
      if (reasonEl) {
        return (reasonEl.value ? reasonEl.value.split(',').map(s=>s.trim()).filter(Boolean) : []);
      }
      return [];
    }

    function show(i) {
      const p = queue[i];
      if (!p) { wrap.style.display='none'; return; }
      wrap.style.display='block';
      goal.textContent = p.context?.goal || '';
      aSub.textContent = redact(p.a.subject);
      bSub.textContent = redact(p.b.subject);
      aBody.textContent = redact(p.a.body);
      bBody.textContent = redact(p.b.body);
      setProgress();
      renderChips();
    }

    async function label(winner) {
      const p = queue[idx]; if (!p) return;
      const idem = (crypto && crypto.randomUUID) ? crypto.randomUUID() : (Date.now()+''+Math.random());
      const payload = { pair_id: p.pair_id, winner, tags: collectTags(), rater_id: raterEl ? raterEl.value : 'expert_ui', confidence: 0.9 };
      if (p.pair_id !== 'DEMO') {
        await fetch('/expert/label', { method: 'POST', headers: { 'Content-Type': 'application/json', 'Idempotency-Key': idem }, body: JSON.stringify(payload) });
      }
      idx += 1; show(idx);
    }

    loadBtn.addEventListener('click', async () => {
      const topic = topicEl.value || 'internal-request';
      queue = await api.get(`/expert/queue?topic=${encodeURIComponent(topic)}&limit=50`);
      // If debug mode and empty queue, provide a demo pair
      try {
        const dbg = await api.get('/debug/status');
        if ((dbg && dbg.debug) && (!queue || queue.length === 0)) {
          queue = [{ pair_id: 'DEMO', item_id: 'demo_item', a: { variant_id: 'va', subject: 'A: Meeting', body: 'Hey, maybe we could meet later?' }, b: { variant_id: 'vb', subject: 'B: Meeting', body: 'Are you free tomorrow at 3 pm at the cafe?' }, context: { goal: topic } }];
        }
      } catch {}
      idx = 0; show(idx);
    });
    pickA.addEventListener('click', () => label('A'));
    pickB.addEventListener('click', () => label('B'));
    abstain.addEventListener('click', () => label('ABSTAIN'));
  }

  // Expert
  if (document.getElementById('load')) setup('');
  // Admin
  if (document.getElementById('adminLoad')) setup('admin');
})();
