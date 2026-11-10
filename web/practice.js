const $=id=>document.getElementById(id);
const symbols={K:'♔',Q:'♕',R:'♖',B:'♗',N:'♘',P:'♙',k:'♚',q:'♛',r:'♜',b:'♝',n:'♞',p:'♟'};
let catalog=[],state=null,selected=null,busy=false,promotionPrefix='';
const progressKey='interchess.practice.progress.v1';
function puzzleOrder(){return catalog.flatMap(c=>c.puzzles.map(p=>({chapter:c.number,number:p.number})));}
function loadProgress(){
 try{const saved=JSON.parse(localStorage.getItem(progressKey));return puzzleOrder().find(p=>p.chapter===saved?.chapter&&p.number===saved?.number)||null;}catch{return null;}
}
function saveProgress(){
 const order=puzzleOrder(),index=order.findIndex(p=>p.chapter===+$('chapter').value&&p.number===state.number);
 if(index<0)return;
 const next=state.complete&&!state.pending?Math.min(index+1,order.length-1):index;
 try{localStorage.setItem(progressKey,JSON.stringify(order[next]));}catch{} // Storage restrictions must not block practice.
}
function formatMove(move){return (move.color==='white'?'白方':'黑方')+'：'+symbols[move.piece]+' '+move.from+'->'+move.to+(move.san.includes('#')?' 将死':move.san.includes('+')?' 将军':move.captured?' 吃 '+symbols[move.captured]:'')+'（'+move.san+'）';}
function lock(value){busy=value;for(const id of ['chapter','puzzle','prev','next','restart','reveal'])$(id).disabled=value;}
async function request(action='state',move='',password=''){
 if(action==='move')practiceSound.unlock();
 const previousCount=state?.history.length||0;
 lock(true);selected=null;
 try{
  const response=await fetch('/api/practice',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({chapter:+$('chapter').value,number:+$('puzzle').value,history:state?.history||[],action,move,password})});
  const data=await response.json();if(!response.ok)throw Error(data.error||'请求失败');state=data;render();saveProgress();
  if(action==='move'&&data.status==='correct')practiceSound.playMoves(data.move_details.slice(previousCount));
  if(action==='reveal'){$('answer').replaceChildren();for(const [i,line] of data.answers.entries()){const p=document.createElement('p');p.textContent='变化 '+(i+1)+'：';$('answer').append(p);const details=data.answer_details[i];for(const move of details){const row=document.createElement('p');row.textContent=formatMove(move);$('answer').append(row);}if(!details.length||state.pending){const original=document.createElement('p');original.textContent='书中记录：'+line;$('answer').append(original);}}for(const note of data.notes){const p=document.createElement('p');p.textContent=note;$('answer').append(p);}$('answer').hidden=false;$('answerPasswordDialog').close();}
 }catch(error){if(action==='reveal'){$('passwordError').textContent=error.message;$('answerPassword').value='';$('answerPassword').focus();}else{$('feedback').textContent=error.message;}}finally{lock(false);}
}
function render(){
 $('title').textContent='第 '+state.number+' 题 · '+state.points+' 分';
 $('side').textContent=(state.orientation==='white'?'白方':'黑方')+'先走';
 $('feedback').textContent=state.pending?'本题题面已核对，答案待复核，暂不判题。':state.complete?(state.checkmate?'将死！你完成了这道题。':'已完成书中变化！可查看答案说明或进入下一题。'):state.status==='illegal'?'这步不符合走棋规则，请重新选择。':state.status==='unlisted'?'这步未收录在书中答案里，需要进一步分析；不判为错棋。你可以换一种走法或查看答案。':state.status==='correct'?'这步符合书中答案，电脑已应手。请继续。':'轮到你了，试着找到关键一步。';
 $('message').replaceChildren();
 for(const move of state.move_details){
  const row=document.createElement('div');row.textContent=formatMove(move);$('message').append(row);
 }
 if(!state.complete&&!state.pending){
  const row=document.createElement('div');
  row.textContent=(state.turn==='white'?'白方':'黑方')+'：思考中';
  const dots=document.createElement('span');dots.className='thinking-dots';dots.setAttribute('aria-hidden','true');
  for(let i=0;i<3;i++){const dot=document.createElement('span');dot.textContent='.';dots.append(dot);}
  row.append(dots);$('message').append(row);
 }
 draw();
}
function draw(){
 $('board').replaceChildren();const flip=state.orientation==='black';
 const replyIndex=state.history.length-(state.history.length%2)-1;
 const reply=replyIndex>=1?state.history[replyIndex]:null;
 const lastSquares=reply?[reply.slice(0,2),reply.slice(2,4)]:[];
 for(let y=0;y<8;y++)for(let x=0;x<8;x++){
  const file=flip?7-x:x,rank=flip?y:7-y,square=String.fromCharCode(97+file)+(rank+1),piece=state.pieces[square];
  const b=document.createElement('button');b.type='button';b.className=(file+rank)%2===0?'dark':'';b.textContent=symbols[piece]||'';b.setAttribute('aria-label',square+(piece?' '+piece:''));
  const label=document.createElement('small');label.textContent=square;b.append(label);
  if(lastSquares.includes(square)){b.classList.add('computer-last');b.setAttribute('aria-label',b.getAttribute('aria-label')+(square===lastSquares[0]?'，电脑上一步起点':'，电脑上一步终点'));}
  if(selected===square)b.classList.add('selected');
  if(state.checked_king===square){b.classList.add('king-check');b.setAttribute('aria-label',b.getAttribute('aria-label')+(state.checkmate?'，将死':'，被将军'));}
  if(state.checkmate&&state.checked_king===square){const badge=document.createElement('span');badge.className='move-badge mate-badge';badge.textContent='#';badge.title='将死';b.append(badge);}
  if(state.last_capture?.square===square){const badge=document.createElement('span');badge.className='move-badge capture-badge';badge.textContent=symbols[state.last_capture.piece];badge.title='吃掉 '+symbols[state.last_capture.piece];badge.setAttribute('aria-label',badge.title);b.append(badge);}
  if(selected&&state.legal_moves.some(m=>m.startsWith(selected+square))){
   const pawn=state.pieces[selected]?.toLowerCase()==='p';
   const capture=Boolean(piece)||(pawn&&selected[0]!==square[0]);
   b.classList.add(capture?'capture-target':'target');
   if(capture)b.setAttribute('aria-label',b.getAttribute('aria-label')+'，可吃子');
  }
  b.onclick=()=>choose(square);$('board').append(b);
 }
}
function choose(square){
 if(busy||!state)return;
 const piece=state.pieces[square],ours=piece&&((piece===piece.toUpperCase())===(state.orientation==='white'));
 if(ours){
  selected=selected===square?null:square;draw();
  return;
 }
 if(state.complete||state.pending)return;
 if(!selected)return;
 const prefix=selected+square,options=state.legal_moves.filter(m=>m.startsWith(prefix));
 if(options.some(m=>m.length===5)){promotionPrefix=prefix;$('promotion').showModal();return;}
 request('move',prefix);
}
function reset(){practiceSound.stop();state=null;selected=null;$('answer').hidden=true;request();}
function chapterChanged(number){const c=catalog.find(c=>c.number===+$('chapter').value);$('puzzle').replaceChildren();for(const p of c.puzzles){const o=document.createElement('option');o.value=p.number;o.textContent='第 '+p.number+' 题'+(p.pending?'（待复核）':'');$('puzzle').append(o);}if(typeof number==='number'&&c.puzzles.some(p=>p.number===number))$('puzzle').value=number;reset();}
function updateSoundButton(){$('soundToggle').textContent=practiceSound.enabled?'声音：开':'声音：关';$('soundToggle').setAttribute('aria-pressed',String(practiceSound.enabled));}
$('soundToggle').onclick=()=>{practiceSound.toggle();updateSoundButton();};updateSoundButton();
$('chapter').onchange=chapterChanged;$('puzzle').onchange=reset;$('restart').onclick=reset;$('reveal').onclick=()=>{$('answer').hidden=true;$('answerPassword').value='';$('passwordError').textContent='';$('answerPasswordDialog').showModal();$('answerPassword').focus();};
$('answerPasswordForm').onsubmit=async event=>{event.preventDefault();if(busy)return;$('confirmAnswer').disabled=true;await request('reveal','',$('answerPassword').value);$('confirmAnswer').disabled=false;};
$('cancelAnswer').onclick=()=>{$('answerPasswordDialog').close();$('answerPassword').value='';};
for(const [id,delta]of [['prev',-1],['next',1]])$(id).onclick=()=>{const select=$('puzzle');select.selectedIndex=(select.selectedIndex+delta+select.options.length)%select.options.length;reset();};
document.querySelectorAll('[data-piece]').forEach(button=>button.onclick=()=>{$('promotion').close();request('move',promotionPrefix+button.dataset.piece);});
$('cancelPromotion').onclick=()=>{$('promotion').close();};
(async()=>{lock(true);try{const response=await fetch('/api/practice/catalog');if(!response.ok)throw Error('题库载入失败');catalog=await response.json();for(const c of catalog){const o=document.createElement('option');o.value=c.number;o.textContent='第 '+c.number+' 章 · '+c.title;$('chapter').append(o);}const saved=loadProgress();if(saved)$('chapter').value=saved.chapter;chapterChanged(saved?.number);}catch(error){$('feedback').textContent=error.message;lock(false);}})();
