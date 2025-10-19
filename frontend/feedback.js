(() => {
  const els = {
    topicName: document.getElementById('topicName'),
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
    rank: document.getElementById('rank'),
    debugBanner: document.getElementById('debugBanner'),
    debugHint: document.getElementById('debugHint'),
  };

  const topic = qs('topic') || 'internal-request';
  els.topicName.textContent = topic;

  let itemId = null;
  let lastAlert = 0;
  const MODE_TO_COOLDOWN = { off: 1e12, light: 6000, standard: 8000, intense: 3000 };
  const DEBOUNCE_MS = 450;
  let debounceTimer = null;
  let debugInfo = null;

  function setMeter(state, tagText) {
    els.meter.classList.remove('good', 'bad', 'debug');
    if (debugInfo && debugInfo.debug) els.meter.classList.add('debug');
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

  async function createItem() {
    const goal = topic;
    const user = 'u_local';
    const text = els.editor.value || '';
    const resp = await api.post('/items', { user_id: user, modality: 'text', content: { text }, context: { goal } });
    itemId = resp.item_id;
    els.sessionInfo.textContent = `item_id=${itemId}`;
  }

  async function refreshRank() {
    if (!itemId) return;
    const data = await api.get(`/rank?item_id=${encodeURIComponent(itemId)}`);
    const list = (data.ranking || []).map((e, i) => `#${i + 1} · ${e.variant_id} · score=${e.score.toFixed(3)} ±${e.stderr.toFixed(3)}`).join('<br />');
    els.rank.innerHTML = list || '<span class="muted">No variants yet</span>';
  }

  async function streamScore() {
    if (!itemId || els.mode.value === 'off') return;
    const cooldown = MODE_TO_COOLDOWN[els.mode.value] || 8000;
    if (Date.now() - lastAlert < cooldown) return;
    const snippet = els.editor.value; if (!snippet.trim()) return;
    const resp = await api.post('/rm/stream/score', {
      modality: 'text', context: { goal: topic }, snippet,
      cursor: { pos: els.editor.selectionStart || snippet.length }, rm_version: 'v1', user_id: 'u_local', item_id: itemId, mode: els.mode.value,
    });
    setMeter(resp.state, (resp.tags && resp.tags[0]) || '');
    els.spans.innerHTML = '';
    (resp.spans || []).forEach(s => { const chip = document.createElement('span'); chip.className='span-chip'; chip.textContent=`${s.tag} [${s.start},${s.end}]`; els.spans.appendChild(chip); });
    if (resp.state === 'negative' && resp.suggestion) {
      els.suggestionLabel.textContent = resp.suggestion.label || 'Apply suggestion';
      els.suggestion.classList.remove('hidden');
      lastAlert = Date.now();
      els.applySuggestion.onclick = async () => {
        const patch = resp.suggestion.patch;
        if (patch && patch.type === 'text_replace') { els.editor.value = patch.text; }
        const diffType = resp.suggestion.label && resp.suggestion.label.toLowerCase().includes('hedge') ? 'remove_hedges' : 'add_concrete_ask';
        await api.post(`/variants/apply_suggestion?item_id=${encodeURIComponent(itemId)}&diff_type=${encodeURIComponent(diffType)}&content_text=${encodeURIComponent(els.editor.value)}`, {});
        els.suggestion.classList.add('hidden');
        refreshRank();
      };
      els.dismissSuggestion.onclick = () => els.suggestion.classList.add('hidden');
    }
  }

  (async () => {
    try {
      debugInfo = await api.get('/debug/status');
      if (debugInfo && debugInfo.debug) {
        els.debugBanner.classList.remove('hidden');
        els.debugHint.classList.remove('hidden');
      }
    } catch {}
  })();

  els.startBtn.addEventListener('click', createItem);
  els.editor.addEventListener('input', () => { if (debounceTimer) clearTimeout(debounceTimer); debounceTimer = setTimeout(streamScore, 450); });
})();

