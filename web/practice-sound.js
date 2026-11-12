// Local audio assets; no network service is needed.
class PracticeSound {
 constructor() {
  this.context=null;this.buffers={};this.loading=null;this.sources=[];this.generation=0;
  this.enabled=true;
  try{this.enabled=localStorage.getItem('practiceSound')!=='off';}catch{}
 }
 async unlock(){
  if(!this.enabled)return;
  try{
   if(!this.context){
    const AudioContext=window.AudioContext||window.webkitAudioContext;
    if(!AudioContext)return;
    this.context=new AudioContext();
    this.loading=Promise.all(['Move','Capture','Check'].map(async name=>{
     const response=await fetch('/sounds/piano/'+name+'.mp3');
     if(!response.ok)throw Error('Sound unavailable');
     this.buffers[name]=await this.context.decodeAudioData(await response.arrayBuffer());
    })).catch(()=>{});
   }
   await this.context.resume();
  }catch{} // Audio failure must never prevent a move.
 }
 stop(){this.generation++;for(const source of this.sources){try{source.stop();}catch{}}this.sources=[];}
 toggle(){this.enabled=!this.enabled;if(!this.enabled)this.stop();else this.unlock();try{localStorage.setItem('practiceSound',this.enabled?'on':'off');}catch{} }
 playRetry(){
  this.stop();
  if(!this.enabled||!this.context||this.context.state!=='running')return;
  try{
   const source=this.context.createOscillator(),gain=this.context.createGain(),now=this.context.currentTime;
   source.type='sine';source.frequency.setValueAtTime(440,now);source.frequency.exponentialRampToValueAtTime(330,now+.18);
   gain.gain.setValueAtTime(0,now);gain.gain.linearRampToValueAtTime(.08,now+.025);gain.gain.exponentialRampToValueAtTime(.001,now+.22);
   source.connect(gain);gain.connect(this.context.destination);this.sources.push(source);
   source.onended=()=>{source.disconnect();gain.disconnect();this.sources=this.sources.filter(s=>s!==source);};
   source.start(now);source.stop(now+.23);
  }catch{}
 }
 async playMoves(moves){
  this.stop();const generation=this.generation;
  if(!this.enabled||!this.context)return;
  await this.loading;
  if(generation!==this.generation||!this.enabled||this.context.state!=='running')return;
  let time=this.context.currentTime;
  for(const move of moves){
   const name=/[+#]/.test(move.san)?'Check':move.captured?'Capture':'Move';
   const buffer=this.buffers[name];if(!buffer)continue;
   const source=this.context.createBufferSource(),gain=this.context.createGain();
   source.buffer=buffer;gain.gain.value=.55;source.connect(gain);gain.connect(this.context.destination);
   source.onended=()=>{source.disconnect();gain.disconnect();this.sources=this.sources.filter(s=>s!==source);};
   this.sources.push(source);source.start(time);time+=buffer.duration+.08;
  }
 }
}
const practiceSound=new PracticeSound();
