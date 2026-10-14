import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('../static/index.html',import.meta.url),'utf8');
const code=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const nodes=new Map();
const node=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',value:'',classList:{add(){},remove(){}},addEventListener(){}});return nodes.get(id);};
const ctx=vm.createContext({URL,console,location:{protocol:'https:',hostname:'example.github.io'},localStorage:{getItem(){return '';}},sessionStorage:{getItem(){return '';}},window:{},document:{querySelector:node,querySelectorAll(){return [];}}});
ctx.window.LabUI={ready:Promise.resolve(),paperTitleHtml(p){return '<span class="paper-title-en">'+p.title+'</span><span class="paper-title-zh">中文题名</span>';}};
// Prevent fetching real data: test the rendering functions with controlled input.
vm.runInContext(code.replace(/\n\s*loadData\(\);\s*$/, '\n'),ctx);
vm.runInContext(`state.papers=[{id:'test',title:'Example',authors:[],scope_note:'Not a battery benchmark',resources:[{label:'Author code',url:'https://example.org/code'},{label:'bad',url:'javascript:alert(1)'},{label:'invalid',url:'not-url'}]}];showPaper('test');`,ctx);
assert.match(node('#detail').innerHTML,/Not a battery benchmark/);
assert.match(node('#detail').innerHTML,/中文题名/);
assert.match(node('#detail').innerHTML,/https:\/\/example.org\/code/);
assert.doesNotMatch(node('#detail').innerHTML,/javascript:|not-url/);
vm.runInContext(`state.papers=[{id:'old',title:'Old',authors:[]}];showPaper('old');`,ctx);
assert.doesNotMatch(node('#detail').innerHTML,/代码、数据与复现入口/);

// A slow optional title-map fetch must not gate the canonical catalog fetch.
let resolveTitles;
let titlesReady = new Promise(resolve => { resolveTitles = resolve; });
let titleLoaded = false;
const requests = [];
const freshNodes = new Map();
const freshNode = id => {
  if (!freshNodes.has(id)) freshNodes.set(id, {innerHTML:'',value:'',classList:{add(){},remove(){},toggle(){},contains(){return false;}},addEventListener(){}});
  return freshNodes.get(id);
};
const freshDocument = {querySelector:freshNode,querySelectorAll(){return [];}};
const response = payload => ({ok:true, async json(){return payload;}});
const catalog = [{id:'p1',title:'English title',authors:[],year:2026,journal:'Test',role:'role',summary:'summary'}];
const fetch = async url => {
  requests.push(url);
  if (url.endsWith('papers.json')) return response(catalog);
  if (url.endsWith('paper_tags.json')) return response({papers:{}});
  if (url.endsWith('learning_route.json')) return response({papers:{},stages:[],frontiers:[]});
  if (url.endsWith('search_config.json')) return response({});
  if (url.endsWith('zotero-links.json')) return response({items:{}});
  if (url.endsWith('method_evidence.auto.json')) return response({papers:{}});
  return response({});
};
const freshWindow = {LabUI:{ready:titlesReady,titleZh(){return titleLoaded ? '中文题名' : '';},paperTitleHtml(p){return `<span>${p.title}${p.title_zh ? ` · ${p.title_zh}` : ''}</span>`;}},BatteryBrowserAgent:{searchDetailed(){return {results:[]};}}};
const asyncCtx = vm.createContext({URL,URLSearchParams,console,fetch,location:{protocol:'https:',hostname:'example.github.io',search:''},localStorage:{getItem(){return '';},setItem(){}},sessionStorage:{getItem(){return '';},setItem(){}},window:freshWindow,document:freshDocument});
vm.runInContext(code, asyncCtx);
await Promise.resolve();
assert.ok(requests.some(url => url.endsWith('papers.json')), 'catalog fetch begins while title readiness is pending');
titleLoaded = true;
resolveTitles();
await new Promise(resolve => setTimeout(resolve, 0));
assert.match(freshNode('#paperList').innerHTML, /中文题名/, 'post-ready title refresh updates rendered list');

// On localhost with no backend, a 404 API probe must fall back to public assets
// and retain static tag/search metadata instead of treating the app as connected.
const localRequests = [];
const localNodes = new Map();
const localNode = id => {
  if (!localNodes.has(id)) localNodes.set(id, {innerHTML:'',value:'',classList:{add(){},remove(){},toggle(){},contains(){return false;}},addEventListener(){}});
  return localNodes.get(id);
};
const localDocument = {querySelector:localNode,querySelectorAll(){return [];}};
const localFetch = async url => {
  localRequests.push(url);
  if (url === '/api/papers') return {ok:false,status:404,async json(){return {error:'not found'};}};
  if (url.endsWith('papers.json')) return response(catalog);
  if (url.endsWith('paper_tags.json')) return response({papers:{p1:{display_tags:['方法论文']}}});
  if (url.endsWith('learning_route.json')) return response({papers:{},stages:[],frontiers:[]});
  if (url.endsWith('search_config.json')) return response({});
  if (url.endsWith('zotero-links.json')) return response({items:{}});
  if (url.endsWith('method_evidence.auto.json')) return response({papers:{}});
  return response({});
};
const localWindow = {LabUI:{ready:Promise.resolve(),titleZh(){return '';},paperTitleHtml(p){return `<span>${p.title}</span>`;}},BatteryBrowserAgent:{searchDetailed(){return {results:[]};}}};
const localCtx = vm.createContext({URL,URLSearchParams,console,fetch:localFetch,location:{protocol:'http:',hostname:'127.0.0.1',search:''},localStorage:{getItem(){return '';},setItem(){}},sessionStorage:{getItem(){return '';},setItem(){}},window:localWindow,document:localDocument});
vm.runInContext(code, localCtx);
for (let i = 0; i < 8; i++) await new Promise(resolve => setTimeout(resolve, 0));
assert.ok(localRequests.includes('/api/papers'), 'localhost probes the backend');
assert.ok(localRequests.some(url => url.endsWith('papers.json')));
assert.ok(localRequests.some(url => url.endsWith('paper_tags.json')));
assert.ok(localRequests.some(url => url.endsWith('search_config.json')));
assert.ok(!localRequests.includes('/api/paper-tags'));
assert.ok(!localRequests.includes('/api/search-config'));
assert.ok(!localRequests.includes('/api/health'));
assert.ok(!localRequests.includes('/api/methods'));
assert.ok(!localRequests.includes('/api/literature'));
assert.match(localNode('#paperList').innerHTML, /方法论文/, 'static tag metadata remains visible after API fallback');
console.log('Learning UI: resources, scope note, unsafe URLs, legacy papers PASS');
