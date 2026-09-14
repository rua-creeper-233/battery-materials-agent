import fs from 'node:fs';
import vm from 'node:vm';
import assert from 'node:assert/strict';
const html=fs.readFileSync(new URL('../static/index.html',import.meta.url),'utf8');
const code=[...html.matchAll(/<script(?:\s[^>]*)?>([\s\S]*?)<\/script>/g)].map(m=>m[1]).join('\n');
const nodes=new Map();
const node=id=>{if(!nodes.has(id))nodes.set(id,{innerHTML:'',value:'',classList:{add(){},remove(){}},addEventListener(){}});return nodes.get(id);};
const ctx=vm.createContext({URL,console,location:{protocol:'https:',hostname:'example.github.io'},localStorage:{getItem(){return '';}},sessionStorage:{getItem(){return '';}},window:{},document:{querySelector:node,querySelectorAll(){return [];}}});
// Prevent fetching real data: test the rendering functions with controlled input.
vm.runInContext(code.replace(/\n\s*loadData\(\);\s*$/, '\n'),ctx);
vm.runInContext(`state.papers=[{id:'test',title:'Example',authors:[],scope_note:'Not a battery benchmark',resources:[{label:'Author code',url:'https://example.org/code'},{label:'bad',url:'javascript:alert(1)'},{label:'invalid',url:'not-url'}]}];showPaper('test');`,ctx);
assert.match(node('#detail').innerHTML,/Not a battery benchmark/);
assert.match(node('#detail').innerHTML,/https:\/\/example.org\/code/);
assert.doesNotMatch(node('#detail').innerHTML,/javascript:|not-url/);
vm.runInContext(`state.papers=[{id:'old',title:'Old',authors:[]}];showPaper('old');`,ctx);
assert.doesNotMatch(node('#detail').innerHTML,/代码、数据与复现入口/);
console.log('Learning UI: resources, scope note, unsafe URLs, legacy papers PASS');
