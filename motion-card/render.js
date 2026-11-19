const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1920,height:1080}});
await p.goto('file://'+__dirname+'/card.html');fs.mkdirSync(__dirname+'/frames',{recursive:true});
const N=91;for(let i=0;i<N;i++){await p.evaluate(t=>draw(t),i/30);await p.screenshot({path:`${__dirname}/frames/f${String(i).padStart(3,'0')}.png`});}
await b.close();})();
