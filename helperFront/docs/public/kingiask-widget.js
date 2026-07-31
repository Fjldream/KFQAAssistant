"use strict";(()=>{var f={enabled:!1,apiBaseUrl:"",apiKey:"",title:"KingIAsk",welcomeText:"\u4F60\u597D\uFF0C\u6211\u53EF\u4EE5\u5E2E\u4F60\u67E5\u8BE2 KF \u4EA7\u54C1\u624B\u518C\u3002",position:"right-bottom",timeoutMs:6e4};function E(i={}){var n,o,a,e,r;let t={...f,...(n=window.KINGIASK_WIDGET_CONFIG)!=null?n:{},...i};return{...t,apiBaseUrl:String((o=t.apiBaseUrl)!=null?o:"").replace(/\/+$/,""),apiKey:String((a=t.apiKey)!=null?a:""),title:String((e=t.title)!=null?e:f.title),welcomeText:String((r=t.welcomeText)!=null?r:f.welcomeText),position:t.position==="left-bottom"?"left-bottom":"right-bottom",timeoutMs:Number(t.timeoutMs||f.timeoutMs)}}function A(i,t){return/^https?:\/\//i.test(t)?t:`${i.apiBaseUrl}/manuals/${t.replace(/^\/+/,"")}`}function K(i){let t=i.replace(/\\/g,"/").replace(/^\/+/,"");return t.toLowerCase().endsWith(".md")?`/${t.replace(/^(helperFront\/docs\/|helperFront\/|docs\/)/,"").replace(/\.md$/i,"")}`:null}async function I(i,t){if(!i.apiBaseUrl)throw new Error("\u52A9\u624B\u914D\u7F6E\u7F3A\u5C11\u670D\u52A1\u5730\u5740\u3002");let n=new AbortController,o=window.setTimeout(()=>n.abort(),i.timeoutMs),a=new Headers({"Content-Type":"application/json"});i.apiKey.trim()&&a.set("X-API-Key",i.apiKey.trim());try{let e=await fetch(`${i.apiBaseUrl}/api/chat`,{method:"POST",headers:a,body:JSON.stringify({question:t}),signal:n.signal});if(e.status===401||e.status===403)throw new Error("\u52A9\u624B\u8BA4\u8BC1\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u914D\u7F6E\u3002");if(!e.ok)throw new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002");return await e.json()}catch(e){throw e instanceof DOMException&&e.name==="AbortError"?new Error("\u8BF7\u6C42\u8D85\u65F6\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5\u3002"):e instanceof Error&&e.message.startsWith("\u52A9\u624B")?e:new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002")}finally{window.clearTimeout(o)}}var T=`
:host { all: initial; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; color: #17212b; }
* { box-sizing: border-box; }
.kiw-root { position: fixed; z-index: 2147483000; bottom: 24px; color: #17212b; }
.kiw-root.right-bottom { right: 24px; }
.kiw-root.left-bottom { left: 24px; }
.kiw-launcher { display: inline-flex; align-items: center; gap: 12px; min-width: 168px; height: 56px; border: 1px solid rgb(255 255 255 / 24%); border-radius: 999px; padding: 8px 16px 8px 8px; background: #1677ff; color: #fff; box-shadow: 0 16px 36px rgb(22 119 255 / 24%), 0 2px 0 rgb(255 255 255 / 18%) inset; cursor: pointer; transition: transform 160ms ease, box-shadow 160ms ease, background 160ms ease; }
.kiw-launcher:hover { transform: translateY(-2px); background: #0958d9; box-shadow: 0 20px 44px rgb(22 119 255 / 30%), 0 2px 0 rgb(255 255 255 / 18%) inset; }
.kiw-launcher:focus-visible, .kiw-close:focus-visible, .kiw-send:focus-visible { outline: 3px solid rgb(22 119 255 / 24%); outline-offset: 2px; }
.kiw-launcher-mark, .kiw-brand-mark { display: grid; place-items: center; width: 40px; height: 40px; border-radius: 14px; background: rgb(255 255 255 / 18%); color: #fff; font-weight: 850; letter-spacing: 0; }
.kiw-launcher-copy { display: grid; gap: 2px; text-align: left; }
.kiw-launcher-title { font-size: 14px; font-weight: 800; line-height: 1.1; }
.kiw-launcher-status { position: relative; padding-left: 10px; color: rgb(255 255 255 / 76%); font-size: 12px; line-height: 1.2; }
.kiw-launcher-status::before { content: ""; position: absolute; left: 0; top: 50%; width: 6px; height: 6px; border-radius: 999px; background: #52c41a; transform: translateY(-50%); box-shadow: 0 0 0 4px rgb(82 196 26 / 16%); }
.kiw-panel { display: none; width: min(440px, calc(100vw - 32px)); height: min(680px, calc(100vh - 88px)); overflow: hidden; border: 1px solid #e5e7eb; border-radius: 18px; background: #f7f9fc; box-shadow: 0 24px 70px rgb(15 23 42 / 18%); }
.kiw-panel.open { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; }
.kiw-header { display: flex; align-items: center; justify-content: space-between; gap: 14px; min-height: 78px; padding: 16px 18px; border-bottom: 1px solid #e5e7eb; background: #fff; }
.kiw-brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.kiw-brand-mark { flex: 0 0 auto; width: 42px; height: 42px; border-radius: 15px; background: #1677ff; box-shadow: inset 0 -10px 16px rgb(0 0 0 / 10%); }
.kiw-title { margin: 0; color: #1f2937; font-size: 16px; font-weight: 850; line-height: 1.2; }
.kiw-subtitle { margin: 3px 0 0; color: #6b7280; font-size: 12px; line-height: 1.35; }
.kiw-close { display: grid; place-items: center; width: 32px; height: 32px; border: 1px solid #e5e7eb; border-radius: 10px; background: #fff; color: #6b7280; cursor: pointer; font-size: 20px; line-height: 1; transition: background 140ms ease, color 140ms ease, border-color 140ms ease; }
.kiw-close:hover { border-color: #d1d5db; background: #f9fafb; color: #1f2937; }
.kiw-messages { display: flex; min-height: 0; flex-direction: column; gap: 14px; overflow: auto; padding: 18px; background: linear-gradient(180deg, #f8fbff 0%, #f3f6fb 100%); scrollbar-width: thin; scrollbar-color: #cbd5e1 transparent; }
.kiw-message { max-width: 92%; border: 1px solid #e5e7eb; border-radius: 16px; padding: 12px 14px; line-height: 1.68; font-size: 14px; white-space: pre-wrap; box-shadow: 0 8px 24px rgb(15 23 42 / 6%); }
.kiw-message-assistant { align-self: flex-start; border-top-left-radius: 6px; background: #fff; color: #1f2937; }
.kiw-message-user { align-self: flex-end; border-color: #1677ff; border-top-right-radius: 6px; background: #1677ff; color: #fff; box-shadow: 0 10px 24px rgb(22 119 255 / 20%); }
.kiw-message-label { margin-bottom: 4px; color: #1677ff; font-size: 12px; font-weight: 800; line-height: 1.2; }
.kiw-answer-text { word-break: break-word; }
.kiw-error, .kiw-loading { align-self: flex-start; max-width: 92%; border-radius: 16px; padding: 12px 14px; line-height: 1.6; font-size: 14px; }
.kiw-error { border: 1px solid #f1c9c4; background: #fff7f6; color: #a23125; white-space: pre-wrap; }
.kiw-loading { display: inline-flex; align-items: center; gap: 10px; border: 1px solid #e5e7eb; background: #fff; color: #4b5563; box-shadow: 0 8px 24px rgb(15 23 42 / 6%); }
.kiw-loading-dots { display: inline-flex; align-items: center; gap: 4px; }
.kiw-loading-dots span { width: 6px; height: 6px; border-radius: 999px; background: #1677ff; animation: kiw-pulse 900ms ease-in-out infinite; }
.kiw-loading-dots span:nth-child(2) { animation-delay: 140ms; }
.kiw-loading-dots span:nth-child(3) { animation-delay: 280ms; }
.kiw-sources { margin-top: 12px; border-top: 1px solid #eef2f7; padding-top: 10px; }
.kiw-sources-heading { margin-bottom: 8px; color: #6b7280; font-size: 12px; font-weight: 800; }
.kiw-source { display: grid; gap: 5px; margin-top: 8px; border: 1px solid #e5e7eb; border-radius: 12px; background: #f8fbff; padding: 10px; color: #4b5563; font-size: 12px; white-space: normal; }
.kiw-source-title { display: block; color: #1f2937; font-size: 13px; font-weight: 800; }
.kiw-source-title-link { text-decoration: none; }
.kiw-source-title-link:hover { color: #1677ff; }
.kiw-source-path { color: #6b7280; word-break: break-all; }
.kiw-source-snippet { color: #4b5563; line-height: 1.55; }
.kiw-source-action { display: inline-flex; width: fit-content; margin-top: 3px; color: #1677ff; font-weight: 800; text-decoration: none; }
.kiw-source-action:hover { color: #0958d9; text-decoration: underline; text-underline-offset: 3px; }
.kiw-source-image { display: inline-flex; width: fit-content; margin-top: 3px; border-radius: 999px; background: #eaf3ff; padding: 4px 9px; color: #1677ff; font-weight: 700; text-decoration: none; }
.kiw-source-image:hover { background: #dcebff; color: #0958d9; }
.kiw-form { padding: 14px; border-top: 1px solid #e5e7eb; background: #fff; }
.kiw-input-shell { display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: end; border: 1px solid #d1d5db; border-radius: 16px; background: #fff; padding: 10px; box-shadow: 0 1px 0 rgb(15 23 42 / 4%) inset; }
.kiw-input-shell:focus-within { border-color: #1677ff; box-shadow: 0 0 0 4px rgb(22 119 255 / 12%); }
.kiw-input { width: 100%; min-height: 58px; max-height: 120px; resize: none; border: 0; padding: 2px 0; background: transparent; color: #17212b; font: inherit; line-height: 1.55; outline: none; }
.kiw-input::placeholder { color: #9aa8a5; }
.kiw-send { min-width: 64px; min-height: 38px; border: 0; border-radius: 12px; background: #1677ff; color: #fff; cursor: pointer; font-weight: 800; transition: transform 140ms ease, background 140ms ease, opacity 140ms ease; }
.kiw-send:hover:not(:disabled) { transform: translateY(-1px); background: #0958d9; }
.kiw-send:disabled { cursor: not-allowed; opacity: 0.58; }
@keyframes kiw-pulse { 0%, 80%, 100% { transform: translateY(0); opacity: 0.36; } 40% { transform: translateY(-3px); opacity: 1; } }
@media (max-width: 520px) {
  .kiw-root { right: 14px; bottom: 14px; left: 14px; }
  .kiw-root.left-bottom { left: 14px; }
  .kiw-launcher { min-width: 0; width: 100%; justify-content: center; }
  .kiw-panel { width: 100%; height: min(620px, calc(100vh - 28px)); border-radius: 16px; }
}
`;function d(i,t,n){let o=document.createElement(i);return o.className=t,o.textContent=n,o}function N(i,t){let n=K(t.source_path),o=document.createElement("div");o.className="kiw-source",n&&o.classList.add("kiw-source-link");let a=t.title||t.source_path;if(n){let e=document.createElement("a");e.className="kiw-source-title kiw-source-title-link",e.href=n,e.textContent=a,o.appendChild(e)}else o.appendChild(d("strong","kiw-source-title",a));if(o.appendChild(d("div","kiw-source-path",t.source_path)),o.appendChild(d("div","kiw-source-snippet",t.snippet)),n){let e=document.createElement("a");e.className="kiw-source-action",e.href=n,e.textContent="\u67E5\u770B\u539F\u6587",o.appendChild(e)}return t.images.slice(0,3).forEach((e,r)=>{let l=document.createElement("a");l.className="kiw-source-image",l.href=A(i,e),l.target="_blank",l.rel="noopener noreferrer",l.textContent=`\u76F8\u5173\u56FE\u7247 ${r+1}`,o.appendChild(l)}),o}function z(i,t,n){let o=document.createElement("article");if(o.className="kiw-message kiw-message-assistant",o.appendChild(d("div","kiw-message-label","KingIAsk")),o.appendChild(d("div","kiw-answer-text",n.answer)),n.sources.length>0){let a=document.createElement("section");a.className="kiw-sources",a.appendChild(d("div","kiw-sources-heading","\u8D44\u6599\u6765\u6E90")),n.sources.slice(0,3).forEach(e=>a.appendChild(N(i,e))),o.appendChild(a)}t.appendChild(o),t.scrollTop=t.scrollHeight}function R(){let i=document.createElement("div");return i.className="kiw-loading",i.setAttribute("aria-live","polite"),i.innerHTML=`
    <span class="kiw-loading-text">\u6B63\u5728\u68C0\u7D22\u8D44\u6599</span>
    <span class="kiw-loading-dots" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
  `,i}function L(i){var v,C;if(!i.enabled)return null;let t=document.createElement("div");t.setAttribute("data-kingiask-widget-root","true");let n=t.attachShadow({mode:"open"}),o=document.createElement("style");o.textContent=T;let a=document.createElement("div");a.className=`kiw-root ${i.position}`;let e=document.createElement("button");e.className="kiw-launcher",e.type="button",e.dataset.role="launcher",e.setAttribute("aria-label",`\u6253\u5F00 ${i.title} \u52A9\u624B`),e.innerHTML=`
    <span class="kiw-launcher-mark" aria-hidden="true">K</span>
    <span class="kiw-launcher-copy">
      <span class="kiw-launcher-title"></span>
      <span class="kiw-launcher-status">\u52A9\u624B\u5728\u7EBF</span>
    </span>
  `,e.querySelector(".kiw-launcher-title").textContent=i.title;let r=document.createElement("section");r.className="kiw-panel",r.dataset.role="panel",r.setAttribute("role","dialog"),r.setAttribute("aria-labelledby","kiw-title"),r.innerHTML=`
    <header class="kiw-header">
      <div class="kiw-brand">
        <span class="kiw-brand-mark" aria-hidden="true">K</span>
        <div>
          <h2 class="kiw-title" id="kiw-title"></h2>
          <p class="kiw-subtitle">\u4F01\u4E1A\u77E5\u8BC6\u95EE\u7B54\u52A9\u624B \xB7 \u52A9\u624B\u5728\u7EBF</p>
        </div>
      </div>
      <button class="kiw-close" type="button" aria-label="\u5173\u95ED KingIAsk">\xD7</button>
    </header>
    <div class="kiw-messages"></div>
    <form class="kiw-form">
      <div class="kiw-input-shell">
        <textarea class="kiw-input" data-role="question" placeholder="\u8F93\u5165 KF \u4EA7\u54C1\u4F7F\u7528\u95EE\u9898"></textarea>
        <button class="kiw-send" data-role="send" type="submit">\u53D1\u9001</button>
      </div>
    </form>
  `,r.querySelector(".kiw-title").textContent=i.title;let l=r.querySelector(".kiw-messages"),c=r.querySelector("[data-role='question']"),k=r.querySelector("[data-role='send']"),g=document.createElement("article");g.className="kiw-message kiw-message-assistant",g.appendChild(d("div","kiw-message-label","KingIAsk")),g.appendChild(d("div","kiw-answer-text",i.welcomeText)),l.appendChild(g);let S=()=>{r.classList.add("open"),e.setAttribute("aria-expanded","true"),e.style.display="none",c.focus()},M=()=>{r.classList.remove("open"),e.setAttribute("aria-expanded","false"),e.style.display=""},b=s=>{c.disabled=s,k.disabled=s,k.textContent=s?"\u5904\u7406\u4E2D":"\u53D1\u9001"},y=async()=>{let s=c.value.trim();if(!s)return;c.value="";let m=document.createElement("article");m.className="kiw-message kiw-message-user",m.appendChild(d("div","kiw-answer-text",s)),l.appendChild(m);let w=R();l.appendChild(w),b(!0);try{let u=await I(i,s);w.remove(),z(i,l,u)}catch(u){w.remove();let W=u instanceof Error?u.message:"\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002";l.appendChild(d("div","kiw-error",W))}finally{b(!1)}};return e.addEventListener("click",S),(v=r.querySelector(".kiw-close"))==null||v.addEventListener("click",M),(C=r.querySelector("form"))==null||C.addEventListener("submit",s=>{s.preventDefault(),y()}),c.addEventListener("keydown",s=>{s.key==="Enter"&&!s.shiftKey&&!s.isComposing&&(s.preventDefault(),y())}),a.append(e,r),n.append(o,a),document.body.appendChild(t),{destroy:()=>t.remove()}}var p=null,h=document.readyState==="loading";function x(i){h=!1,p==null||p.destroy();let t=E(i);p=L(t)}function H(){h=!1,p==null||p.destroy(),p=null}var U={init:x,destroy:H};window.KingIAskWidget=U;document.readyState==="loading"?document.addEventListener("DOMContentLoaded",()=>{h&&x()},{once:!0}):x();})();
