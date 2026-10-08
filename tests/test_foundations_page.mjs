import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const html = fs.readFileSync(new URL('../static/foundations.html', import.meta.url), 'utf8');
const script = [...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map((m) => m[1]).join('\n');
const topicBlocks = [...html.matchAll(/<details\s+class="topic"([^>]*)>([\s\S]*?)<\/details>/g)];
const resourceBlocks = [...html.matchAll(/<details\s+class="resource"([^>]*)>([\s\S]*?)<\/details>/g)];
const attr = (attrs, name) => attrs.match(new RegExp(`${name}="([^"]*)"`))?.[1] ?? '';
const plain = (value) => value.replace(/<[^>]*>/g, ' ').replace(/&amp;/g, '&').replace(/\s+/g, ' ').trim();

assert.equal(topicBlocks.length, 20, 'foundations page should contain 20 topic cards');
assert.match(html, /20 个主题卡/, 'header inventory must match the topic count');
assert.doesNotMatch(html, /解释定态为何只得到离散能级|最小镜像距离需小于盒长一半/, 'known physics errors must not return');
assert.match(html, /散射态可具有连续能谱/);
assert.match(html, /短程截断半径需小于最短盒边的一半/);
assert.equal(resourceBlocks.filter(([_, attrs]) => attr(attrs, 'id').startsWith('book-')).length, 8);
assert.equal(resourceBlocks.filter(([_, attrs]) => attr(attrs, 'id').startsWith('paper-')).length, 8);

const ids = [...html.matchAll(/\bid="([^"]+)"/g)].map((m) => m[1]);
assert.equal(new Set(ids).size, ids.length, 'all page ids must be unique');
for (const block of [...topicBlocks, ...resourceBlocks]) {
  assert.match(block[2], /<summary[\s>]/, `${attr(block[1], 'id')} needs a native summary`);
}
for (const [, attrs, body] of topicBlocks) {
  assert.match(body, /<dl\s+class="glossary"[\s>]/, `${attr(attrs, 'id')} needs a glossary`);
}
for (const href of [...html.matchAll(/\bhref="([^"]+)"/g)].map((m) => m[1])) {
  if (/^https?:/i.test(href)) assert.match(href, /^https:\/\//i, `external link is not HTTPS: ${href}`);
}
assert.doesNotMatch(html, /\son[a-z]+\s*=|javascript\s*:/i, 'page must not use inline event handlers or javascript URLs');
assert.doesNotMatch(script, /createElement|appendChild|insertAdjacentHTML/i, 'cards must be present in static HTML');

class El {
  constructor({ id = '', className = '', dataset = {}, textContent = '', parent = null } = {}) {
    this.id = id; this.className = className; this.dataset = dataset; this.textContent = textContent;
    this.value = '';
    this.classList = { toggle: (name, enabled) => {
      const classes = new Set(this.className.split(/\s+/).filter(Boolean));
      if (enabled) classes.add(name); else classes.delete(name);
      this.className = [...classes].join(' ');
    } };
    this.parent = parent; this.hidden = false; this.open = false; this.listeners = new Map(); this.focused = false;
  }
  addEventListener(type, fn) { this.listeners.set(type, fn); }
  dispatch(type) { this.listeners.get(type)?.(); }
  matches(selector) { return selector === 'details' && (this.className === 'topic' || this.className === 'resource'); }
  querySelector(selector) {
    if (selector === 'summary') return { focus: () => { this.focused = true; } };
    if (selector === '.topic:not([hidden])') return this.children?.find((child) => !child.hidden) ?? null;
    return null;
  }
  scrollIntoView() { this.scrolled = true; }
}

const topics = topicBlocks.map(([, attrs, body]) => new El({
  id: attr(attrs, 'id'), className: 'topic', dataset: { category: attr(attrs, 'data-category'), search: attr(attrs, 'data-search') }, textContent: plain(body),
}));
const resources = resourceBlocks.map(([, attrs, body]) => new El({ id: attr(attrs, 'id'), className: 'resource', textContent: plain(body) }));
const groups = ['workflow', 'physics', 'dft', 'md', 'electrochem'].map((name) => {
  const group = new El({ className: 'group' });
  group.children = topics.filter((topic) => topic.dataset.category === name); group.querySelector = El.prototype.querySelector.bind(group);
  return group;
});
const search = new El({ id: 'search', value: '' });
const category = new El({ id: 'category', value: 'all' });
search.value = ''; category.value = 'all';
const count = new El({ id: 'count', textContent: '' });
const empty = new El({ id: 'empty', className: 'empty' });
const resourcesSection = new El({ className: 'resources' });
const expand = new El({ id: 'expand' }); const collapse = new El({ id: 'collapse' });
const byId = new Map([['search', search], ['category', category], ['count', count], ['empty', empty], ['expand', expand], ['collapse', collapse]]);
for (const card of [...topics, ...resources]) byId.set(card.id, card);
const location = { hash: '' };
const window = { listeners: new Map(), addEventListener(type, fn) { this.listeners.set(type, fn); } };
const document = {
  querySelector(selector) {
    if (selector.startsWith('#')) return byId.get(selector.slice(1));
    if (selector === '.resources') return resourcesSection;
    return null;
  },
  querySelectorAll(selector) {
    if (selector === '.topic') return topics;
    if (selector === '.resource') return resources;
    if (selector === '.group') return groups;
    return [];
  },
  getElementById(id) { return byId.get(id) ?? null; },
};
const ctx = vm.createContext({ URL, console, location, window, document });
vm.runInContext(script, ctx);

assert.equal(count.textContent, '显示 20 个主题 + 16 个资源 / 36 张卡');
search.value = 'wavefunction'; search.dispatch('input');
assert.equal(topics.filter((topic) => !topic.hidden).length, 1);
assert.match(count.textContent, /^显示 1 个主题 \+ 0 个资源/);
category.value = 'dft'; category.dispatch('change');
assert.equal(topics.filter((topic) => !topic.hidden).length, topics.filter((topic) => topic.dataset.category === 'dft' && topic.textContent.toLocaleLowerCase().includes('wavefunction')).length);
search.value = 'definitely-no-such-foundation-term'; search.dispatch('input');
assert.equal(empty.className, 'empty show'); assert.equal(resourcesSection.hidden, true);

search.value = ''; category.value = 'all'; search.dispatch('input');
expand.dispatch('click'); assert.ok([...topics, ...resources].every((card) => card.open));
collapse.dispatch('click'); assert.ok([...topics, ...resources].every((card) => !card.open));

location.hash = '#topic-wavefunction'; window.listeners.get('hashchange')();
assert.equal(search.value, ''); assert.equal(category.value, 'all'); assert.equal(byId.get('topic-wavefunction').open, true);
assert.equal(byId.get('topic-wavefunction').focused, true); assert.equal(byId.get('topic-wavefunction').scrolled, true);
location.hash = '#%E0%A4%A'; assert.doesNotThrow(() => window.listeners.get('hashchange')());
location.hash = '#book-03'; window.listeners.get('hashchange')();
assert.equal(byId.get('book-03').open, true, 'book deep links should open a resource');
console.log('Foundations page: static inventory, safety, progressive HTML, filters, controls, deep links PASS');
