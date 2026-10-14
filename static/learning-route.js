(() => {
  const cards = [...document.querySelectorAll('.stage-card, .frontier-card')];
  const search = document.querySelector('#route-search');
  const filter = document.querySelector('#stage-filter');
  const count = document.querySelector('#route-count');
  const empty = document.querySelector('#route-empty');
  const normalize = (value) => String(value || '').trim().toLocaleLowerCase();
  const conceptText = (card) => {
    const copy = card.cloneNode(true);
    copy.querySelectorAll('.paper-card, .reference-paper-card, .citations, .reference-groups, .frontier-card').forEach((node) => node.remove());
    return normalize(copy.textContent);
  };
  const paperMatch = (card, query) => [...card.querySelectorAll('.paper-card[data-search], .reference-paper-card[data-search]')].some((node) => normalize(node.dataset.search).includes(query));
  const ownStageMatch = (card, stage) => stage === 'all' || card.dataset.stage === stage || (stage === 'frontier' && Boolean(card.dataset.frontier));
  const matches = (card) => {
    const query = normalize(search.value);
    const stage = filter.value;
    if (!ownStageMatch(card, stage)) return false;
    if (!query) return true;
    if (conceptText(card).includes(query) || paperMatch(card, query)) return true;
    return [...card.querySelectorAll('.frontier-card')].some((child) => ownStageMatch(child, stage) && matches(child));
  };
  const refresh = () => {
    let visible = 0;
    cards.forEach((card) => { const show = matches(card); card.hidden = !show; if (show) visible += 1; });
    const allPaperNodes = [...document.querySelectorAll('.paper-card[data-paper-id]')];
    const query = normalize(search.value);
    const referenceNodes = [...document.querySelectorAll('.reference-paper-card[data-paper-id]')];
    [...allPaperNodes, ...referenceNodes].forEach((node) => { node.hidden = Boolean(query && !normalize(`${node.textContent} ${node.dataset.search}`).includes(query)); });
    document.querySelectorAll('.citations, .reference-group').forEach((section) => { section.hidden = ![...section.querySelectorAll('.paper-card, .reference-paper-card')].some((node) => !node.hidden); });
    const uniquePaperIds = new Set(allPaperNodes.map((node) => node.dataset.paperId));
    const visibleNodes = [...allPaperNodes, ...referenceNodes].filter((node) => !node.hidden && !node.closest('details[hidden]'));
    const visiblePaperIds = new Set(visibleNodes.map((node) => node.dataset.paperId));
    const visibleRefs = visibleNodes.length;
    const overlapRefs = allPaperNodes.length - uniquePaperIds.size;
    count.textContent = `显示 ${visible} / ${cards.length} 个路线分支 · 论文 ${visiblePaperIds.size}/${uniquePaperIds.size} 篇 · 匹配引用 ${visibleRefs} 条`;
    empty.hidden = visible !== 0;
  };
  const readHash = () => { const encoded = location.hash.slice(1); if (!encoded) return null; try { return decodeURIComponent(encoded); } catch (_) { return null; } };
  const openHashTarget = () => {
    const target = readHash();
    if (!target) return;
    search.value = ''; filter.value = 'all'; refresh();
    const node = document.getElementById(target);
    if (!node) return;
    let parent = node.closest('details');
    while (parent) { parent.open = true; parent = parent.parentElement?.closest('details'); }
    if (node.matches('details')) node.open = true;
    if (typeof node.focus === 'function') node.focus({ preventScroll: true });
    if (typeof node.scrollIntoView === 'function') node.scrollIntoView({ block: 'start' });
  };
  search.addEventListener('input', refresh);
  filter.addEventListener('change', refresh);
  document.querySelector('#expand-visible').addEventListener('click', () => {
    cards.forEach((card) => { if (!card.hidden) card.open = true; });
    document.querySelectorAll('.reference-group').forEach((group) => { if (!group.hidden && !group.closest('details[hidden]')) group.open = true; });
  });
  document.querySelector('#collapse-visible').addEventListener('click', () => {
    cards.forEach((card) => { if (!card.hidden) card.open = false; });
    document.querySelectorAll('.reference-group').forEach((group) => { if (!group.hidden) group.open = false; });
  });
  window.addEventListener('hashchange', openHashTarget);
  refresh();
  openHashTarget();
})();
