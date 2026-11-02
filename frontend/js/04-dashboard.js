/* CropGuard frontend, part 04-dashboard. Scripts share one global scope and MUST load in numeric order. */
/* Dashboard + page polish: ease-out-expo count-up, staggered reveals, scroll-in panels */
const eo=t=>t>=1?1:1-Math.pow(2,-10*t);
function tween(ms,fn,delay=0){return new Promise(r=>setTimeout(()=>{const t0=performance.now();(function f(n){const t=Math.min(1,(n-t0)/ms);fn(eo(t),t);t<1?requestAnimationFrame(f):r()})(t0)},delay))}
const _show=show,_ld=loaded;
show=function(){
  try{_show();}catch(e){console.error('show._show error:',e);}
  if(!R||!A)return;
  if(R._a)return;R._a=1;
  const k=R.k,cf=R.c*100,ap=A.pct,sv=sevI(A.pct);
  const mk=$('mk'),ring=$('ring'),cfEl=$('cf'),apEl=$('ap'),dnEl=$('dn'),svEl=$('sv'),resEl=$('res');
  if(ring)ring.style.setProperty('--p',0);
  if(cfEl)cfEl.textContent='0%';
  if(k!='low'&&apEl)apEl.textContent='0%';
  if(mk)mk.style.visibility='hidden';
  if(dnEl){dnEl.classList.remove('pop');void dnEl.offsetWidth;dnEl.classList.add('pop');}
  if(svEl)svEl.style.color=k=='low'?'':['var(--acc)','var(--warn)','var(--bad)'][sv];
  if(ring&&cfEl)tween(1500,e=>{ring.style.setProperty('--p',cf*e);cfEl.textContent=Math.round(cf*e)+'%'},250);
  if(mk&&apEl)tween(1500,e=>{mk.style.visibility='visible';if(k!='low')apEl.textContent=Math.round(ap*e)+'%';mk.style.left=Math.min(98,ap/50*100)*e+'%'},450);
  Q('.kpi').forEach((c,i)=>c.style.animationDelay=i*.12+'s');
  Q('#cols .col').forEach((c,i)=>{c.style.animationDelay=(.5+i*.15)+'s';c.querySelectorAll('li').forEach((l,j)=>l.style.animationDelay=(.8+i*.15+j*.09)+'s')});
  if(resEl){const r=resEl.getBoundingClientRect();if(r.top>innerHeight*.55&&innerWidth<1280)setTimeout(()=>window.scrollTo({top:scrollY+r.top-70,behavior:'smooth'}),350);}
};
loaded=function(){_ld();cv.classList.remove('fl');void cv.offsetWidth;cv.classList.add('fl')};
{const b=$('say'),o=b.onclick;b.onclick=()=>{o();b.classList.add('sp');setTimeout(()=>{const iv=setInterval(()=>{if(!window.speechSynthesis||!speechSynthesis.speaking){b.classList.remove('sp');clearInterval(iv)}},300)},700)}}
Q('.wrap>.panel').forEach((p,k)=>p.style.animationDelay=k*.1+'s');$('res').style.animationDelay='0s';
{const els=[...Q('.wrap>.panel')].slice(-2);els.forEach(e=>e.classList.add('rvl'));const io=new IntersectionObserver(es=>es.forEach(x=>{if(x.isIntersecting){x.target.classList.add('in2');io.unobserve(x.target)}}),{threshold:.15});els.forEach(e=>io.observe(e))}
