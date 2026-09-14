import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';

const code = fs.readFileSync(new URL('../static/browser_agent.js', import.meta.url), 'utf8');
const papers = JSON.parse(fs.readFileSync(new URL('../data/papers.json', import.meta.url), 'utf8'));
const tags = JSON.parse(fs.readFileSync(new URL('../data/paper_tags.json', import.meta.url), 'utf8')).papers;
const config = JSON.parse(fs.readFileSync(new URL('../data/search_config.json', import.meta.url), 'utf8'));
const merged = papers.map(paper => ({...paper, ...(tags[paper.id] || {})}));
const context = vm.createContext({window:{}});
vm.runInContext(code, context);
const agent = context.window.BatteryBrowserAgent;

const vasp = agent.searchDetailed('tag:VASP 入门', merged, 30, config);
assert.ok(vasp.results.length > 0);
assert.ok(vasp.results.every(paper => paper.display_tags.includes('VASP')));
assert.match(vasp.results[0].retrieval.reason, /VASP/);
assert.equal(agent.search('zzzz-not-a-real-material-token', merged, 5, config).length, 0);
assert.equal(agent.taskType('VASP 入门如何设置 INCAR？'), 'dft_setup');
assert.equal(merged.filter(paper => paper.display_tags.includes('MS')).length, 0);
console.log('Browser retrieval: weighted search, filters, reasons, honest no-hit PASS');
