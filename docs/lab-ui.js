(() => {
  const escapeHtml = (value) => String(value ?? '').replace(/[&<>"']/g, ch => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
  let map = {};
  const ready = fetch('./data/paper_titles_zh.json', { cache: 'no-store' })
    .then(response => response.ok ? response.json() : {})
    .then(payload => { map = payload && payload.papers && typeof payload.papers === 'object' ? payload.papers : {}; return map; })
    .catch(() => map);
  const progressReady = fetch('./data/project_status.json', { cache: 'no-store' })
    .then(response => response.ok ? response.json() : {})
    .then(status => {
      const values = status && typeof status === 'object' ? status : {};
      const asOf = values.as_of;
      const papers = values.papers;
      const rows = values.dataset_rows;
      if (!/^\d{4}-\d{2}-\d{2}$/.test(asOf || '') || !Number.isSafeInteger(papers) || papers < 0 || !Number.isSafeInteger(rows) || rows < 0) return {};
      const paint = () => document.querySelectorAll('[data-project-progress]').forEach(node => {
        node.textContent = `项目更新 ${asOf} · ${papers} 篇论文 · ${rows} 条问答数据 · 本版未重新训练模型`;
      });
      if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', paint, { once: true });
      else paint();
      return values;
    }).catch(() => ({}));
  const titleZh = (paperOrId, englishTitle) => {
    const id = typeof paperOrId === 'object' ? paperOrId?.id : paperOrId;
    const paper = typeof paperOrId === 'object' ? paperOrId : null;
    const row = Object.prototype.hasOwnProperty.call(map, id) ? map[id] : {};
    const canonical = paper?.title || englishTitle;
    if (canonical && row.title !== canonical) return '';
    return typeof row.title_zh === 'string' ? row.title_zh : '';
  };
  const paperTitleHtml = (paperOrId, englishTitle) => {
    const paper = paperOrId && typeof paperOrId === 'object' ? paperOrId : { id: paperOrId, title: englishTitle };
    const english = paper.title || englishTitle || '';
    const zh = titleZh(paper);
    return `<span class="paper-title-en">${escapeHtml(english)}</span>${zh ? `<span class="paper-title-zh" lang="zh-CN">${escapeHtml(zh)}</span>` : ''}`;
  };
  const metadata = (paperOrId) => {
    const id = typeof paperOrId === 'object' ? paperOrId?.id : paperOrId;
    return map[id] || {};
  };
  window.LabUI = { ready, progressReady, escapeHtml, titleZh, paperTitleHtml, metadata, get titles() { return map; } };
  window.labUIReady = ready;
})();
