import fs from 'node:fs';
import vm from 'node:vm';

const code = fs.readFileSync(new URL('../static/browser_agent.js', import.meta.url), 'utf8');
const dataPath = process.argv[2] || 'data/papers.json';
const papers = JSON.parse(fs.readFileSync(dataPath, 'utf8'));
const tags = JSON.parse(fs.readFileSync(new URL('../data/paper_tags.json', import.meta.url), 'utf8')).papers;
const config = JSON.parse(fs.readFileSync(new URL('../data/search_config.json', import.meta.url), 'utf8'));
const merged = papers.map(paper => ({display_tags: [], ...paper, ...(tags[paper.id] || {})}));
const context = vm.createContext({window: {}});
vm.runInContext(code, context);
const agent = context.window.BatteryBrowserAgent;
const queries = JSON.parse(process.argv[3] || '[]');
const result = {};
for (const query of queries) {
  const detailed = agent.searchDetailed(query, merged, 8, config);
  result[query] = {
    ids: detailed.results.map(paper => paper.id),
    dois: detailed.query.dois,
    mode: detailed.query.mode,
    expanded_terms: detailed.query.expanded_terms,
  };
}
if (process.argv[4]) {
  result.answer = agent.answer(process.argv[4], merged, config).answer_markdown;
}
process.stdout.write(JSON.stringify(result));
