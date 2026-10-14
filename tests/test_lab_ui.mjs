import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const source = fs.readFileSync(new URL('../static/lab-ui.js', import.meta.url), 'utf8');

async function run({titlePayload = {}, statusPayload = {}, readyState = 'complete', statusOk = true} = {}) {
  const progress = [{textContent: '静态回退'}];
  const listeners = {};
  const document = {
    readyState,
    addEventListener(type, callback) { listeners[type] = callback; },
    querySelectorAll(selector) { return selector === '[data-project-progress]' ? progress : []; },
  };
  const response = (payload, ok = true) => ({ok, async json() { return payload; }});
  const fetch = async (url) => url.includes('paper_titles_zh') ? response(titlePayload) : response(statusPayload, statusOk);
  const window = {};
  vm.runInContext(source, vm.createContext({window, document, fetch, console}));
  await window.LabUI.ready;
  await window.LabUI.progressReady;
  return {window, document, listeners, progress};
}

let t = await run({
  titlePayload: {papers: {p1: {title: 'English <title>', title_zh: '中文 <危险>'}}},
  statusPayload: {as_of: '2026-10-14', papers: 176, dataset_rows: 998},
});
assert.equal(t.window.LabUI.titleZh({id: 'p1', title: 'English <title>'}), '中文 <危险>');
assert.match(t.window.LabUI.paperTitleHtml({id: 'p1', title: 'English <title>'}), /English &lt;title&gt;/);
assert.match(t.window.LabUI.paperTitleHtml({id: 'p1', title: 'English <title>'}), /中文 &lt;危险&gt;/);
assert.doesNotMatch(t.window.LabUI.paperTitleHtml({id: 'p1', title: 'English <title>'}), /<危险>/);
assert.equal(t.progress[0].textContent, '项目更新 2026-10-14 · 176 篇论文 · 998 条问答数据 · 本版未重新训练模型');

t = await run({titlePayload: {papers: {p1: {title: 'Old English', title_zh: '不应显示'}}}});
assert.equal(t.window.LabUI.titleZh({id: 'p1', title: 'Current English'}), '');
assert.doesNotMatch(t.window.LabUI.paperTitleHtml({id: 'p1', title: 'Current English'}), /不应显示/);
assert.equal(t.window.LabUI.titleZh({id: 'missing', title: 'Fallback'}), '');

t = await run({
  readyState: 'loading',
  titlePayload: {papers: {}},
  statusPayload: {as_of: '2026-10-14', papers: 176, dataset_rows: 998},
});
assert.equal(t.progress[0].textContent, '静态回退', 'status must wait for DOM readiness');
t.listeners.DOMContentLoaded();
assert.equal(t.progress[0].textContent, '项目更新 2026-10-14 · 176 篇论文 · 998 条问答数据 · 本版未重新训练模型');

t = await run({
  titlePayload: {papers: {}},
  statusPayload: {as_of: 'not-a-date', papers: -1, dataset_rows: 0},
});
assert.equal(t.progress[0].textContent, '静态回退', 'invalid status must preserve static fallback');

console.log('Lab UI: bilingual title escaping/fallback, DOM-ready progress, invalid status fallback PASS');
