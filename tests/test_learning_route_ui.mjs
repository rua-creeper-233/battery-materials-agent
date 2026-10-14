import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const code = fs.readFileSync(new URL('../static/learning-route.js', import.meta.url), 'utf8');

function run({hash = '', query = ''} = {}) {
  const events = {};
  const controls = new Map();
  const stageCards = ['baseline', 'beginner', 'intermediate', 'frontier'].map((id) => {
    const c = {
      id: `stage-${id}`, dataset: {stage: id}, hidden: false, open: id === 'baseline',
      // In the generated page DOI/method/tag values are metadata (href/data-search),
      // not visible card text. Search must nevertheless index those values.
      textContent: id === 'beginner' ? 'Beginner route method' : id === 'baseline' ? 'baseline 10.1016/j.est.2026.121104' : id,
      matches(sel) { return sel === 'details'; }, closest(sel) { return sel === 'details' ? this.parentDetail ?? null : null; },
      querySelectorAll(sel) {
        if (sel === '[data-search]') return this.searchNodes ?? [];
        if (sel === '.frontier-card') return this.children ?? [];
        if (sel === '.paper-card[data-search]') return this.searchNodes?.length ? this.searchNodes : this.paperNodes ?? [];
        if (sel === '.paper-card') return this.paperNodes ?? [];
        return [];
      },
      cloneNode() { return {textContent: this.textContent, querySelectorAll() { return []; }}; },
      parentElement: null,
      focus() {},
      scrollIntoView() { this.scrolled = true; },
    };
    c.searchNodes = id === 'beginner' ? [{textContent: 'method', dataset: {search: 'doi10.1234 diffusion method tag'}}] : [];
    return c;
  });
  const paperNodes = Array.from({length: 176}, (_, i) => ({
    id: `paper-${i}`, dataset: {paperId: `paper-${i}`, search: i === 42 ? '10.1016/j.est.2026.121104 DFT method' : `paper-${i}`},
    textContent: i === 42 ? '10.1016/j.est.2026.121104' : `paper-${i}`, hidden: false,
    closest(sel) { if (sel === 'details[hidden]') return stageCards[0].hidden ? stageCards[0] : null; return sel === 'details' ? stageCards[0] : null; },
  }));
  paperNodes.push({...paperNodes[42], id: 'paper-42-overlap'});
  stageCards[0].paperNodes = paperNodes;
  const frontier = {id: 'frontier-mlip', dataset: {frontier: 'mlip_transport_and_sse'}, hidden: false, open: false,
    textContent: 'MLIP transport frontier', matches(sel) { return sel === 'details'; },
    closest(sel) { return sel === 'details' ? this.parentDetail ?? null : null; },
    querySelectorAll(sel) { return sel === '[data-search]' ? [] : []; }, parentElement: null,
    cloneNode() { return {textContent: this.textContent, querySelectorAll() { return []; }}; },
    focus() {}, scrollIntoView() { this.scrolled = true; }};
  const paper = {id: 'frontier-mlip-paper-x', dataset: {}, hidden: false, open: false,
    matches() { return false; }, closest(sel) { return sel === 'details' ? frontier : null; },
    querySelectorAll() { return []; }, parentElement: frontier,
    scrollIntoView() { this.scrolled = true; }};
  frontier.parentDetail = stageCards[3]; frontier.parentElement = {closest: (sel) => sel === 'details' ? stageCards[3] : null}; paper.parentDetail = frontier;
  stageCards[3].children = [frontier];
  const cards = [...stageCards, frontier];
  const byId = new Map([...cards, paper].map((c) => [c.id, c]));
  const make = (id, value = '') => {
    const el = {id, value, textContent: '', hidden: false, open: false, addEventListener(type, fn) { events[`${id}:${type}`] = fn; }};
    controls.set(`#${id}`, el); return el;
  };
  make('route-search', query); make('stage-filter', 'all');
  make('route-count'); make('route-empty'); make('expand-visible'); make('collapse-visible');
  const document = {
    querySelector(sel) { return controls.get(sel); },
    querySelectorAll(sel) {
      if (sel.includes('stage-card')) return cards;
      if (sel === '.paper-card[data-paper-id]') return paperNodes;
      if (sel === '.citations') return [];
      return [];
    },
    getElementById(id) { return byId.get(id) ?? null; },
  };
  const location = {hash};
  const window = {addEventListener(type, fn) { events[`window:${type}`] = fn; }};
  const context = vm.createContext({document, window, location, console, decodeURIComponent});
  vm.runInContext(code, context);
  return {cards, stageCards, frontier, paper, controls, events, location};
}

let t = run({query: 'method'});
assert.equal(t.cards.filter((c) => !c.hidden).length, 1, 'search finds method metadata');
assert.match(t.controls.get('#route-count').textContent, /显示 1 \/ 5/);
t = run({query: '10.1016/j.est.2026.121104'});
assert.equal(t.cards[0].paperNodes.filter((p) => !p.hidden).length, 2, 'overlapping DOI references remain visible');
assert.match(t.controls.get('#route-count').textContent, /论文 1\/176/);
t.controls.get('#route-search').value = ''; t.events['route-search:input']();
assert.equal(new Set(t.cards[0].paperNodes.filter((p) => !p.hidden).map((p) => p.dataset.paperId)).size, 176, 'clearing search restores every unique paper');
t = run();
t.controls.get('#route-search').value = 'method'; t.events['route-search:input']();
assert.equal(t.cards.filter((c) => !c.hidden).length, 1, 'method search indexes generated metadata');
t.controls.get('#route-search').value = ''; t.events['route-search:input']();
t.controls.get('#stage-filter').value = 'frontier'; t.events['stage-filter:change']();
const visibleFrontier = t.cards.filter((c) => !c.hidden);
assert.equal(visibleFrontier.length, 2, 'stage filter shows the stage and its frontier branch once each');
assert.equal(new Set(visibleFrontier.map((c) => c.id)).size, visibleFrontier.length, 'stage filter does not duplicate cross-references');
t.events['expand-visible:click'](); assert.equal(t.cards.find((c) => c.id === 'stage-frontier').open, true);
t.events['collapse-visible:click'](); assert.equal(t.cards.find((c) => c.id === 'stage-frontier').open, false);
t = run({hash: '#frontier-mlip-paper-x'});
assert.equal(t.frontier.open, true, 'deep paper hash opens frontier ancestor');
assert.equal(t.stageCards[3].open, true, 'deep paper hash opens outer stage ancestor');
assert.equal(t.paper.scrolled, true);
t = run({hash: '#stage-beginner'});
assert.equal(t.cards.find((c) => c.id === 'stage-beginner').open, true);
assert.equal(t.cards.find((c) => c.id === 'stage-beginner').scrolled, true);
t = run({hash: '#stage-beginner', query: 'stale'});
assert.equal(t.controls.get('#route-search').value, '', 'hash navigation clears stale search');
t = run({hash: '#does-not-exist'});
assert.ok(true, 'unknown hashes are ignored gracefully');
t = run({hash: '#%E0%A4%A'});
assert.ok(true, 'malformed hashes are ignored gracefully');
t = run();
t.location.hash = '#stage-beginner'; t.events['window:hashchange']?.();
assert.equal(t.stageCards[1].open, true, 'hashchange navigates after initial load');
console.log('Learning route UI: search, stage filter, unique counts, expand/collapse, hash navigation PASS');
