(() => {
  const api = {
    post: (url, body) => fetch(url, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) }).then(r => r.json()),
    get: (url) => fetch(url).then(r => r.json()),
  };

  const els = {
    goal: document.getElementById('goal'),
    userId: document.getElementById('userId'),
    startBtn: document.getElementById('startBtn'),
    sessionInfo: document.getElementById('sessionInfo'),
    mode: document.getElementById('mode'),
    editor: document.getElementById('editor'),
    meter: document.getElementById('meter'),
    suggestion: document.getElementById('suggestion'),
    suggestionLabel: document.getElementById('suggestionLabel'),
    applySuggestion: document.getElementById('applySuggestion'),
    dismissSuggestion: document.getElementById('dismissSuggestion'),
    spans: document.getElementById('spans'),
    genVariants: document.getElementById('genVariants'),
    refreshRank: document.getElementById('refreshRank'),
    rank: document.getElementById('rank'),
    debugBanner: document.getElementById('debugBanner'),
    debugHint: document.getElementById('debugHint'),
  };

  let itemId = null;
  let lastAlert = 0; // client-side soft cooldown (server also enforces)
  const MODE_TO_COOLDOWN = { off: 1e12, light: 6000, standard: 8000, intense: 3000 };
  const DEBOUNCE_MS = 450;
  let debounceTimer = null;

  let debugInfo = null;

  function setMeter(state, tagText) {
    els.meter.classList.remove('good', 'bad');
    if (debugInfo && debugInfo.debug) {
      els.meter.classList.add('debug');
    } else {
      els.meter.classList.remove('debug');
    }
    if (state === 'positive') {
      els.meter.textContent = `${debugInfo?.debug ? '[DEBUG] ' : ''}👍 Likely better${tagText ? ` · ${tagText}` : ''}`;
      els.meter.classList.add('good');
    } else if (state === 'negative') {
      els.meter.textContent = `${debugInfo?.debug ? '[DEBUG] ' : ''}⚠️ Likely worse${tagText ? ` · ${tagText}` : ''}`;
      els.meter.classList.add('bad');
    } else {
      els.meter.textContent = `${debugInfo?.debug ? '[DEBUG] ' : ''}Neutral`;
    }
  }

  function showSuggestion(label) {
    els.suggestionLabel.textContent = label;
    els.suggestion.classList.remove('hidden');
  }
  function hideSuggestion() {
    els.suggestion.classList.add('hidden');
  }

  async function createItem() {
    const goal = els.goal.value || 'ask clearly and respectfully';
    const user = els.userId.value || 'u_local';
    const text = els.editor.value || '';
    const resp = await api.post('/items', {
      user_id: user,
      modality: 'text',
      content: { text },
      context: { goal },
    });
    itemId = resp.item_id;
    els.sessionInfo.textContent = `item_id=${itemId}`;
  }

  async function streamScore() {
    if (!itemId || els.mode.value === 'off') return;
    const cooldown = MODE_TO_COOLDOWN[els.mode.value] || 8000;
    if (Date.now() - lastAlert < cooldown) return;

    const snippet = els.editor.value;
    if (!snippet || snippet.trim().length === 0) return;
    const goal = els.goal.value || '';
    const user = els.userId.value || 'u_local';
    const resp = await api.post('/rm/stream/score', {
      modality: 'text',
      context: { goal },
      snippet,
      cursor: { pos: els.editor.selectionStart || snippet.length },
      rm_version: 'v1',
      user_id: user,
      item_id: itemId,
      mode: els.mode.value,
    });

    // Update meter
    setMeter(resp.state, (resp.tags && resp.tags[0]) || '');
    // Spans visualization
    els.spans.innerHTML = '';
    if (Array.isArray(resp.spans)) {
      resp.spans.forEach(s => {
        const chip = document.createElement('span');
        chip.className = 'span-chip';
        chip.textContent = `${s.tag} [${s.start},${s.end}]`;
        els.spans.appendChild(chip);
      });
    }

    // Suggestion handling (only when backend emits a state)
    if (resp.state === 'negative' && resp.suggestion) {
      showSuggestion(resp.suggestion.label || 'Apply suggestion');
      lastAlert = Date.now();
      // Attach patch for apply
      els.applySuggestion.onclick = async () => {
        try {
          const patch = resp.suggestion.patch;
          if (patch && patch.type === 'text_replace') {
            els.editor.value = patch.text;
          }
          // Create variant to keep A/B lineage
          const diffType = resp.suggestion.label && resp.suggestion.label.toLowerCase().includes('hedge') ? 'remove_hedges' : 'add_concrete_ask';
          await api.post(`/variants/apply_suggestion?item_id=${encodeURIComponent(itemId)}&diff_type=${encodeURIComponent(diffType)}&content_text=${encodeURIComponent(els.editor.value)}`, {});
          hideSuggestion();
          await refreshRank();
        } catch (e) {
          console.error(e);
        }
      };
      els.dismissSuggestion.onclick = () => hideSuggestion();
    }
  }

  async function generateVariants() {
    if (!itemId) await createItem();
    await api.post('/variants', { item_id: itemId });
    await refreshRank();
  }

  async function refreshRank() {
    if (!itemId) return;
    const data = await api.get(`/rank?item_id=${encodeURIComponent(itemId)}`);
    const list = (data.ranking || []).map((e, i) => `#${i + 1} · ${e.variant_id} · score=${e.score.toFixed(3)} ±${e.stderr.toFixed(3)}`).join('<br />');
    els.rank.innerHTML = list || '<span class="muted">No variants yet</span>';
  }

  // Events
  (async () => {
    try {
      debugInfo = await api.get('/debug/status');
      if (debugInfo && debugInfo.debug) {
        els.debugBanner.classList.remove('hidden');
        els.debugHint.classList.remove('hidden');
        if (!els.goal.value) {
          els.goal.value = debugInfo.fixed_goal || els.goal.value;
        }
      }
    } catch (e) { /* ignore */ }
  })();

  els.startBtn.addEventListener('click', createItem);
  els.genVariants.addEventListener('click', generateVariants);
  els.refreshRank.addEventListener('click', refreshRank);
  els.editor.addEventListener('input', () => {
    if (debounceTimer) clearTimeout(debounceTimer);
    debounceTimer = setTimeout(streamScore, DEBOUNCE_MS);
  });
})();
