const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../web/duel.js'),'utf8');
const elements={};let shown=0;
const context=vm.createContext({$:id=>elements[id]??=( {textContent:'',open:false,showModal(){shown++;this.open=true;},close(){this.open=false;},click(){}} )});
vm.runInContext('let state=null;'+source.slice(source.indexOf('let resultShownFor='),source.indexOf('function soundButton')),context);
function finish(id,winner,reason,turn='black',human='white'){
 vm.runInContext('state='+JSON.stringify({id,result:{winner,reason},turn,human})+';showResult();',context);
 return {title:elements.resultTitle.textContent,reason:elements.resultReason.textContent};
}
assert.deepEqual(finish('1','white','超时'),{title:'白方获胜',reason:'原因：黑方超时'});
elements.resultBoard.onclick();finish('1','white','超时');assert.equal(shown,1);
assert.equal(finish('2','black','将死','white').reason,'原因：白方被将死');
assert.equal(finish('3','white','认输').reason,'原因：黑方认输');
assert.equal(finish('4',null,'逼和').title,'本局和棋');
assert.equal(finish('5',null,'超时，另一方子力不足，和棋').reason,'原因：黑方超时，另一方子力不足，和棋');
assert.equal(shown,5);
console.log('Result dialog: winner, losing side, timeout draw and once-per-game display passed');
