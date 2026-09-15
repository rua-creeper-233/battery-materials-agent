import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const read = path => JSON.parse(fs.readFileSync(new URL('../'+path, import.meta.url),'utf8'));
const context = vm.createContext({window:{}});
vm.runInContext(fs.readFileSync(new URL('../static/browser_agent.js',import.meta.url),'utf8'), context);
const agent = context.window.BatteryBrowserAgent;
const papers = read('data/papers.json');
const config = read('data/search_config.json');
const cases = read('data/answer_regression.json').cases;
for (const c of cases) {
  const result = agent.answer(c.question,papers,config);
  assert.equal(result.guidance_id,c.guidance,c.question);
  if(c.task) assert.equal(result.task,c.task,c.question);
  for(const text of c.contains) assert.ok(result.answer_markdown.includes(text),`${c.question}: ${text}`);
  for(const text of c.excludes || []) assert.ok(!result.answer_markdown.includes(text),`${c.question}: unexpected ${text}`);
}
vm.runInContext('window.batteryBeginnerLessons={};',context);
vm.runInContext(fs.readFileSync(new URL('../static/md_lessons.js',import.meta.url),'utf8'),context);
const lessons=context.window.batteryMDLessons(()=>'<svg></svg>');
assert.equal(lessons.length,6);
assert.equal(context.window.batteryBeginnerLessons.md.length,lessons.length);
for(const [i,lesson] of lessons.entries()) {
  assert.ok(lesson.title && lesson.body && lesson.check);
  assert.equal(context.window.batteryBeginnerLessons.md[i].length,6);
}
console.log(`${cases.length} browser answer cases + 6 MD lesson contracts passed`);
