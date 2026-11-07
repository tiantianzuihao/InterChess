const $=id=>document.getElementById(id);
const symbols={K:'♔',Q:'♕',R:'♖',B:'♗',N:'♘',P:'♙',k:'♚',q:'♛',r:'♜',b:'♝',n:'♞',p:'♟'};
let catalog=[],state=null,selected=null,busy=false,promotionPrefix='';
function lock(value){busy=value;for(const id of ['chapter','puzzle','prev','next','restart','reveal'])$(id).disabled=value;}
async function request(action='state',move=''){
 lock(true);selected=null;
 try{
  const response=await fetch('/api/practice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chapter:+$('chapter').value,number:+$('puzzle').value,history:state?.history||[],action,move})});
  const data=await response.json();if(!response.ok)throw Error(data.error||'请求失败');state=data;render();
  if(action==='reveal'){$('answer').replaceChildren();for(const [i,line] of data.answers.entries()){const p=document.createElement('p');p.textContent='变化 '+(i+1)+'：'+line;$('answer').append(p);}for(const note of data.notes){const p=document.createElement('p');p.textContent=note;$('answer').append(p);}$('answer').hidden=false;}
 }catch(error){$('message').textContent=error.message;}finally{lock(false);}
}
function render(){
 $('title').textContent='第 '+state.number+' 题 · '+state.points+' 分';
 $('side').textContent=(state.orientation==='white'?'白方':'黑方')+'先走';
 $('moves').textContent=state.san.length?'已走：'+state.san.join(' '):'';
 $('message').textContent=state.pending?'本题题面已核对，答案待复核，暂不判题。':state.complete?(state.checkmate?'将死！你完成了这道题。':'已完成书中变化！可查看答案说明或进入下一题。'):state.status==='illegal'?'这步不符合走棋规则，请重新选择。':state.status==='unlisted'?'这步未收录在书中答案里，需要进一步分析；不判为错棋。你可以换一种走法或查看答案。':state.status==='correct'?'这步符合书中答案，电脑已应手。请继续。':'轮到你了，试着找到关键一步。';
 draw();
}
function draw(){
 $('board').replaceChildren();const flip=state.orientation==='black';
 for(let y=0;y<8;y++)for(let x=0;x<8;x++){
  const file=flip?7-x:x,rank=flip?y:7-y,square=String.fromCharCode(97+file)+(rank+1),piece=state.pieces[square];
  const b=document.createElement('button');b.type='button';b.className=(file+rank)%2===0?'dark':'';b.textContent=symbols[piece]||'';b.setAttribute('aria-label',square+(piece?' '+piece:''));
  const label=document.createElement('small');label.textContent=square;b.append(label);
  if(selected===square)b.classList.add('selected');
  if(selected&&state.legal_moves.some(m=>m.startsWith(selected+square)))b.classList.add('target');
  b.onclick=()=>choose(square);$('board').append(b);
 }
}
function choose(square){
 if(busy||!state||state.complete||state.pending)return;
 const piece=state.pieces[square],ours=piece&&((piece===piece.toUpperCase())===(state.orientation==='white'));
 if(ours){selected=selected===square?null:square;draw();return;}
 if(!selected)return;
 const prefix=selected+square,options=state.legal_moves.filter(m=>m.startsWith(prefix));
 if(options.some(m=>m.length===5)){promotionPrefix=prefix;$('promotion').showModal();return;}
 request('move',prefix);
}
function reset(){state=null;selected=null;$('answer').hidden=true;request();}
function chapterChanged(){const c=catalog.find(c=>c.number===+$('chapter').value);$('puzzle').replaceChildren();for(const p of c.puzzles){const o=document.createElement('option');o.value=p.number;o.textContent='第 '+p.number+' 题'+(p.pending?'（待复核）':'');$('puzzle').append(o);}reset();}
$('chapter').onchange=chapterChanged;$('puzzle').onchange=reset;$('restart').onclick=reset;$('reveal').onclick=()=>request('reveal');
for(const [id,delta]of [['prev',-1],['next',1]])$(id).onclick=()=>{const select=$('puzzle');select.selectedIndex=(select.selectedIndex+delta+select.options.length)%select.options.length;reset();};
document.querySelectorAll('[data-piece]').forEach(button=>button.onclick=()=>{$('promotion').close();request('move',promotionPrefix+button.dataset.piece);});
$('cancelPromotion').onclick=()=>{$('promotion').close();};
(async()=>{lock(true);try{const response=await fetch('/api/practice/catalog');if(!response.ok)throw Error('题库载入失败');catalog=await response.json();for(const c of catalog){const o=document.createElement('option');o.value=c.number;o.textContent='第 '+c.number+' 章 · '+c.title;$('chapter').append(o);}chapterChanged();}catch(error){$('message').textContent=error.message;lock(false);}})();
