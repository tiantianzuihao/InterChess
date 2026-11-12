const $=id=>document.getElementById(id);
const symbols={K:'♔',Q:'♕',R:'♖',B:'♗',N:'♘',P:'♙',k:'♚',q:'♛',r:'♜',b:'♝',n:'♞',p:'♟'};
let state=null,selected=null,busy=false,receivedAt=0,promotionPrefix='',engineFailed=false;
function savedId(){try{return sessionStorage.getItem('duelId');}catch{return null;}}
function remember(id){try{sessionStorage.setItem('duelId',id);}catch{}}
function formatMove(m){return (m.color==='white'?'白方':'黑方')+'：'+symbols[m.piece]+' '+m.from+'->'+m.to+(m.captured?' 吃 '+symbols[m.captured]:'')+(m.san.includes('#')?' 将死':m.san.includes('+')?' 将军':'')+'（'+m.san+'）';}
function renderMove(row,move){
 row.replaceChildren();
 for(const part of formatMove(move).split(/([♔♕♖♗♘♙♚♛♜♝♞♟])/u)){
  if(/^[♔♕♖♗♘♙♚♛♜♝♞♟]$/u.test(part)){const piece=document.createElement('span');piece.className='inline-piece';piece.textContent=part;row.append(piece);}else row.append(document.createTextNode(part));
 }
}
let resultShownFor=null;
function resultSummary(game){
 const name=color=>color==='white'?'白方':'黑方';
 const winner=game.result.winner,reason=game.result.reason;
 const loser=winner?(winner==='white'?'black':'white'):game.turn;
 let detail=reason;
 if(reason==='超时')detail=name(loser)+'超时';
 else if(reason==='将死')detail=name(loser)+'被将死';
 else if(reason==='认输')detail=name(loser)+'认输';
 else if(reason.startsWith('超时，'))detail=name(game.turn)+reason;
 return {title:winner?name(winner)+'获胜':'本局和棋',detail,
  player:winner?(winner===game.human?'你赢了！':'电脑获胜'):'双方握手言和'};
}
function showResult(){
 if(!state?.result||resultShownFor===state.id)return;
 const summary=resultSummary(state);
 $('resultTitle').textContent=summary.title;
 $('resultPlayer').textContent=summary.player;
 $('resultReason').textContent='原因：'+summary.detail;
 if($('promotion').open)$('promotion').close();
 resultShownFor=state.id;
 $('resultDialog').showModal();
}
$('resultBoard').onclick=()=>$('resultDialog').close();
$('resultNew').onclick=()=>{$('resultDialog').close();$('newSettings').click();};
function soundButton(){$('soundToggle').textContent=practiceSound.enabled?'声音：开':'声音：关';$('soundToggle').setAttribute('aria-pressed',String(practiceSound.enabled));}
$('soundToggle').onclick=()=>{practiceSound.toggle();soundButton();};soundButton();
for(let i=1;i<=8;i++){const label=document.createElement('label'),input=document.createElement('input');input.type='radio';input.name='level';input.value=i;input.checked=i===1;label.append(input,document.createTextNode(String(i)));$('levels').append(label);}
for(const [minutes,increment] of [[1,0],[2,1],[3,0],[3,2],[5,0],[5,3],[10,0],[10,5],[15,10],[30,0]]){const b=document.createElement('button');b.type='button';b.textContent=minutes+' + '+increment;b.dataset.minutes=minutes;b.dataset.increment=increment;b.setAttribute('aria-label',`每方 ${minutes} 分钟，每步加 ${increment} 秒`);b.onclick=()=>{$('minutes').value=minutes;$('increment').value=increment;updateTimePreset();};$('presets').append(b);}
function updateTimePreset(){const m=+$('minutes').value,i=+$('increment').value;let matched=false;for(const b of $('presets').children){const active=+b.dataset.minutes===m&&+b.dataset.increment===i;b.classList.toggle('chosen',active);b.setAttribute('aria-pressed',String(active));matched||=active;}$('timeSummary').textContent=matched?'已选 '+m+' + '+i:'自定义';}
$('minutes').oninput=updateTimePreset;$('increment').oninput=updateTimePreset;updateTimePreset();
function timeMode(){const unlimited=document.querySelector('[name=timing]:checked').value==='unlimited';$('timeFields').hidden=unlimited;$('unlimitedHint').hidden=!unlimited;$('minutes').disabled=unlimited;$('increment').disabled=unlimited;}
document.querySelectorAll('[name=timing]').forEach(input=>input.onchange=timeMode);timeMode();
async function api(action,extra={}){
 if(busy)return;busy=true;const before=state?.history.length||0;
 $('start').disabled=true;$('newSettings').disabled=true;$('resign').disabled=true;$('claim').disabled=true;$('retry').hidden=true;
 try{
  const response=await fetch('/api/duel',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id:state?.id||savedId(),action,...extra})});
  const data=await response.json();if(!response.ok)throw Error(data.error||'连接失败');
  const same=state?.id===data.id;const unchanged=action==='state'&&same&&state.fen===data.fen&&JSON.stringify(state.result)===JSON.stringify(data.result);state=data;receivedAt=performance.now();if(!unchanged)selected=null;engineFailed=false;remember(data.id);
  $('error').textContent='';$('gameError').textContent='';$('setup').hidden=true;$('game').hidden=false;
  if(unchanged)clocks();else render();
  if(same&&['move','engine'].includes(action)&&data.history.length>before)practiceSound.playMoves(data.move_details.slice(before));
 }catch(error){
  if(state){$('gameError').textContent=error.message;$('retry').hidden=false;engineFailed=true;}
  else{$('error').textContent=error.message;}
 }finally{busy=false;$('start').disabled=false;$('newSettings').disabled=false;$('resign').disabled=Boolean(state?.result);$('claim').disabled=false;}
 if(state&&!state.result&&state.turn!==state.human&&!engineFailed&&action!=='new-settings')api('engine');
}
$('newGame').onsubmit=event=>{event.preventDefault();if(busy)return;practiceSound.unlock();practiceSound.stop();engineFailed=false;const form=new FormData(event.target);api('new',{level:+form.get('level'),color:form.get('color'),minutes:form.get('timing')==='timed'?+$('minutes').value:0,increment:form.get('timing')==='timed'?+$('increment').value:0});};
$('newSettings').onclick=()=>{if(state&&!state.result&&!confirm('结束当前对局并重新设置？'))return;practiceSound.stop();$('setup').hidden=false;$('game').hidden=true;state=null;try{sessionStorage.removeItem('duelId');}catch{};};
$('resign').onclick=()=>{if(confirm('确定认输吗？'))api('resign');};$('claim').onclick=()=>api('claim');$('retry').onclick=()=>{engineFailed=false;api('state');};
function render(){
 const human=state.human==='white'?'白方':'黑方',other=state.human==='white'?'黑方':'白方';
 $('humanLabel').textContent='你 · '+human;$('opponentLabel').textContent='电脑 · '+other;
 $('title').textContent='人机对弈 · '+state.level+' 级';
 $('status').replaceChildren();
 if(state.result){const summary=resultSummary(state);$('status').textContent=summary.title+' · '+summary.detail;}
 else{const text=(state.turn==='white'?'白方':'黑方')+(state.turn===state.human?'：轮到你了':'：电脑思考中');$('status').textContent=text;if(state.turn!==state.human){const dots=document.createElement('span');dots.className='thinking-dots';for(let i=0;i<3;i++){const dot=document.createElement('span');dot.textContent='.';dots.append(dot);}$('status').append(dots);}}
 $('claim').hidden=!state.can_claim_draw||state.turn!==state.human;
 $('history').replaceChildren();for(const move of state.move_details){const row=document.createElement('div');renderMove(row,move);$('history').append(row);}$('history').scrollTop=$('history').scrollHeight;
 renderCaptures();draw();clocks();showResult();
}
function renderCaptures(){
 const names={p:'兵',n:'马',b:'象',r:'车',q:'后',k:'王'};
 for(const [id,color] of [['human',state.human],['opponent',state.human==='white'?'black':'white']]){
  const tray=$(id+'Captures');tray.replaceChildren();
  const captures=state.move_details.filter(move=>move.color===color&&move.captured);
  tray.hidden=captures.length===0;
  for(const move of captures){
   const piece=document.createElement('span');piece.className='captured-piece';piece.textContent=symbols[move.captured];
   const name=(move.captured===move.captured.toUpperCase()?'白':'黑')+names[move.captured.toLowerCase()];
   piece.title='吃掉'+name;piece.setAttribute('aria-label',piece.title);tray.append(piece);
  }
 }
}
function clocks(){if(!state)return;for(const [color,id] of [[state.human,'human'],[state.human==='white'?'black':'white','opponent']]){let remaining=state.clocks?.[color];if(remaining!==undefined&&!state.result&&state.turn===color)remaining=Math.max(0,remaining-(performance.now()-receivedAt)/1000);$(id+'Time').textContent=remaining===undefined?'∞':Math.floor(Math.ceil(remaining)/60)+':'+String(Math.ceil(remaining)%60).padStart(2,'0');$(id+'Clock').classList.toggle('active',!state.result&&state.turn===color);$(id+'Clock').classList.toggle('low',remaining!==undefined&&remaining<30);}}
function draw(){
 $('board').replaceChildren();const flip=state.human==='black',last=state.history.at(-1),lastMove=state.move_details.at(-1);
 for(let y=0;y<8;y++)for(let x=0;x<8;x++){
  const file=flip?7-x:x,rank=flip?y:7-y,square=String.fromCharCode(97+file)+(rank+1),piece=state.pieces[square];
  const b=document.createElement('button');b.type='button';b.className=(file+rank)%2===0?'dark':'';b.textContent=symbols[piece]||'';b.setAttribute('aria-label',square+(piece?' '+piece:''));
  const label=document.createElement('small');label.textContent=square;b.append(label);
  if(last&&[last.slice(0,2),last.slice(2,4)].includes(square))b.classList.add('computer-last');
  if(selected===square)b.classList.add('selected');
  if(state.checked_king===square){b.classList.add('king-check');if(state.result?.reason==='将死'){const badge=document.createElement('span');badge.className='move-badge mate-badge';badge.textContent='#';b.append(badge);}}
  if(lastMove?.captured&&lastMove.to===square){const badge=document.createElement('span');badge.className='move-badge capture-badge';badge.textContent=symbols[lastMove.captured];badge.title='吃掉 '+symbols[lastMove.captured];b.append(badge);}
  if(selected&&state.legal_moves.some(m=>m.startsWith(selected+square))){const pawn=state.pieces[selected]?.toLowerCase()==='p';b.classList.add(piece||(pawn&&selected[0]!==square[0])?'capture-target':'target');}
  b.onclick=()=>choose(square);$('board').append(b);
 }
}
function choose(square){
 if(busy||!state||state.result||state.turn!==state.human)return;
 practiceSound.unlock();const piece=state.pieces[square];
 if(piece&&((piece===piece.toUpperCase())===(state.human==='white'))){selected=selected===square?null:square;draw();return;}
 if(!selected)return;const prefix=selected+square,options=state.legal_moves.filter(m=>m.startsWith(prefix));if(!options.length)return;
 if(options.some(m=>m.length===5)){promotionPrefix=prefix;$('promotion').showModal();return;}
 api('move',{move:prefix});
}
document.querySelectorAll('[data-piece]').forEach(b=>b.onclick=()=>{$('promotion').close();api('move',{move:promotionPrefix+b.dataset.piece});});$('cancelPromotion').onclick=()=>$('promotion').close();
setInterval(clocks,100);
setInterval(()=>{if(state&&!busy&&!state.result&&!engineFailed&&state.turn===state.human)api('state');},1000);
if(savedId())api('state');
