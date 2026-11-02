/* CropGuard frontend, part 05-theme-camera-panels. Scripts share one global scope and MUST load in numeric order. */
/* Theme toggle, separate capture/upload, redesigned inspector panels */
function setTheme(m){document.documentElement.dataset.theme=m;try{localStorage.setItem('cgth',m)}catch(_){}$('th').textContent=m=='light'?'🌙 Dark':'☀ Light';redraw()}
$('th').onclick=()=>setTheme(document.documentElement.dataset.theme=='light'?'dark':'light');
const h0=$('file').onchange;['file','file2'].forEach(id=>$(id).onchange=e=>{h0(e);e.target.value=''});
function openCam(){const o=document.createElement('div');o.className='cam';o.innerHTML='<div><video playsinline autoplay muted></video><p>Centre one leaf in the frame</p><div class="row" style="justify-content:center;margin:0"><button class="pri" id="cc">● Capture</button><button id="cclose">Cancel</button></div></div>';document.body.appendChild(o);const v=o.querySelector('video');let st;const close=()=>{if(st)st.getTracks().forEach(t=>t.stop());o.remove()};
navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(s=>{st=s;v.srcObject=s}).catch(()=>{o.querySelector('p').textContent='Camera is not available here. Please use Upload image.';o.querySelector('#cc').disabled=true});
o.querySelector('#cc').onclick=()=>{const w=v.videoWidth,h=v.videoHeight;if(!w)return;const m=Math.min(w,h);sx.fillStyle='#fff';sx.fillRect(0,0,W,W);sx.drawImage(v,(w-m)/2,(h-m)/2,m,m,0,0,W,W);close();loaded()};o.querySelector('#cclose').onclick=close}
/* FIX: use querySelector since input#file is a sibling of label, not child — .closest('label') returns null and crashed everything after it */
const _camLbl=document.querySelector('label[for="file"]');
if(_camLbl)_camLbl.addEventListener('click',e=>{if(matchMedia('(pointer:fine)').matches&&navigator.mediaDevices&&navigator.mediaDevices.getUserMedia){e.preventDefault();openCam()}});
const LW=520,LH=170,F=(s,w=500)=>w+' '+s+'px system-ui,-apple-system,"Segoe UI",sans-serif',ez=t=>1-Math.pow(1-cl(t),3),CH=['#d9534f','#5aa469','#5b8fd9'];
function PC(id){const c=$(id),d=Math.min(2,window.devicePixelRatio||1);if(c.width!==LW*d){c.width=LW*d;c.height=LH*d}const x=c.getContext('2d');x.setTransform(d,0,0,d,0,0);x.clearRect(0,0,LW,LH);x.textAlign='left';return x}
function RP(x,a,b,w,h,r){x.beginPath();if(x.roundRect)x.roundRect(a,b,w,h,r);else x.rect(a,b,w,h)}
function p0n(t){const x=PC('c0'),mu=cvr('--mut'),ink=cvr('--ink'),u0=ez(t*2);x.globalAlpha=u0;x.save();RP(x,4,10,110,110,12);x.clip();x.drawImage(src,4,10,110,110);x.restore();x.fillStyle=ink;x.font=F(12,600);x.fillText('Your photo',4,138);x.fillStyle=mu;x.font=F(10.5);x.fillText('224×224 RGB',4,153);
x.strokeStyle=mu;x.lineWidth=1.5;x.beginPath();x.moveTo(124,65);x.lineTo(148,65);x.lineTo(142,59);x.moveTo(148,65);x.lineTo(142,71);x.stroke();x.globalAlpha=1;
[0,1,2].forEach(k=>{const u=ez(t*1.8-.3*k),px=158+k*122;x.globalAlpha=u;x.save();RP(x,px,10+(1-u)*8,110,110,12);x.clip();x.drawImage(A.ch[k],px,10+(1-u)*8,110,110);x.restore();x.fillStyle=CH[k];x.font=F(12,700);x.fillText(['Red','Green','Blue'][k],px,138);x.fillStyle=mu;x.font=F(10.5);x.fillText('μ '+A.nm[k].toFixed(2)+'  σ '+A.ns[k].toFixed(2),px,153)});
x.globalAlpha=1;x.fillStyle=mu;x.font=F(10.5);x.fillText('[1, 3, 224, 224] · float32 · (pixel/255 − mean) / std',4,168)}
function p1n(t){const x=PC('c1'),mu=cvr('--mut'),ac=cvr('--acc'),wn=cvr('--warn'),ln=cvr('--line'),X=d=>8+d/360*504,B=120,M=Math.max(...A.hb,1);
x.globalAlpha=.14;x.fillStyle=wn;x.fillRect(X(0),30,X(60)-X(0),B-30);x.fillStyle=ac;x.fillRect(X(60),30,X(170)-X(60),B-30);x.globalAlpha=1;
x.textAlign='center';x.font=F(11,600);x.fillStyle=wn;x.fillText('damage hues',(X(0)+X(60))/2,22);x.fillStyle=ac;x.fillText('healthy green',(X(60)+X(170))/2,22);
A.hb.forEach((v,b)=>{const u=ez(t*1.7-b*.02),h=v/M*(B-38)*u;x.fillStyle='hsl('+(b*10)+',36%,62%)';RP(x,X(b*10)+2,B-h,10,h,3);x.fill()});
x.strokeStyle=ln;x.lineWidth=1.5;x.beginPath();x.moveTo(8,B);x.lineTo(512,B);x.stroke();x.fillStyle=mu;x.font=F(10.5);[0,60,120,180,240,300,360].forEach(d=>x.fillText(d+'°',Math.min(500,Math.max(14,X(d))),136));
const tot=A.hb.reduce((a,b)=>a+b,0)||1,hp=Math.round(A.hb.slice(6,17).reduce((a,b)=>a+b,0)/tot*100);x.textAlign='left';x.font=F(12,500);x.fillStyle=mu;x.globalAlpha=ez(t*2-.6);x.fillText('Healthy-green pixels '+hp+'%  ·  damage / other hues '+(100-hp)+'%',8,160);x.globalAlpha=1}
function p2n(t){const x=PC('c2'),mu=cvr('--mut'),ink=cvr('--ink'),ln=cvr('--line'),ac=cvr('--acc'),wn=cvr('--warn'),N=['Vertical edges','Horizontal edges','Spots & texture','Smoothing'],D=['Sobel-x','Sobel-y','Laplacian','Gaussian'],K=[[-1,0,1,-2,0,2,-1,0,1],[-1,-2,-1,0,0,0,1,2,1],[0,1,0,1,-4,1,0,1,0],[1,2,1,2,4,2,1,2,1]],s=116;
K.forEach((k,i)=>{const u=ez(t*1.8-.3*i),px=10+i*(s+12);x.save();RP(x,px,4,s,s,12);x.fillStyle=ln;x.fill();x.clip();x.beginPath();x.rect(px,4,s*u,s);x.clip();x.drawImage(A.fl[i],px,4,s,s);x.restore();
if(u>.5){x.globalAlpha=(u-.5)*2;RP(x,px+6,10,29,29,6);x.fillStyle='rgba(0,0,0,.55)';x.fill();k.forEach((v,j)=>{x.fillStyle=v>0?ac:v<0?wn:'rgba(255,255,255,.25)';x.fillRect(px+9+(j%3)*8,13+(j/3|0)*8,6,6)});x.globalAlpha=1}
x.globalAlpha=u;x.textAlign='left';x.fillStyle=ink;x.font=F(12,600);x.fillText(N[i],px,138);x.fillStyle=mu;x.font=F(10.5);x.fillText(D[i]+' · 3×3 kernel',px,153);x.globalAlpha=1})}
function p3n(t){const x=PC('c3'),mu=cvr('--mut'),ink=cvr('--ink'),ln=cvr('--line'),ac=cvr('--acc'),a2=cvr('--acc2'),X0=190,BW=290;
R.t3.forEach(([n,p],k)=>{const y=22+k*40;x.textAlign='left';x.fillStyle=k?mu:ink;x.font=F(13,k?500:700);x.fillText(n,0,y+12);RP(x,X0,y,BW,16,8);x.fillStyle=ln;x.fill();const w=Math.max(0,BW*p*t);if(w>1){RP(x,X0,y,Math.max(16,w),16,8);x.fillStyle=k?a2:ac;x.globalAlpha=k?.65:1;x.fill();x.globalAlpha=1}x.textAlign='right';x.fillStyle=k?mu:ink;x.font=F(13,k?500:700);x.fillText((p*t*100).toFixed(0)+'%',LW-2,y+13)});
const gx=X0+BW*GATE;x.strokeStyle=mu;x.lineWidth=1;x.setLineDash([4,4]);x.beginPath();x.moveTo(gx,12);x.lineTo(gx,138);x.stroke();x.setLineDash([]);x.textAlign='center';x.fillStyle=mu;x.font=F(10.5);x.fillText(Math.round(GATE*100)+'% gate',gx,9);
x.textAlign='left';if(t>.85){const ok=R.c>=GATE;x.fillStyle=ok?ac:cvr('--bad');x.font=F(12,600);x.fillText(ok?'✓ Above the gate: result accepted':'✕ Below the gate: asking for a retake',0,162)}}
PAN[1][0][1]=p0n;PAN[2][0][1]=p1n;PAN[3][0][1]=p2n;PAN[3][1][1]=t=>p3n(Math.max(0,(t-.45)/.55));
function redraw(){if(!A||!R)return;[['ip0',p0n],['ip1',p1n],['ip2',p2n],['ip3',p3n]].forEach(([id,f])=>{if($(id).classList.contains('done'))f(1)})}
['c0','c1','c2','c3'].forEach(PC);
const TT=[['Model input','Your photo is split into three colour channels and rescaled, the form the network was trained on.'],['Colour analysis','Where the leaf\'s colours sit. Green means healthy tissue; brown and yellow hues point to damage.'],['Feature filters','First-layer style detectors pick out edges and spots, the building blocks the CNN learns from.'],['Class probabilities','The model\'s confidence for each disease. Below 60% the app asks for a retake instead of guessing.']];
Q('.ip').forEach((p,i)=>{const hEl=p.querySelector('h2,h3');const sEl=p.querySelectorAll('small')[1]||p.querySelector('small');if(hEl&&TT[i])hEl.textContent=TT[i][0];if(sEl&&TT[i])sEl.textContent=TT[i][1];});
{let m;try{m=localStorage.getItem('cgth')}catch(_){}if(!m)m=matchMedia('(prefers-color-scheme:light)').matches?'light':'dark';setTheme(m)}
