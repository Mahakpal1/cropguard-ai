/* CropGuard frontend, part 01-core. Scripts share one global scope and MUST load in numeric order. */
let GATE=0.6;
const W=224,$=i=>document.getElementById(i),Q=s=>document.querySelectorAll(s),T0=performance.now();
const cv=$('img'),cx=cv.getContext('2d'),src=document.createElement('canvas');src.width=src.height=W;const sx=src.getContext('2d');
let ready=false,lang='en',A=null,R=null,busy=false;
const ST=[
  ['Capture','uint8 RGB','live','📸','01','Captures & verifies leaf photo'],
  ['Preprocess','[1,3,224,224]','live','⚙️','02','Resizes & balances image for AI'],
  ['Segment','mask[224,224]','live','🍃','03','Separates leaf from background'],
  ['Classify','logits[1,15]','sim','🧠','04','Scans for 38 disease patterns'],
  ['Grad-CAM','cam[7,7]→224²','sim','🔥','05','Highlights infection spots'],
  ['Severity','ratio ∈ [0,1]','live','📊','06','Measures damage & spread %'],
  ['Advise','KB lookup','live','🛡️','07','Prepares safe spray advice']
];
const CAP=[['Image captured','Decoded from camera/gallery into a 224×224 RGB canvas.','Input size matches the pretrained network.'],
['Resize + normalise','Pixels scaled to 0–1, then ImageNet mean/std applied, the same transform used in training.','Mismatched preprocessing silently ruins accuracy.'],
['Leaf segmentation','HSV thresholds (S>0.20, V>0.12) keep leaf pixels, drop background.','Lab-trained models fail on cluttered field backgrounds.'],
['CNN inference','EfficientNet-B0 (transfer learning) scans the image as feature maps and outputs 15 logits → softmax.','Pretrained ImageNet features need less data and give higher accuracy.'],
['Grad-CAM','Gradient of the winning class over the last conv layer gives a 7×7 map, upsampled to the image.','Shows the model looked at lesions, not the background.'],
['Severity','Lesion pixels ÷ leaf pixels, then binned. No severity labels exist, so this is an estimate.','Honest labelling: image-based estimate, not lab measurement.'],
['Advice lookup','The class id indexes a reviewed JSON knowledge base (no live generation, no dosage numbers).','A wrong dose can harm crops, so the advice is curated.']];
$('graph').innerHTML=ST.map((s,i)=>`${i?`<div class="cn" id="c${i}x"></div>`:''}<div class="nd" id="n${i}"><div class="nd-top-row"><span class="nd-step-badge">${s[4]}</span><i class="tg ${s[2]}">${s[2].toUpperCase()}</i></div><div class="nd-name-row"><span class="nd-ico">${s[3]}</span><b>${s[0]}</b></div><code>${s[1]}</code><p class="nd-desc" id="ndDesc${i}">${s[5]}</p><em id="m${i}"></em></div>`).join('');
const KB={ok:{n:['Tomato · Healthy','टमाटर · स्वस्थ'],do:[['Keep monitoring weekly','Water at the base of the plant'],['हर हफ्ते पौधों की जाँच करें','पौधे की जड़ के पास पानी दें']],av:[['Unnecessary pesticide spraying','Overwatering'],['बिना ज़रूरत कीटनाशक छिड़काव','ज़्यादा पानी देना']],pr:[['Keep proper plant spacing','Remove fallen debris'],['पौधों के बीच उचित दूरी रखें','गिरे हुए अवशेष हटाएँ']]},
eb:{n:['Tomato · Early Blight','टमाटर · अगेती झुलसा'],do:[['Remove severely infected leaves','Improve air circulation','Use a registered fungicide per product label and local agricultural officer advice'],['ज्यादा संक्रमित पत्तियाँ हटाएँ','पौधों के बीच हवा का आवागमन बढ़ाएँ','पंजीकृत फफूंदनाशक लेबल और स्थानीय कृषि अधिकारी की सलाह के अनुसार ही इस्तेमाल करें']],av:[['Do not spray repeatedly without confirming the disease','Do not exceed the label dose','Do not spray in rain or strong wind'],['बिना पुष्टि के बार-बार छिड़काव न करें','लेबल पर लिखी मात्रा से ज़्यादा न डालें','बारिश या तेज़ हवा में छिड़काव न करें']],pr:[['Keep adequate plant spacing','Remove infected plant debris','Rotate crops; avoid overhead irrigation'],['पौधों के बीच उचित दूरी रखें','संक्रमित अवशेष हटा दें','फसल चक्र अपनाएँ; ऊपर से सिंचाई न करें']]},
low:{n:['Unsure – please retake the photo','पक्का नहीं – कृपया फोटो दोबारा लें'],do:[['Photograph a single leaf in daylight','Keep it in focus, fill the frame'],['दिन की रोशनी में एक पत्ती की फोटो लें','फोटो साफ़ रखें, फ्रेम में पत्ती भरें']],av:[['Do not spray anything based on an unsure result'],['अनिश्चित परिणाम पर कोई छिड़काव न करें']],pr:[['Ask a local agricultural officer if it persists'],['समस्या बनी रहे तो स्थानीय कृषि अधिकारी से पूछें']]}};
const L={
  en:{h:['What to do now','What not to do','Prevention'],p:'Problem identified',d:'Severity is an image-based estimate. Always follow the product label and local agricultural officer guidance.',s:['Mild','Moderate','Severe']},
  hi:{h:['अभी क्या करें','क्या न करें','रोकथाम'],p:'समस्या की पहचान',d:'गंभीरता तस्वीर पर आधारित अनुमान है। हमेशा उत्पाद लेबल और स्थानीय कृषि अधिकारी की सलाह मानें।',s:['हल्का','मध्यम','गंभीर']},
  pa:{h:['ਹੁਣ ਕੀ ਕਰਨਾ ਹੈ','ਕੀ ਨਹੀਂ ਕਰਨਾ','ਰੋਕਥਾਮ'],p:'ਸਮੱਸਿਆ ਦੀ ਪਛਾਣ',d:'ਗੰਭੀਰਤਾ ਤਸਵੀਰ ਆਧਾਰਿਤ ਅੰਦਾਜ਼ਾ ਹੈ। ਹਮੇਸ਼ਾ ਉਤਪਾਦ ਲੇਬਲ ਅਤੇ ਸਥਾਨਕ ਖੇਤੀਬਾੜੀ ਅਧਿਕਾਰੀ ਦੀ ਸਲਾਹ ਮੰਨੋ।',s:['ਹਲਕਾ','ਦਰਮਿਆਨਾ','ਗੰਭੀਰ']},
  mr:{h:['आता काय करावे','काय करू नये','प्रतिबंध'],p:'समस्येची ओळख',d:'तीव्रता ही फोटोवर आधारित अंदाज आहे. नेहमी उत्पादन लेबल व स्थानिक कृषी अधिकाऱ्यांचा सल्ला पाळा.',s:['सौम्य','मध्यम','तीव्र']},
  te:{h:['ఇప్పుడు ఏమి చేయాలి','ఏమి చేయకూడదు','నివారణ'],p:'సమస్య గుర్తించబడింది',d:'తీవ్రత అనేది చిత్రం ఆధారిత అంచనా. ఎల్లప్పుడూ ఉత్పత్తి లేబుల్ మరియు వ్యవసాయ అధికారి మార్గదర్శకాలను పాటించండి.',s:['తేలికపాటి','మధ్యస్థం','తీవ్రమైన']},
  ta:{h:['இப்போது செய்ய வேண்டியவை','செய்யக்கூடாதவை','தடுப்பு முறைகள்'],p:'சிக்கல் கண்டறியப்பட்டது',d:'தீவிரம் என்பது படம் அடிப்படையிலான மதிப்பீடு. எப்போதும் தயாரிப்பு லேபிளைப் பின்பற்றுங்கள்.',s:['லேசானது','மிதமானது','தீவிரமானது']},
  gu:{h:['હવે શું કરવું','શું ન કરવું','અટકાવ'],p:'સમસ્યાની ઓળખ',d:'ગંભીરતા એ ફોટો આધારિત અંદાજ છે. હંમેશા લેબલ અને સ્થાનિક કૃષિ અધિકારીની સલાહ અનુસરો.',s:['હળવો','મધ્યમ','ગંભીર']},
  kn:{h:['ಈಗ ಏನು ಮಾಡಬೇಕು','ಏನು ಮಾಡಬಾರದು','ತಡೆಗಟ್ಟುವಿಕೆ'],p:'ಸಮಸ್ಯೆ ಪತ್ತೆಯಾಗಿದೆ',d:'ತೀವ್ರತೆಯು ಚಿತ್ರ ಆಧಾರಿತ ಅಂದಾಜಾಗಿದೆ. ಯಾವಾಗಲೂ ಉತ್ಪನ್ನ ಲೇಬಲ್ ಮತ್ತು ಕೃಷಿ ಅಧಿಕಾರಿ ಸಲಹೆ ಪಾಲಿಸಿ.',s:['ಸೌಮ್ಯ','ಮಧ್ಯಮ','ತೀವ್ರ']},
  bn:{h:['এখন কি করবেন','যা করবেন না','প্রতিরোধ'],p:'সমস্যার শনাক্তকরণ',d:'তীব্রতা ছবির উপর ভিত্তি করে অনুমান। সর্বদা পণ্যের লেবেল ও স্থানীয় কৃষি কর্মকর্তার পরামর্শ অনুসরণ করুন।',s:['মৃদু','মাঝারি','মারাত্মক']}
};
function log(){}
function sample(){
  const im = new Image();
  im.onload = () => {
    sx.clearRect(0, 0, W, W);
    sx.drawImage(im, 0, 0, W, W);
    loaded();
  };
  im.onerror = () => {
    const c = sx; c.fillStyle = '#f1efe6'; c.fillRect(0, 0, W, W); c.save(); c.translate(112, 112); c.rotate(-.5);
    const g = c.createRadialGradient(0, 0, 10, 0, 0, 100); g.addColorStop(0, '#4f9a3c'); g.addColorStop(1, '#2d6a2a');
    c.fillStyle = g; c.beginPath(); c.ellipse(0, 0, 98, 62, 0, 0, 7); c.fill(); c.strokeStyle = '#9acb6a'; c.lineWidth = 3;
    c.beginPath(); c.moveTo(-96, 0); c.lineTo(96, 0); c.stroke(); c.restore(); loaded();
  };
  im.src = 'img/sample_leaf.jpg';
}
function loaded(){ready=true;_idle=true;$('run').disabled=false;cx.drawImage(src,0,0);if(typeof brackets==='function')brackets(1)}
$('sample').onclick=sample;
/* file2 = choose image (gallery), file = camera */
function _loadFile(f){if(!f)return;const im=new Image();im.onload=()=>{sx.fillStyle='rgb(128,128,128)';sx.fillRect(0,0,W,W);const k=Math.min(W/im.width,W/im.height),dw=im.width*k,dh=im.height*k;sx.drawImage(im,(W-dw)/2,(W-dh)/2,dw,dh);loaded()};im.src=URL.createObjectURL(f)}
$('file').onchange=e=>{_loadFile(e.target.files[0])};
$('file2').onchange=e=>{_loadFile(e.target.files[0])};
/* Drag-and-drop on drop-overlay */
{const dz=$('drop');
if(dz){dz.addEventListener('dragover',e=>{e.preventDefault();dz.classList.add('over')});
dz.addEventListener('dragleave',()=>dz.classList.remove('over'));
dz.addEventListener('drop',e=>{e.preventDefault();dz.classList.remove('over');const f=e.dataTransfer&&e.dataTransfer.files[0];if(f)_loadFile(f)});}}
function hsv(r,g,b){r/=255;g/=255;b/=255;const M=Math.max(r,g,b),m=Math.min(r,g,b),d=M-m;let h=0;if(d){h=M==r?((g-b)/d)%6:M==g?(b-r)/d+2:(r-g)/d+4;h*=60;if(h<0)h+=360}return[h,M?d/M:0,M]}
function lay(fn){const c=document.createElement('canvas');c.width=c.height=W;const x=c.getContext('2d'),im=x.createImageData(W,W);for(let i=0;i<W*W;i++)im.data.set(fn(i),i*4);x.putImageData(im,0,0);return c}
function conv(gr,k,div=1){const o=new Float32Array(W*W);let mx=0;for(let y=1;y<W-1;y++)for(let x=1;x<W-1;x++){let a=0,n=0;for(let j=-1;j<=1;j++)for(let i=-1;i<=1;i++)a+=gr[(y+j)*W+x+i]*k[n++];a=Math.abs(a/div);o[y*W+x]=a;if(a>mx)mx=a}return lay(i=>{const v=mx?Math.min(255,o[i]/mx*255*1.6):0;return[v*.25,v,v*.9,255]})}
function analyse(){const n=W*W,d=sx.getImageData(0,0,W,W).data;let t=performance.now();
const MU=[.485,.456,.406],SD=[.229,.224,.225],s1=[0,0,0],s2=[0,0,0];for(let i=0;i<n;i++)for(let c=0;c<3;c++){const v=(d[i*4+c]/255-MU[c])/SD[c];s1[c]+=v;s2[c]+=v*v}
const nm=s1.map(v=>v/n),ns=s2.map((v,c)=>Math.sqrt(v/n-nm[c]*nm[c]));const tpre=performance.now()-t;t=performance.now();
const leaf=new Uint8Array(n),les=new Uint8Array(n),gr=new Float32Array(n),hb=new Array(36).fill(0);let lf=0,ls=0,x0=W,y0=W,x1=0,y1=0;
for(let i=0;i<n;i++){const r=d[i*4],g=d[i*4+1],b=d[i*4+2];gr[i]=.299*r+.587*g+.114*b;const[h,s,v]=hsv(r,g,b);if(s>.2&&v>.12){leaf[i]=1;lf++;hb[Math.min(35,h/10|0)]++;const x=i%W,y=i/W|0;x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);if(!(h>=60&&h<=170&&s>.25)){les[i]=1;ls++}}}
const tseg=performance.now()-t;t=performance.now();
let f=Float32Array.from(les);for(let p=0;p<3;p++){const q=new Float32Array(n);for(let y=0;y<W;y++)for(let x=0;x<W;x++){let a=0,c=0;for(let k=-7;k<=7;k++){const xx=x+k;if(xx>=0&&xx<W){a+=f[y*W+xx];c++}}q[y*W+x]=a/c}for(let y=0;y<W;y++)for(let x=0;x<W;x++){let a=0,c=0;for(let k=-7;k<=7;k++){const yy=y+k;if(yy>=0&&yy<W){a+=q[yy*W+x];c++}}f[y*W+x]=a/c}}
let mx=0;f.forEach(v=>mx=Math.max(mx,v));const tcam=performance.now()-t;
return{lf,ls,pct:lf?ls/lf*100:0,leafFrac:lf/n,bb:[x0,y0,x1,y1],hb,nm,ns,tpre,tseg,tcam,
ch:[0,1,2].map(c=>lay(i=>{const a=[0,0,0,255];a[c]=d[i*4+c];return a})),
mask:lay(i=>leaf[i]?[60,220,110,90]:[0,0,0,170]),
heat:lay(i=>{const v=mx?f[i]/mx:0;return[255*Math.min(1,v*2),255*Math.max(0,1-Math.abs(v-.5)*2),255*Math.max(0,1-v*2),v>.08?170*Math.min(1,v*1.5):0]}),
les:lay(i=>les[i]?[255,60,80,190]:[0,0,0,0]),
fl:[conv(gr,[-1,0,1,-2,0,2,-1,0,1],4),conv(gr,[-1,-2,-1,0,0,0,1,2,1],4),conv(gr,[0,1,0,1,-4,1,0,1,0],4),conv(gr,[1,2,1,2,4,2,1,2,1],16)]}}
function classify(a){
  return {
    k: 'offline',
    c: 0.0,
    t3: [['AI Server Offline · Connect port 8000', 0.0]]
  };
}
const sevI=p=>p<10?0:p<35?1:2,wait=(ms,fn)=>new Promise(r=>{const t0=performance.now();(function f(now){const t=Math.min(1,(now-t0)/ms);fn&&fn(t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2);t<1?requestAnimationFrame(f):r()})(t0)}),sl=ms=>new Promise(r=>setTimeout(r,ms));
/* stage() and hud() and brackets() are defined in 02-scanner.js which loads after this file */
const P=id=>{const c=$(id),x=c.getContext('2d');x.clearRect(0,0,240,96);x.font='10px monospace';return x},mu='#7f9a8b';
function p0(t){const x=P('c0');x.globalAlpha=t;[0,1,2].forEach(k=>x.drawImage(A.ch[k],k*80+2,2,76,76));x.globalAlpha=1;x.fillStyle=mu;['R','G','B'].forEach((s,k)=>x.fillText(s+' μ='+A.nm[k].toFixed(2),k*80+4,92))}
function p1(t){const x=P('c1'),m=Math.max(...A.hb,1);x.fillStyle='rgba(61,245,160,.12)';x.fillRect(60/10*6.6,0,11*6.6,80);A.hb.forEach((v,b)=>{x.fillStyle=`hsl(${b*10},75%,55%)`;const h=v/m*76*t;x.fillRect(b*6.6+1,80-h,5.4,h)});x.fillStyle=mu;x.fillText('0°',2,92);x.fillText('180°',112,92);x.fillText('360°',212,92);x.fillText('healthy band',70,10)}
function p2(t){const x=P('c2');['Sobel-x','Sobel-y','Laplace','Gauss'].forEach((s,k)=>{x.globalAlpha=Math.min(1,t*4-k*.6);x.drawImage(A.fl[k],k*60+2,2,56,56);x.globalAlpha=1;x.fillStyle=mu;x.fillText(s,k*60+4,72)})}
function p3(t){const x=P('c3');R.t3.forEach(([n,p],k)=>{const y=8+k*28;x.fillStyle=mu;x.fillText(n.slice(0,16),2,y+9);x.fillStyle='#1d3027';x.fillRect(104,y,110,10);x.fillStyle=k?'#27c4ff':'#3df5a0';x.fillRect(104,y,110*p*t,10);x.fillStyle='#d7eadf';x.fillText((p*t*100).toFixed(0)+'%',218,y+9)})}
const PAN={1:[['ip0',p0]],2:[['ip1',p1]],3:[['ip2',p2],['ip3',(t)=>p3(Math.max(0,(t-.45)/.55))]]};
function LG(i){const a=A,o=R,p=Math.round;return[
[['<span class="k">io.read</span> image 224×224 px · decoded RGB uint8','']],
[['<span class="k">tensor</span> shape=[1,3,224,224] dtype=float32','ok'],[`normalise: μ=${a.nm.map(v=>v.toFixed(2))}  σ=${a.ns.map(v=>v.toFixed(2))} (ImageNet mean/std)`,'']],
[[`<span class="k">hsv.mask</span> thr: S>0.20 V>0.12 → leaf=${a.lf}px (${(a.leafFrac*100).toFixed(1)}%)`,''],[`bbox=[${a.bb}]  hue histogram: 36 bins`,'']],
[['<span class="k">onnx.run</span> model=efficientnet_b0.onnx  <b class="w">[SIMULATED]</b>','w'],[`logits[15] → softmax: top1=${o.t3[0][0]} p=${o.t3[0][1].toFixed(2)}`,'ok'],[`entropy(top3)=${(-o.t3.reduce((s,[,q])=>s+q*Math.log(q),0)).toFixed(3)} nats`,'']],
[['<span class="k">gradcam</span> target=features.8 · map 7×7 → bilinear 224×224  <b class="w">[SIM]</b>','w'],[`blur+normalise ${a.tcam.toFixed(1)} ms`,'']],
[[`<span class="k">severity</span> lesion=${a.ls}px / leaf=${a.lf}px = ${a.pct.toFixed(1)}%`,'ok'],[`bin → ${['MILD','MODERATE','SEVERE'][sevI(a.pct)]}  (estimate)`,'']],
[[`<span class="k">gate</span> conf=${o.c.toFixed(2)} ≥ 0.60 ? ${o.c>=.6?'PASS':'FAIL → ask retake'}`,o.c>=.6?'ok':'b'],[`<span class="k">kb.lookup</span> class=${o.k} lang=${lang} → advice ready`,'']]][i]}
async function run(){if(busy)return;if(!ready){sample();await sl(150);}busy=true;_idle=false;
window.runPipeline = run;
console.log('[CropGuard] run() started — stage pipeline beginning');
const rb=$('run');if(rb){rb.disabled=true;rb.innerHTML='<span class="btn-play">⚡</span><span>Analysing…</span>';}const res=$('res');if(res)res.classList.remove('show');const pb=$('pb');if(pb)pb.style.width='0';Q('.nd').forEach(n=>{n.className='nd';n.lastChild.textContent=''});Q('.cn').forEach(c=>c.className='cn');Q('.ip').forEach(p=>p.classList.remove('on','done'));
A=analyse();R=classify(A);const live=typeof apiRes!=='undefined'&&apiRes&&!apiRes.model.simulated,ms=[null,A.tpre,A.tseg,live?apiRes.timings_ms.inference:'~sim',live&&apiRes.timings_ms.explain?apiRes.timings_ms.explain:A.tcam,.05,.1];
/* 8 stages: 0=capture 1=norm 2=segment 3=patch 4=raster 5=heat 6=lesion 7=diagnosis */
const STAGES=8,DUR=[1200,1400,1400,2000,2600,1400,1600,900];
try {
for(let i=0;i<STAGES;i++){
  const si=Math.min(i,6);/* CAP only has 7 entries */
  if($('n'+si))$('n'+si).className='nd act';
  if(i&&$('c'+si+'x'))$('c'+si+'x').className='cn flow';
  if(CAP[si]){const cp=CAP[si];const cap=$('cap');if(cap)cap.innerHTML=`<b>${i+1}. ${cp[0]}</b><p>${cp[1]}</p><p><b>Why:</b> ${cp[2]}</p>`;}
  (PAN[si]||[]).forEach(([id])=>{const el=$(id);if(el)el.classList.add('on')});
  const pb=$('pb');if(pb)pb.style.width=((i+1)/STAGES*100)+'%';
  await wait(DUR[i],t=>{stage(i,t);(PAN[si]||[]).forEach(([,f])=>f(t))});
  if(si==0&&$('m0'))$('m0').textContent='ok';else if(typeof ms[si]=='string'&&$('m3'))$('m3').textContent=ms[si];else if($('m'+si)&&typeof ms[si]=='number')$('m'+si).textContent=ms[si].toFixed(1)+' ms';
  if($('n'+si))$('n'+si).className='nd done';
  if(i&&$('c'+si+'x'))$('c'+si+'x').className='cn';
  (PAN[si]||[]).forEach(([id])=>{const el=$(id);if(el){el.classList.remove('on');el.classList.add('done')}})
  console.log('[CropGuard] stage',i,'complete');
}
} catch(e) { console.error('[CropGuard] stage loop error:',e); }
_idle=true;
log('pipeline complete · rendering diagnosis','ok');
try{show();}catch(e){console.error('[CropGuard] show() error:',e);}
busy=false;if(rb){rb.disabled=false;rb.innerHTML='<span class="btn-play">▶</span><span>Analyse Leaf</span>';}}
function show(){const k=R.k,sv=sevI(A.pct),T=L[lang],li=lang=='hi'?1:0,e=KB[k];const res=$('res');if(res)res.classList.add('show');const rl1=$('rl1');if(rl1)rl1.textContent=T.p;const dn=$('dn');if(dn)dn.textContent=e.n[li];const gate=$('gate');if(gate)gate.textContent=R.c>=GATE?'confidence gate ≥ '+Math.round(GATE*100)+'%: PASS':'confidence gate ≥ '+Math.round(GATE*100)+'%: FAIL';
const cf=$('cf');if(cf)cf.textContent=Math.round(R.c*100)+'%';const ring=$('ring');if(ring)ring.style.setProperty('--p',R.c*100);const ent=$('ent');if(ent)ent.textContent='top-3: '+R.t3.map(x=>x[1].toFixed(2)).join(' / ');
const ap=$('ap');if(ap)ap.textContent=k=='low'?'–':A.pct.toFixed(0)+'%';const sv2=$('sv');if(sv2)sv2.textContent=k=='low'?'':T.s[sv];setTimeout(()=>{const mk=$('mk');if(mk)mk.style.left=Math.min(98,A.pct/50*100)+'%'},60);
const cols=$('cols');if(cols)cols.innerHTML=[e.do[li],e.av[li],e.pr[li]].map((l,i)=>`<div class="col" style="animation-delay:${i*.15}s"><h4>${['✅','⚠️','🛡️'][i]} ${T.h[i]}</h4><ul>${l.map(x=>`<li>${x}</li>`).join('')}</ul></div>`).join('');const disc=$('disc');if(disc)disc.textContent=T.d;
/* Update recent analysis panel */
const dn2=$('dn'),cf2=$('cf');
/* Update What to Do/Not lists on the dashboard card */
const dl=$('actionDoList'),ntl=$('actionDontList');
if(dl)dl.innerHTML=e.do[li].map(x=>`<li>${x}</li>`).join('');
if(ntl)ntl.innerHTML=e.av[li].map(x=>`<li>${x}</li>`).join('');
if(!R.sv){R.sv=1;try{const h=JSON.parse(localStorage.getItem('cg2')||'[]');h.unshift(`${new Date().toLocaleTimeString()}  ${e.n[0]}  conf=${R.c.toFixed(2)}  area=${A.pct.toFixed(0)}%`);localStorage.setItem('cg2',JSON.stringify(h.slice(0,8)))}catch(_){}}hist()}
function hist(){let h=[];try{h=JSON.parse(localStorage.getItem('cg2')||'[]')}catch(_){}const hi=$('hist');if(hi)hi.innerHTML=h.length?h.map(x=>`<span>${x}</span>`).join(''):'<span>no scans yet</span>'}
const _runBtn=$('run');if(_runBtn)_runBtn.onclick=run;hist();log('console ready · waiting for image','ok');
Q('[data-l]').forEach(b=>b.onclick=()=>{lang=b.dataset.l;Q('[data-l]').forEach(x=>x.classList.toggle('on',x==b));if(R&&!busy)show()});
const SPEECH_VOICES={en:'en-IN',hi:'hi-IN',pa:'pa-IN',mr:'mr-IN',te:'te-IN',ta:'ta-IN',gu:'gu-IN',kn:'kn-IN',bn:'bn-IN'};
const _sayBtn=$('say');if(_sayBtn)_sayBtn.onclick=()=>{if(!R||!window.speechSynthesis)return;const li=lang=='en'?0:1,e=KB[R.k],T=L[lang]||L.en,u=new SpeechSynthesisUtterance([e.n[li]||e.n[0],...[0,1,2].flatMap(i=>[T.h[i],...[e.do,e.av,e.pr][i][li]||[e.do,e.av,e.pr][i][0]])].join('. '));u.lang=SPEECH_VOICES[lang]||'en-IN';speechSynthesis.cancel();speechSynthesis.speak(u)};
setTimeout(sample, 100);
