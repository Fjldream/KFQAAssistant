"use strict";(()=>{var m={enabled:!1,apiBaseUrl:"",apiKey:"",title:"KingIAsk",welcomeText:"\u4F60\u597D\uFF0C\u6211\u53EF\u4EE5\u5E2E\u4F60\u67E5\u8BE2 KF \u4EA7\u54C1\u624B\u518C\u3002",position:"right-bottom",timeoutMs:6e4,persistSession:!0};function C(e={}){var n,i,s,o,r;let t={...m,...(n=window.KINGIASK_WIDGET_CONFIG)!=null?n:{},...e};return{...t,apiBaseUrl:String((i=t.apiBaseUrl)!=null?i:"").replace(/\/+$/,""),apiKey:String((s=t.apiKey)!=null?s:""),title:String((o=t.title)!=null?o:m.title),welcomeText:String((r=t.welcomeText)!=null?r:m.welcomeText),position:t.position==="left-bottom"?"left-bottom":"right-bottom",timeoutMs:Number(t.timeoutMs||m.timeoutMs),persistSession:t.persistSession!==!1}}function E(e,t){return/^https?:\/\//i.test(t)?t:`${e.apiBaseUrl}/manuals/${t.replace(/^\/+/,"")}`}function A(e){let t=e.replace(/\\/g,"/").replace(/^\/+/,"");return t.toLowerCase().endsWith(".md")?`/${t.replace(/^(helperFront\/docs\/|helperFront\/|docs\/)/,"").replace(/\.md$/i,"")}`:null}async function K(e,t){if(!e.apiBaseUrl)throw new Error("\u52A9\u624B\u914D\u7F6E\u7F3A\u5C11\u670D\u52A1\u5730\u5740\u3002");let n=new AbortController,i=window.setTimeout(()=>n.abort(),e.timeoutMs),s=new Headers({"Content-Type":"application/json"});e.apiKey.trim()&&s.set("X-API-Key",e.apiKey.trim());try{let o=await fetch(`${e.apiBaseUrl}/api/chat`,{method:"POST",headers:s,body:JSON.stringify({question:t}),signal:n.signal});if(o.status===401||o.status===403)throw new Error("\u52A9\u624B\u8BA4\u8BC1\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u914D\u7F6E\u3002");if(!o.ok)throw new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002");return await o.json()}catch(o){throw o instanceof DOMException&&o.name==="AbortError"?new Error("\u8BF7\u6C42\u8D85\u65F6\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5\u3002"):o instanceof Error&&o.message.startsWith("\u52A9\u624B")?o:new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002")}finally{window.clearTimeout(i)}}var I=`
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
.kiw-source-header { display: flex; align-items: center; gap: 8px; min-width: 0; }
.kiw-source-badge { flex: 0 0 auto; border-radius: 999px; background: #eaf3ff; padding: 3px 8px; color: #1677ff; font-size: 12px; font-weight: 800; line-height: 1.35; }
.kiw-source-title { display: block; min-width: 0; color: #1f2937; font-size: 13px; font-weight: 800; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kiw-source-title-link { text-decoration: none; }
.kiw-source-title-link:hover { color: #1677ff; }
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
`;var W="kingiask-widget:conversation:v1",U=40;function d(e,t,n){let i=document.createElement(e);return i.className=t,i.textContent=n,i}function _(e){if(!e.persistSession)return[];try{let t=window.sessionStorage.getItem(W);if(!t)return[];let n=JSON.parse(t);return Array.isArray(n)?n.filter(i=>{var s,o;return(i==null?void 0:i.role)==="user"?typeof i.text=="string":(i==null?void 0:i.role)==="assistant"?typeof((s=i.response)==null?void 0:s.answer)=="string"&&Array.isArray((o=i.response)==null?void 0:o.sources):!1}):[]}catch{return[]}}function T(e,t){if(e.persistSession)try{window.sessionStorage.setItem(W,JSON.stringify(t.slice(-U)))}catch{}}function M(e,t){let n=document.createElement("article");n.className="kiw-message kiw-message-user",n.appendChild(d("div","kiw-answer-text",t)),e.appendChild(n),e.scrollTop=e.scrollHeight}function P(e){var t;return(t=e.evidence_ids.find(n=>n.trim()))!=null?t:"\u8D44\u6599"}function B(e){return(e.title||e.source_path).replace(/\\/g,"/").replace(/\.md$/i,"").split("/").filter(Boolean).at(-1)||"\u76F8\u5173\u8D44\u6599"}function O(e){return e.snippet.split(/\r?\n/).filter(t=>{let n=t.trim();return!/^#*\s*(helperFront\/|docs\/).+\.md?$/i.test(n)&&!/^#*\s*(helperFront\/|docs\/)/i.test(n)}).join(`
`).trim()}function $(e,t){let n=A(t.source_path),i=document.createElement("div");i.className="kiw-source",n&&i.classList.add("kiw-source-link");let s=P(t),o=B(t),r=document.createElement("div");if(r.className="kiw-source-header",r.appendChild(d("span","kiw-source-badge",s)),n){let a=document.createElement("a");a.className="kiw-source-title kiw-source-title-link",a.href=n,a.textContent=o,r.appendChild(a)}else r.appendChild(d("strong","kiw-source-title",o));if(i.appendChild(r),i.appendChild(d("div","kiw-source-snippet",O(t))),n){let a=document.createElement("a");a.className="kiw-source-action",a.href=n,a.textContent="\u67E5\u770B\u539F\u6587",i.appendChild(a)}return t.images.slice(0,3).forEach((a,u)=>{let p=document.createElement("a");p.className="kiw-source-image",p.href=E(e,a),p.target="_blank",p.rel="noopener noreferrer",p.textContent=`\u76F8\u5173\u56FE\u7247 ${u+1}`,i.appendChild(p)}),i}function L(e,t,n){let i=document.createElement("article");if(i.className="kiw-message kiw-message-assistant",i.appendChild(d("div","kiw-message-label","KingIAsk")),i.appendChild(d("div","kiw-answer-text",n.answer)),n.sources.length>0){let s=document.createElement("section");s.className="kiw-sources",s.appendChild(d("div","kiw-sources-heading","\u8D44\u6599\u6765\u6E90")),n.sources.slice(0,3).forEach(o=>s.appendChild($(e,o))),i.appendChild(s)}t.appendChild(i),t.scrollTop=t.scrollHeight}function q(){let e=document.createElement("div");return e.className="kiw-loading",e.setAttribute("aria-live","polite"),e.innerHTML=`
    <span class="kiw-loading-text">\u6B63\u5728\u68C0\u7D22\u8D44\u6599</span>
    <span class="kiw-loading-dots" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
  `,e}function N(e){var v,S;if(!e.enabled)return null;let t=document.createElement("div");t.setAttribute("data-kingiask-widget-root","true");let n=t.attachShadow({mode:"open"}),i=document.createElement("style");i.textContent=I;let s=document.createElement("div");s.className=`kiw-root ${e.position}`;let o=document.createElement("button");o.className="kiw-launcher",o.type="button",o.dataset.role="launcher",o.setAttribute("aria-label",`\u6253\u5F00 ${e.title} \u52A9\u624B`),o.innerHTML=`
    <span class="kiw-launcher-mark" aria-hidden="true">K</span>
    <span class="kiw-launcher-copy">
      <span class="kiw-launcher-title"></span>
      <span class="kiw-launcher-status">\u52A9\u624B\u5728\u7EBF</span>
    </span>
  `,o.querySelector(".kiw-launcher-title").textContent=e.title;let r=document.createElement("section");r.className="kiw-panel",r.dataset.role="panel",r.setAttribute("role","dialog"),r.setAttribute("aria-labelledby","kiw-title"),r.innerHTML=`
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
  `,r.querySelector(".kiw-title").textContent=e.title;let a=r.querySelector(".kiw-messages"),u=r.querySelector("[data-role='question']"),p=r.querySelector("[data-role='send']"),g=_(e),w=document.createElement("article");w.className="kiw-message kiw-message-assistant",w.appendChild(d("div","kiw-message-label","KingIAsk")),w.appendChild(d("div","kiw-answer-text",e.welcomeText)),a.appendChild(w),g.forEach(l=>{l.role==="user"?M(a,l.text):L(e,a,l.response)});let R=()=>{r.classList.add("open"),o.setAttribute("aria-expanded","true"),o.style.display="none",u.focus()},z=()=>{r.classList.remove("open"),o.setAttribute("aria-expanded","false"),o.style.display=""},b=l=>{u.disabled=l,p.disabled=l,p.textContent=l?"\u5904\u7406\u4E2D":"\u53D1\u9001"},y=async()=>{let l=u.value.trim();if(!l)return;u.value="",M(a,l),g.push({role:"user",text:l}),T(e,g);let h=q();a.appendChild(h),b(!0);try{let f=await K(e,l);h.remove(),L(e,a,f),g.push({role:"assistant",response:f}),T(e,g)}catch(f){h.remove();let H=f instanceof Error?f.message:"\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002";a.appendChild(d("div","kiw-error",H))}finally{b(!1)}};return o.addEventListener("click",R),(v=r.querySelector(".kiw-close"))==null||v.addEventListener("click",z),(S=r.querySelector("form"))==null||S.addEventListener("submit",l=>{l.preventDefault(),y()}),u.addEventListener("keydown",l=>{l.key==="Enter"&&!l.shiftKey&&!l.isComposing&&(l.preventDefault(),y())}),s.append(o,r),n.append(i,s),document.body.appendChild(t),{destroy:()=>t.remove()}}var c=null,k=document.readyState==="loading";function x(e){k=!1,c==null||c.destroy();let t=C(e);c=N(t)}function F(){k=!1,c==null||c.destroy(),c=null}var D={init:x,destroy:F};window.KingIAskWidget=D;document.readyState==="loading"?document.addEventListener("DOMContentLoaded",()=>{k&&x()},{once:!0}):x();})();
