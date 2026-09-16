(()=>{"use strict";
const FORMATS={"40x40":{label:"40×40 mm",w_mm:40,h_mm:40,w_px:320,h_px:320,offset_y_px:0},"50x30":{label:"50×30 mm",w_mm:50,h_mm:30,w_px:384,h_px:240,offset_y_px:4},"30x20":{label:"30×20 mm",w_mm:30,h_mm:20,w_px:240,h_px:160,offset_y_px:0},"50x50":{label:"50×50 mm",w_mm:50,h_mm:50,w_px:384,h_px:400,offset_y_px:0}};
const model={id:4096,name_prefixes:["B1"],task:"b1",density:3,label_type:1,speed:1,dpi:203};
let connected=false,name="NIIMBOT B1",printing=false;
function supported(){return !!(navigator.bluetooth&&window.Niimbot);}
function tuneTransport(){
  if(!window.Niimbot)return;
  if("PACE_MS" in Niimbot)Niimbot.PACE_MS=Math.max(10,Number(Niimbot.PACE_MS||10));
  if("BUNDLE_MAX" in Niimbot)Niimbot.BUNDLE_MAX=180;
  if("WRITE_MODE" in Niimbot){try{Niimbot.WRITE_MODE="paced";}catch(_){}}
}
async function connect(){
  if(!window.Niimbot)throw new Error("NIIMBOT-Treiber nicht geladen");
  if(!navigator.bluetooth)throw new Error("Web Bluetooth wird in diesem Browser nicht unterstützt");
  const info=await Niimbot.identify(model);
  name=info?.name||Niimbot.printer?.device?.name||"NIIMBOT B1";
  connected=true;
  tuneTransport();
  return{name};
}

// The upstream driver accepts an image URL and internally performs
// fetch(url) -> blob() -> createImageBitmap(). Some iOS/Bluefy WebViews fail
// that load path even though the label already exists as a perfectly usable
// canvas. Intercept ONLY our one synthetic URL and hand the original canvas
// directly to the driver's drawImage() step. No data: URL, Blob URL or image
// decoding is involved. All globals are restored in finally.
async function printCanvasDirect(canvas,opts){
  const g=globalThis;
  const originalFetch=g.fetch;
  const hadCreate=Object.prototype.hasOwnProperty.call(g,"createImageBitmap");
  const originalCreate=g.createImageBitmap;
  if(typeof originalFetch!=="function")throw new Error("Browser-Fetch ist nicht verfügbar");
  const token=`https://niimbot-canvas.invalid/${Date.now()}-${Math.random().toString(36).slice(2)}`;
  const sentinel=Object.freeze({kind:"niimbot-canvas",token});
  let fetchHit=false,bitmapHit=false;
  g.fetch=function(input,init){
    const url=typeof input==="string"?input:(input&&input.url)||String(input||"");
    if(url===token){fetchHit=true;return Promise.resolve({ok:true,status:200,blob:async()=>sentinel});}
    return originalFetch.call(this,input,init);
  };
  g.createImageBitmap=async function(source,...args){
    if(source===sentinel){bitmapHit=true;return canvas;}
    if(typeof originalCreate==="function")return originalCreate.call(this,source,...args);
    throw new Error("createImageBitmap wird von diesem Browser nicht unterstützt");
  };
  try{
    const result=await Niimbot.printImage(token,opts);
    if(!fetchHit||!bitmapHit)throw new Error("NIIMBOT-Treiber hat den Canvas-Direktpfad nicht verwendet");
    return result;
  }finally{
    g.fetch=originalFetch;
    if(hadCreate)g.createImageBitmap=originalCreate;else try{delete g.createImageBitmap;}catch(_){g.createImageBitmap=originalCreate;}
  }
}

async function print(canvas,format,{density=3,copies=1,onProgress}={}){
  if(!connected)throw new Error("Drucker nicht verbunden");
  if(printing)throw new Error("Es läuft bereits ein Druckauftrag");
  if(!canvas||typeof canvas.getContext!=="function")throw new Error("Druck-Canvas fehlt");
  const f=FORMATS[format]||FORMATS["40x40"];
  let stage="Druckbild vorbereiten";
  printing=true;
  tuneTransport();
  try{
    return await printCanvasDirect(canvas,{
      model,size:f,density:Number(density),copies:Number(copies),offsetY:f.offset_y_px,
      onProgress:(s)=>{stage=String(s||stage);if(typeof onProgress==="function")onProgress(stage);}
    });
  }catch(e){
    const msg=e?.message||String(e);
    throw new Error(`${stage}: ${msg}`);
  }finally{printing=false;}
}
window.Printer={FORMATS,supported,connect,print,get connected(){return connected},get name(){return name},get printing(){return printing}};
})();
