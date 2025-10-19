(() => {
  const sel = document.getElementById('topicSel');
  const go = document.getElementById('goBtn');
  api.get('/topics').then(d => {
    (d.topics || ['internal-request','customer-support','networking','ask-out']).forEach(t => {
      const o = document.createElement('option'); o.value = t; o.textContent = t; sel.appendChild(o);
    });
  });
  go.addEventListener('click', () => {
    const t = sel.value || 'internal-request';
    location.href = `/user-feedback.html?topic=${encodeURIComponent(t)}`;
  });
})();

