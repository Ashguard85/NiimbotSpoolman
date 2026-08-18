(()=>{"use strict";
const FORMATS={"40x40":{label:"40×40 mm",w_mm:40,h_mm:40,w_px:320,h_px:320,offset_y_px:0},"50x30":{label:"50×30 mm",w_mm:50,h_mm:30,w_px:384,h_px:240,offset_y_px:4},"30x20":{label:"30×20 mm",w_mm:30,h_mm:20,w_px:240,h_px:160,offset_y_px:0},"50x50":{label:"50×50 mm",w_mm:50,h_mm:50,w_px:384,h_px:400,offset_y_px:0}};
const model={id:4096,name_prefixes:["B1"],task:"b1",density:3,label_type:1,speed:1,dpi:203};let connected=false,name="NIIMBOT B1";
function supported(){return !!(navigator.bluetooth&&window.Niimbot);}
async function connect(){if(!window.Niimbot)throw new Error("NIIMBOT-Treiber nicht geladen");if(!navigator.bluetooth)throw new Error("Web Bluetooth wird in diesem Browser nicht unterstützt");const info=await Niimbot.identify(model);name=info?.name||Niimbot.printer?.device?.name||"NIIMBOT B1";connected=true;if("PACE_MS" in Niimbot)Niimbot.PACE_MS=Math.max(10,Number(Niimbot.PACE_MS||10));if("BUNDLE_MAX" in Niimbot)Niimbot.BUNDLE_MAX=180;return{name};}
async function print(canvas,format,{density=3,copies=1}={}){if(!connected)throw new Error("Drucker nicht verbunden");const f=FORMATS[format]||FORMATS["40x40"];const url=canvas.toDataURL("image/png");return Niimbot.printImage(url,{model,size:f,density:Number(density),copies:Number(copies),offsetY:f.offset_y_px});}
window.Printer={FORMATS,supported,connect,print,get connected(){return connected},get name(){return name}};
})();
