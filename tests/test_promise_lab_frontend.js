/* No browser dependency: smoke-test interactive client calculations under Node.js. */
const fs=require('fs');const assert=require('assert');
const html=fs.readFileSync('promise_lab/index.html','utf8');
const data=html.match(/<script id="data" type="application\/json">([\s\S]*?)<\/script>/)[1];
const js=html.match(/<script>\s*([\s\S]*?)<\/script>/)[1];
const elements=new Map();const defaults={budget:15000,unitcost:5,efficacy:25,value:150,coverage:35};
function get(id){if(!elements.has(id)){elements.set(id,{textContent:id==='data'?data:'',innerHTML:'',value:defaults[id]??'',handlers:{},addEventListener(name,fn){this.handlers[name]=fn;}})}return elements.get(id)}
global.document={getElementById:get};
eval(js);
assert.strictEqual(get('treated').textContent,'3,000');
assert.strictEqual(get('avoided').textContent,'94.9');
assert.match(get('net').textContent,/772/);
assert.match(get('allocationtable').innerHTML,/RJ/);
get('efficacy').value=0;get('efficacy').handlers.input();
assert.strictEqual(get('avoided').textContent,'0.0');
get('budget').value=0;get('budget').handlers.input();
assert.strictEqual(get('treated').textContent,'0');
assert.strictEqual(get('breakeven').textContent,'N/A');
get('reset').handlers.click();
assert.strictEqual(get('treated').textContent,'3,000');
console.log('PromiseLab interactive JS smoke test: PASS (default, 0% efficacy, zero budget, reset)');
