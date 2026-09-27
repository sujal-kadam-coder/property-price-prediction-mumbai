let page=1,pages=1,selected=[],charts={};
const $=id=>document.getElementById(id);
const esc=s=>String(s).replace(/[&<>"']/g,m=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#039;'}[m]));
function fill(id,a,first="Select"){ $(id).innerHTML=`<option value="">${first}</option>`+a.map(x=>`<option value="${esc(x)}">${esc(x)}</option>`).join("");}
function toast(t){let e=$("toast");e.textContent=t;e.style.display="block";setTimeout(()=>e.style.display="none",2500)}
function moneyL(v){return v>=100?`₹${(v/100).toFixed(2)} Cr`:`₹${v.toFixed(2)} L`}
async function init(){
 let m=await fetch("/api/metadata").then(r=>r.json());
 fill("bhk",m.bhk);fill("type",m.types);fill("region",m.regions);fill("status",m.statuses);fill("age",m.ages);
 fill("fRegion",m.regions,"All regions");fill("fType",m.types,"All types");fill("fStatus",m.statuses,"All status");fill("fAge",m.ages,"All age");
 $("sTotal").textContent=m.stats.total.toLocaleString();$("heroTotal").textContent=m.stats.total.toLocaleString();$("sRegions").textContent=m.stats.regions;$("sLocalities").textContent=m.stats.localities.toLocaleString();$("sTypes").textContent=m.stats.types;
 $("avgPrice").textContent=moneyL(m.stats.avg_price_lakh);$("medianPrice").textContent=moneyL(m.stats.median_price_lakh);$("avgPpsf").textContent="₹"+Math.round(m.stats.avg_ppsf).toLocaleString("en-IN");
 loadProperties(1);loadAnalytics();loadMetrics();
}
async function predict(){
 let body={bhk:$("bhk").value,type:$("type").value,area:$("area").value,region:$("region").value,status:$("status").value,age:$("age").value};
 if(Object.values(body).some(v=>!v)){toast("Please complete all six inputs.");return}
 $("resultPrice").textContent="Calculating…";$("predictBtn").disabled=true;
 try{let r=await fetch("/api/predict",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)}),d=await r.json();if(!r.ok)throw Error(d.error);
 $("resultPrice").textContent=d.formatted_price;$("resultPpsf").textContent="₹"+Math.round(d.price_per_sqft).toLocaleString("en-IN");$("resultModel").textContent=d.model_used;$("resultRegion").textContent=d.inputs.region;
 let qs=new URLSearchParams(body);let s=await fetch("/api/similar?"+qs).then(r=>r.json());$("similarWrap").style.display="block";$("similar").innerHTML=s.items.map(card).join("");$("similarWrap").scrollIntoView({behavior:"smooth",block:"start"});
 }catch(e){toast(e.message)}finally{$("predictBtn").disabled=false}
}
function card(x){return `<div class="property"><span class="tag">${esc(x.type)}</span><h3>${esc(x.price)}</h3><p>${x.bhk} BHK · ${Number(x.area).toLocaleString()} sq.ft.</p><p>${esc(x.locality)} · ${esc(x.region)}</p><p>${esc(x.status)} · ${esc(x.age)}</p><div class="bottom"><b>₹${Math.round(x.ppsf).toLocaleString("en-IN")}/sq.ft.</b><button class="mini-btn" onclick="addCompare(${x.id})">Compare</button></div></div>`}
async function loadProperties(p){
 if(p<1||p>pages)return;page=p;
 let q=new URLSearchParams({page,limit:12,q:$("q").value,region:$("fRegion").value,type:$("fType").value,status:$("fStatus").value,age:$("fAge").value,sort:"price_asc"});
 let d=await fetch("/api/properties?"+q).then(r=>r.json());pages=d.pages;$("pageInfo").textContent=`Page ${page} of ${pages} · ${d.total.toLocaleString()} properties`;$("properties").innerHTML=d.items.map(card).join("");
}
function addCompare(id){fetch("/api/properties?page=1&limit=1").catch(()=>{});if(selected.includes(id))return;if(selected.length>=3){toast("You can compare up to 3 properties.");return}selected.push(id);renderCompare();toast("Property added to comparison.");}
async function renderCompare(){
 if(!selected.length){$("compareList").innerHTML='<div class="compare-card" style="color:var(--muted)">No properties selected yet.</div>';$("compareTable").innerHTML="";return}
 let all=await fetch("/api/properties?page=1&limit=1").then(r=>r.json()); // endpoint is used below with direct record search fallback
 let rows=[];
 for(let id of selected){
   let r=await fetch("/api/properties?page=1&limit=1&q=").then(x=>x.json()); // placeholder
 }
 // Get selected records through a compact local request using server-side full search is not ideal; use a dedicated comparison endpoint.
 let r=await fetch("/api/compare",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({ids:selected})}).then(x=>x.json());
 $("compareList").innerHTML=r.items.map(x=>`<div class="compare-card"><b>${esc(x.price)}</b><p>${x.bhk} BHK · ${x.area.toLocaleString()} sq.ft.</p><p>${esc(x.locality)} · ${esc(x.region)}</p><button class="mini-btn" onclick="removeCompare(${x.id})">Remove</button></div>`).join("");
 if(r.items.length){let keys=[["Price","price"],["BHK","bhk"],["Type","type"],["Area","area"],["Region","region"],["Price / sq.ft.","ppsf"],["Status","status"],["Age","age"]];$("compareTable").innerHTML="<table><tr><th>Feature</th>"+r.items.map(x=>`<th>${esc(x.locality)}</th>`).join("")+"</tr>"+keys.map(k=>`<tr><td>${k[0]}</td>${r.items.map(x=>`<td>${k[1]=="ppsf"?"₹"+Math.round(x[k[1]]).toLocaleString("en-IN"):esc(x[k[1]])}</td>`).join("")}</tr>`).join("")+"</table>"}
}
function removeCompare(id){selected=selected.filter(x=>x!==id);renderCompare()}
async function loadAnalytics(){
 let d=await fetch("/api/analytics").then(r=>r.json());
 charts.region=new Chart($("regionChart"),{type:"bar",data:{labels:d.regions.map(x=>x.name),datasets:[{label:"Average price (Lakh)",data:d.regions.map(x=>x.avg_price)}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}}});
 charts.type=new Chart($("typeChart"),{type:"doughnut",data:{labels:Object.keys(d.types),datasets:[{data:Object.values(d.types)}]},options:{responsive:true,maintainAspectRatio:false}});
 charts.bhk=new Chart($("bhkChart"),{type:"bar",data:{labels:Object.keys(d.bhk),datasets:[{label:"Properties",data:Object.values(d.bhk)}]},options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:false}}}});
 charts.status=new Chart($("statusChart"),{type:"doughnut",data:{labels:Object.keys(d.status),datasets:[{data:Object.values(d.status)}]},options:{responsive:true,maintainAspectRatio:false}});
}
async function loadMetrics(){
 let d=await fetch("/api/metrics").then(r=>r.json()),m=d.metrics;
 $("metricsTable").innerHTML=`<table><tr><th>Model</th><th>MAE</th><th>RMSE</th><th>R²</th><th>Role</th></tr>`+
 Object.entries(m).map(([n,v])=>`<tr><td><b>${n}</b></td><td>${v.MAE_lakh.toFixed(2)} L</td><td>${v.RMSE_lakh.toFixed(2)} L</td><td>${v.R2.toFixed(4)}</td><td>${n===d.model_used?"Automatically selected":"Evaluated"}</td></tr>`).join("")+"</table>";
}
$("predictBtn").onclick=predict;$("prev").onclick=()=>loadProperties(page-1);$("next").onclick=()=>loadProperties(page+1);
["q","fRegion","fType","fStatus","fAge"].forEach(id=>$(id).addEventListener("input",()=>loadProperties(1)));
$("themeBtn").onclick=()=>{let dark=document.documentElement.getAttribute("data-theme")==="dark";document.documentElement.setAttribute("data-theme",dark?"light":"dark");localStorage.theme=dark?"light":"dark";$("themeBtn").textContent=dark?"☾":"☀"};
if(localStorage.theme==="dark"){document.documentElement.setAttribute("data-theme","dark");$("themeBtn").textContent="☀"}init();