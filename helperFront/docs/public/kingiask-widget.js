"use strict";(()=>{var m={enabled:!1,apiBaseUrl:"",apiKey:"",title:"KingIAsk",welcomeText:"\u4F60\u597D\uFF0C\u6211\u53EF\u4EE5\u5E2E\u4F60\u67E5\u8BE2 KF \u4EA7\u54C1\u624B\u518C\u3002",position:"right-bottom",timeoutMs:6e4,persistSession:!0};function A(e={}){var a,i,s,r,o;let t={...m,...(a=window.KINGIASK_WIDGET_CONFIG)!=null?a:{},...e};return{...t,apiBaseUrl:String((i=t.apiBaseUrl)!=null?i:"").replace(/\/+$/,""),apiKey:String((s=t.apiKey)!=null?s:""),title:String((r=t.title)!=null?r:m.title),welcomeText:String((o=t.welcomeText)!=null?o:m.welcomeText),position:t.position==="left-bottom"?"left-bottom":"right-bottom",timeoutMs:Number(t.timeoutMs||m.timeoutMs),persistSession:t.persistSession!==!1}}function K(e,t){return/^https?:\/\//i.test(t)?t:`${e.apiBaseUrl}/manuals/${t.replace(/^\/+/,"")}`}function I(e){let t=e.replace(/\\/g,"/").replace(/^\/+/,"");return t.toLowerCase().endsWith(".md")?`/${t.replace(/^(helperFront\/docs\/|helperFront\/|docs\/)/,"").replace(/\.md$/i,"")}`:null}async function T(e,t){if(!e.apiBaseUrl)throw new Error("\u52A9\u624B\u914D\u7F6E\u7F3A\u5C11\u670D\u52A1\u5730\u5740\u3002");let a=new AbortController,i=window.setTimeout(()=>a.abort(),e.timeoutMs),s=new Headers({"Content-Type":"application/json"});e.apiKey.trim()&&s.set("X-API-Key",e.apiKey.trim());try{let r=await fetch(`${e.apiBaseUrl}/api/chat`,{method:"POST",headers:s,body:JSON.stringify({question:t}),signal:a.signal});if(r.status===401||r.status===403)throw new Error("\u52A9\u624B\u8BA4\u8BC1\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u914D\u7F6E\u3002");if(!r.ok)throw new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002");return await r.json()}catch(r){throw r instanceof DOMException&&r.name==="AbortError"?new Error("\u8BF7\u6C42\u8D85\u65F6\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5\u3002"):r instanceof Error&&r.message.startsWith("\u52A9\u624B")?r:new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002")}finally{window.clearTimeout(i)}}var M=`
/* ============================================================
   KingIAsk Widget \xB7 Apple \u98CE\u683C
   - \u73BB\u7483\u8D28\u611F\uFF08backdrop-filter blur + saturate\uFF09
   - \u6D45\u8272 / \u6DF1\u8272\u81EA\u9002\u5E94\uFF08prefers-color-scheme\uFF09
   - iOS spring \u7F13\u52A8\uFF08--kiw-ease-drawer\uFF09
   - SF Pro \u7CFB\u7EDF\u5B57\u4F53 + \u8D1F tracking
   ============================================================ */
:host {
  all: initial;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;

  /* \u6D45\u8272 tokens */
  --kiw-bg: #f5f5f7;
  --kiw-surface: rgba(255, 255, 255, 0.78);
  --kiw-surface-solid: #ffffff;
  --kiw-surface-muted: rgba(118, 118, 128, 0.09);
  --kiw-border: rgba(0, 0, 0, 0.08);
  --kiw-border-strong: rgba(0, 0, 0, 0.16);
  --kiw-text: #1d1d1f;
  --kiw-text-secondary: #6e6e73;
  --kiw-text-tertiary: #86868b;
  --kiw-accent: #0071e3;
  --kiw-accent-strong: #0060c9;
  --kiw-accent-soft: rgba(0, 113, 227, 0.1);
  --kiw-accent-ring: rgba(0, 113, 227, 0.22);
  --kiw-user-bubble: #0a84ff;
  --kiw-on-accent: #ffffff;
  --kiw-green: #34c759;
  --kiw-green-soft: rgba(52, 199, 89, 0.16);
  --kiw-red: #ff3b30;
  --kiw-red-soft: rgba(255, 59, 48, 0.12);
  --kiw-shadow-soft: 0 1px 2px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.06);
  --kiw-shadow-pop: 0 8px 24px rgba(0, 0, 0, 0.14), 0 40px 90px rgba(0, 0, 0, 0.2);

  /* iOS spring \u7F13\u52A8 */
  --kiw-ease-drawer: cubic-bezier(0.32, 0.72, 0, 1);
  --kiw-ease-out: cubic-bezier(0.22, 1, 0.36, 1);

  color: var(--kiw-text);
  color-scheme: light;
  -webkit-font-smoothing: antialiased;
}

@media (prefers-color-scheme: dark) {
  :host {
    --kiw-bg: #000000;
    --kiw-surface: rgba(28, 28, 30, 0.8);
    --kiw-surface-solid: #1c1c1e;
    --kiw-surface-muted: rgba(255, 255, 255, 0.08);
    --kiw-border: rgba(255, 255, 255, 0.12);
    --kiw-border-strong: rgba(255, 255, 255, 0.22);
    --kiw-text: #f5f5f7;
    --kiw-text-secondary: #98989d;
    --kiw-text-tertiary: #6e6e73;
    --kiw-accent: #2997ff;
    --kiw-accent-strong: #5ab0ff;
    --kiw-accent-soft: rgba(41, 151, 255, 0.16);
    --kiw-accent-ring: rgba(41, 151, 255, 0.34);
    --kiw-user-bubble: #0a84ff;
    --kiw-on-accent: #ffffff;
    --kiw-green: #30d158;
    --kiw-green-soft: rgba(48, 209, 88, 0.18);
    --kiw-red: #ff453a;
    --kiw-red-soft: rgba(255, 69, 58, 0.16);
    --kiw-shadow-soft: 0 1px 2px rgba(0, 0, 0, 0.4), 0 8px 24px rgba(0, 0, 0, 0.4);
    --kiw-shadow-pop: 0 10px 30px rgba(0, 0, 0, 0.55), 0 48px 100px rgba(0, 0, 0, 0.6);
    color-scheme: dark;
  }
}

* { box-sizing: border-box; }

/* \u2014\u2014 \u6D6E\u52A8\u5165\u53E3 \u2014\u2014 */
.kiw-root { position: fixed; z-index: 2147483000; bottom: 24px; }
.kiw-root.right-bottom { right: 24px; }
.kiw-root.left-bottom { left: 24px; }

.kiw-launcher {
  display: inline-flex; align-items: center; gap: 12px; min-width: 172px; height: 56px;
  border: 1px solid rgba(255, 255, 255, 0.28); border-radius: 999px; padding: 8px 18px 8px 8px;
  background: linear-gradient(135deg, var(--kiw-accent) 0%, #5ac8fa 100%);
  color: var(--kiw-on-accent); cursor: pointer;
  box-shadow: 0 14px 34px var(--kiw-accent-ring), 0 2px 0 rgba(255, 255, 255, 0.22) inset;
  transition: transform 180ms var(--kiw-ease-out), box-shadow 180ms ease, background 180ms ease;
}
.kiw-launcher:hover { transform: translateY(-2px); box-shadow: 0 18px 44px var(--kiw-accent-ring), 0 2px 0 rgba(255, 255, 255, 0.22) inset; }
.kiw-launcher:active { transform: scale(0.96); transition-duration: 100ms; }

.kiw-launcher-mark, .kiw-brand-mark {
  display: grid; place-items: center; width: 40px; height: 40px;
  border-radius: 14px; background: rgba(255, 255, 255, 0.24); color: var(--kiw-on-accent);
  font-weight: 850; font-size: 18px; letter-spacing: -0.02em;
  -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
}
.kiw-launcher-copy { display: grid; gap: 2px; text-align: left; }
.kiw-launcher-title { font-size: 14px; font-weight: 800; letter-spacing: -0.01em; line-height: 1.15; }
.kiw-launcher-status {
  position: relative; padding-left: 10px; color: rgba(255, 255, 255, 0.82);
  font-size: 11.5px; font-weight: 550; line-height: 1.2;
}
.kiw-launcher-status::before {
  content: ""; position: absolute; left: 0; top: 50%; width: 6px; height: 6px;
  border-radius: 999px; background: #34c759; transform: translateY(-50%);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.28);
}

/* \u2014\u2014 \u9762\u677F \u2014\u2014 */
.kiw-panel {
  display: none; width: min(440px, calc(100vw - 32px)); height: min(680px, calc(100vh - 88px));
  overflow: hidden; border: 1px solid var(--kiw-border); border-radius: 24px;
  background: var(--kiw-surface); color: var(--kiw-text);
  -webkit-backdrop-filter: blur(28px) saturate(190%); backdrop-filter: blur(28px) saturate(190%);
  box-shadow: var(--kiw-shadow-pop);
}
.kiw-panel.open {
  display: grid; grid-template-rows: auto minmax(0, 1fr) auto;
  animation: kiw-panel-in 300ms var(--kiw-ease-drawer) both;
  transform-origin: bottom center;
}

/* \u2014\u2014 \u5934\u90E8 \u2014\u2014 */
.kiw-header {
  display: flex; align-items: center; justify-content: space-between; gap: 14px;
  min-height: 78px; padding: 16px 20px; border-bottom: 1px solid var(--kiw-border);
  background: var(--kiw-surface);
  -webkit-backdrop-filter: blur(24px) saturate(180%); backdrop-filter: blur(24px) saturate(180%);
}
.kiw-brand { display: flex; align-items: center; gap: 12px; min-width: 0; }
.kiw-brand-mark {
  flex: 0 0 auto; width: 42px; height: 42px; border-radius: 15px;
  background: linear-gradient(135deg, var(--kiw-accent) 0%, #5ac8fa 100%);
  box-shadow: 0 6px 16px var(--kiw-accent-ring);
}
.kiw-title { margin: 0; color: var(--kiw-text); font-size: 16px; font-weight: 800; letter-spacing: -0.015em; line-height: 1.2; }
.kiw-subtitle { margin: 3px 0 0; color: var(--kiw-text-secondary); font-size: 12px; line-height: 1.35; }
.kiw-close {
  display: grid; place-items: center; width: 32px; height: 32px; flex: 0 0 auto;
  border: 1px solid var(--kiw-border); border-radius: 999px; background: var(--kiw-surface-muted);
  color: var(--kiw-text-secondary); cursor: pointer; font-size: 19px; line-height: 1;
  transition: background 150ms ease, color 150ms ease, border-color 150ms ease, transform 150ms var(--kiw-ease-out);
}
.kiw-close:hover { border-color: var(--kiw-border-strong); background: var(--kiw-surface-muted); color: var(--kiw-text); }
.kiw-close:active { transform: scale(0.9); }

/* \u2014\u2014 \u6D88\u606F\u533A \u2014\u2014 */
.kiw-messages {
  display: flex; min-height: 0; flex-direction: column; gap: 14px; overflow: auto; padding: 20px;
  background: var(--kiw-bg);
  scrollbar-width: thin; scrollbar-color: var(--kiw-border-strong) transparent;
}
.kiw-message {
  max-width: 92%; border: 1px solid var(--kiw-border); border-radius: 20px;
  padding: 12px 15px; line-height: 1.7; font-size: 14px; white-space: pre-wrap;
  box-shadow: var(--kiw-shadow-soft);
  animation: kiw-msg-in 240ms var(--kiw-ease-out) both;
}
.kiw-message:nth-child(2) { animation-delay: 30ms; }
.kiw-message:nth-child(3) { animation-delay: 60ms; }
.kiw-message:nth-child(4) { animation-delay: 90ms; }
.kiw-message:nth-child(n + 5) { animation-delay: 120ms; }
.kiw-message-assistant {
  align-self: flex-start; border-top-left-radius: 7px;
  background: var(--kiw-surface-solid); color: var(--kiw-text);
}
.kiw-message-user {
  align-self: flex-end; border-color: transparent; border-top-right-radius: 7px;
  background: var(--kiw-user-bubble); color: var(--kiw-on-accent);
  box-shadow: 0 10px 24px var(--kiw-accent-ring);
}
.kiw-message-label { margin-bottom: 5px; color: var(--kiw-accent); font-size: 12px; font-weight: 800; line-height: 1.2; letter-spacing: -0.01em; }
.kiw-answer-text { word-break: break-word; }

/* \u2014\u2014 \u9519\u8BEF / \u52A0\u8F7D \u2014\u2014 */
.kiw-error, .kiw-loading {
  align-self: flex-start; max-width: 92%; border-radius: 18px; padding: 12px 15px;
  line-height: 1.65; font-size: 14px; animation: kiw-msg-in 240ms var(--kiw-ease-out) both;
}
.kiw-error {
  border: 1px solid var(--kiw-red-soft); background: var(--kiw-red-soft);
  color: var(--kiw-red); white-space: pre-wrap;
}
.kiw-loading {
  display: inline-flex; align-items: center; gap: 10px;
  border: 1px solid var(--kiw-border); background: var(--kiw-surface-solid);
  color: var(--kiw-text-secondary);
  box-shadow: var(--kiw-shadow-soft);
}
.kiw-loading-dots { display: inline-flex; align-items: center; gap: 4px; }
.kiw-loading-dots span {
  width: 6px; height: 6px; border-radius: 999px; background: var(--kiw-accent);
  animation: kiw-pulse 1.05s var(--kiw-ease-out) infinite;
}
.kiw-loading-dots span:nth-child(2) { animation-delay: 140ms; }
.kiw-loading-dots span:nth-child(3) { animation-delay: 280ms; }

/* \u2014\u2014 \u8D44\u6599\u6765\u6E90 \u2014\u2014 */
.kiw-sources { margin-top: 13px; border-top: 1px solid var(--kiw-border); padding-top: 11px; }
.kiw-sources-heading {
  margin-bottom: 8px; color: var(--kiw-text-tertiary);
  font-size: 11px; font-weight: 800; letter-spacing: 0.06em; text-transform: uppercase;
}
.kiw-source {
  display: grid; gap: 5px; margin-top: 8px; border: 1px solid var(--kiw-border);
  border-radius: 14px; background: var(--kiw-surface-muted); padding: 11px;
  color: var(--kiw-text-secondary); font-size: 12px; white-space: normal;
  transition: border-color 150ms ease, background-color 150ms ease;
}
.kiw-source:hover { border-color: var(--kiw-accent-ring); }
.kiw-source-header { display: flex; align-items: center; gap: 8px; min-width: 0; }
.kiw-source-badge {
  flex: 0 0 auto; border-radius: 999px; background: var(--kiw-accent-soft);
  padding: 3px 9px; color: var(--kiw-accent); font-size: 12px; font-weight: 800; line-height: 1.35;
}
.kiw-source-title {
  display: block; min-width: 0; color: var(--kiw-text); font-size: 13px;
  font-weight: 700; letter-spacing: -0.01em;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.kiw-source-title-link { text-decoration: none; }
.kiw-source-title-link:hover { color: var(--kiw-accent); }
.kiw-source-snippet { color: var(--kiw-text-secondary); line-height: 1.6; }
.kiw-source-action {
  display: inline-flex; width: fit-content; margin-top: 3px; color: var(--kiw-accent);
  font-weight: 800; text-decoration: none;
}
.kiw-source-action:hover { color: var(--kiw-accent-strong); text-decoration: underline; text-underline-offset: 3px; }
.kiw-source-image {
  display: inline-flex; width: fit-content; margin-top: 3px; border-radius: 999px;
  background: var(--kiw-accent-soft); padding: 4px 10px; color: var(--kiw-accent);
  font-weight: 700; text-decoration: none;
}
.kiw-source-image:hover { background: var(--kiw-accent-ring); color: var(--kiw-accent-strong); }

/* \u2014\u2014 \u8F93\u5165\u533A \u2014\u2014 */
.kiw-form {
  padding: 13px 14px 14px; border-top: 1px solid var(--kiw-border);
  background: var(--kiw-surface);
  -webkit-backdrop-filter: blur(24px) saturate(180%); backdrop-filter: blur(24px) saturate(180%);
}
.kiw-input-shell {
  display: grid; grid-template-columns: minmax(0, 1fr) auto; gap: 10px; align-items: end;
  border: 1px solid var(--kiw-border-strong); border-radius: 18px;
  background: var(--kiw-surface-solid); padding: 9px 9px 9px 13px;
  box-shadow: 0 1px 0 rgba(0, 0, 0, 0.04) inset;
  transition: border-color 180ms ease, box-shadow 180ms ease;
}
.kiw-input-shell:focus-within {
  border-color: var(--kiw-accent);
  box-shadow: 0 0 0 4px var(--kiw-accent-soft);
}
.kiw-input {
  width: 100%; min-height: 56px; max-height: 120px; resize: none; border: 0; padding: 4px 0;
  background: transparent; color: var(--kiw-text); font: inherit; line-height: 1.55; outline: none;
}
.kiw-input::placeholder { color: var(--kiw-text-tertiary); }
.kiw-send {
  min-width: 64px; min-height: 38px; border: 0; border-radius: 999px;
  background: var(--kiw-accent); color: var(--kiw-on-accent); cursor: pointer; font-weight: 750;
  letter-spacing: -0.01em;
  box-shadow: 0 4px 12px var(--kiw-accent-ring);
  transition: transform 160ms var(--kiw-ease-out), background 160ms ease, opacity 160ms ease;
}
.kiw-send:hover:not(:disabled) { background: var(--kiw-accent-strong); transform: translateY(-1px); }
.kiw-send:active:not(:disabled) { transform: scale(0.96); transition-duration: 100ms; }
.kiw-send:disabled { cursor: not-allowed; opacity: 0.55; }

/* \u2014\u2014 \u7126\u70B9\u53EF\u89C1 \u2014\u2014 */
.kiw-launcher:focus-visible, .kiw-close:focus-visible, .kiw-send:focus-visible,
.kiw-source-title-link:focus-visible, .kiw-source-action:focus-visible, .kiw-source-image:focus-visible {
  outline: 3px solid var(--kiw-accent-ring); outline-offset: 2px;
}

/* \u2014\u2014 \u52A8\u753B \u2014\u2014 */
@keyframes kiw-panel-in {
  from { opacity: 0; transform: translateY(14px) scale(0.97); }
  to { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes kiw-msg-in {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes kiw-pulse {
  0%, 60%, 100% { transform: translateY(0); opacity: 0.4; }
  30% { transform: translateY(-3px); opacity: 1; }
}

/* \u2014\u2014 \u79FB\u52A8\u7AEF \u2014\u2014 */
@media (max-width: 520px) {
  .kiw-root { right: 14px; bottom: 14px; left: 14px; }
  .kiw-root.left-bottom { left: 14px; }
  .kiw-launcher { min-width: 0; width: 100%; justify-content: center; }
  .kiw-panel { width: 100%; height: min(620px, calc(100vh - 28px)); border-radius: 22px; }
}

/* \u2014\u2014 \u51CF\u5C11\u52A8\u6548 \u2014\u2014 */
@media (prefers-reduced-motion: reduce) {
  .kiw-panel.open, .kiw-message, .kiw-error, .kiw-loading,
  .kiw-loading-dots span { animation: none; }
}
`;var z="kingiask-widget:conversation:v1",F=40;function d(e,t,a){let i=document.createElement(e);return i.className=t,i.textContent=a,i}function O(e){if(!e.persistSession)return[];try{let t=window.sessionStorage.getItem(z);if(!t)return[];let a=JSON.parse(t);return Array.isArray(a)?a.filter(i=>{var s,r;return(i==null?void 0:i.role)==="user"?typeof i.text=="string":(i==null?void 0:i.role)==="assistant"?typeof((s=i.response)==null?void 0:s.answer)=="string"&&Array.isArray((r=i.response)==null?void 0:r.sources):!1}):[]}catch{return[]}}function L(e,t){if(e.persistSession)try{window.sessionStorage.setItem(z,JSON.stringify(t.slice(-F)))}catch{}}function W(e,t){let a=document.createElement("article");a.className="kiw-message kiw-message-user",a.appendChild(d("div","kiw-answer-text",t)),e.appendChild(a),e.scrollTop=e.scrollHeight}function U(e){var t;return(t=e.evidence_ids.find(a=>a.trim()))!=null?t:"\u8D44\u6599"}function Y(e){return(e.title||e.source_path).replace(/\\/g,"/").replace(/\.md$/i,"").split("/").filter(Boolean).at(-1)||"\u76F8\u5173\u8D44\u6599"}function _(e){return e.snippet.split(/\r?\n/).filter(t=>{let a=t.trim();return!/^#*\s*(helperFront\/|docs\/).+\.md?$/i.test(a)&&!/^#*\s*(helperFront\/|docs\/)/i.test(a)}).join(`
`).trim()}function B(e,t){let a=I(t.source_path),i=document.createElement("div");i.className="kiw-source",a&&i.classList.add("kiw-source-link");let s=U(t),r=Y(t),o=document.createElement("div");if(o.className="kiw-source-header",o.appendChild(d("span","kiw-source-badge",s)),a){let l=document.createElement("a");l.className="kiw-source-title kiw-source-title-link",l.href=a,l.textContent=r,o.appendChild(l)}else o.appendChild(d("strong","kiw-source-title",r));if(i.appendChild(o),i.appendChild(d("div","kiw-source-snippet",_(t))),a){let l=document.createElement("a");l.className="kiw-source-action",l.href=a,l.textContent="\u67E5\u770B\u539F\u6587",i.appendChild(l)}return t.images.slice(0,3).forEach((l,w)=>{let c=document.createElement("a");c.className="kiw-source-image",c.href=K(e,l),c.target="_blank",c.rel="noopener noreferrer",c.textContent=`\u76F8\u5173\u56FE\u7247 ${w+1}`,i.appendChild(c)}),i}function N(e,t,a){let i=document.createElement("article");if(i.className="kiw-message kiw-message-assistant",i.appendChild(d("div","kiw-message-label","KingIAsk")),i.appendChild(d("div","kiw-answer-text",a.answer)),a.sources.length>0){let s=document.createElement("section");s.className="kiw-sources",s.appendChild(d("div","kiw-sources-heading","\u8D44\u6599\u6765\u6E90")),a.sources.slice(0,3).forEach(r=>s.appendChild(B(e,r))),i.appendChild(s)}t.appendChild(i),t.scrollTop=t.scrollHeight}function $(){let e=document.createElement("div");return e.className="kiw-loading",e.setAttribute("aria-live","polite"),e.innerHTML=`
    <span class="kiw-loading-text">\u6B63\u5728\u68C0\u7D22\u8D44\u6599</span>
    <span class="kiw-loading-dots" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
  `,e}function R(e){var E,C;if(!e.enabled)return null;let t=document.createElement("div");t.setAttribute("data-kingiask-widget-root","true");let a=t.attachShadow({mode:"open"}),i=document.createElement("style");i.textContent=M;let s=document.createElement("div");s.className=`kiw-root ${e.position}`;let r=document.createElement("button");r.className="kiw-launcher",r.type="button",r.dataset.role="launcher",r.setAttribute("aria-label",`\u6253\u5F00 ${e.title} \u52A9\u624B`),r.innerHTML=`
    <span class="kiw-launcher-mark" aria-hidden="true">K</span>
    <span class="kiw-launcher-copy">
      <span class="kiw-launcher-title"></span>
      <span class="kiw-launcher-status">\u52A9\u624B\u5728\u7EBF</span>
    </span>
  `,r.querySelector(".kiw-launcher-title").textContent=e.title;let o=document.createElement("section");o.className="kiw-panel",o.dataset.role="panel",o.setAttribute("role","dialog"),o.setAttribute("aria-labelledby","kiw-title"),o.innerHTML=`
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
  `,o.querySelector(".kiw-title").textContent=e.title;let l=o.querySelector(".kiw-messages"),w=o.querySelector("[data-role='question']"),c=o.querySelector("[data-role='send']"),k=O(e),u=document.createElement("article");u.className="kiw-message kiw-message-assistant",u.appendChild(d("div","kiw-message-label","KingIAsk")),u.appendChild(d("div","kiw-answer-text",e.welcomeText)),l.appendChild(u),k.forEach(n=>{n.role==="user"?W(l,n.text):N(e,l,n.response)});let H=()=>{o.classList.add("open"),r.setAttribute("aria-expanded","true"),r.style.display="none",window.addEventListener("keydown",f),w.focus()},v=()=>{o.classList.remove("open"),r.setAttribute("aria-expanded","false"),r.style.display="",window.removeEventListener("keydown",f)},f=n=>{n.key==="Escape"&&v()},y=n=>{w.disabled=n,c.disabled=n,c.textContent=n?"\u5904\u7406\u4E2D":"\u53D1\u9001"},S=async()=>{let n=w.value.trim();if(!n)return;w.value="",W(l,n),k.push({role:"user",text:n}),L(e,k);let x=$();l.appendChild(x),y(!0);try{let g=await T(e,n);x.remove(),N(e,l,g),k.push({role:"assistant",response:g}),L(e,k)}catch(g){x.remove();let P=g instanceof Error?g.message:"\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002";l.appendChild(d("div","kiw-error",P))}finally{y(!1)}};return r.addEventListener("click",H),(E=o.querySelector(".kiw-close"))==null||E.addEventListener("click",v),(C=o.querySelector("form"))==null||C.addEventListener("submit",n=>{n.preventDefault(),S()}),w.addEventListener("keydown",n=>{n.key==="Enter"&&!n.shiftKey&&!n.isComposing&&(n.preventDefault(),S())}),s.append(r,o),a.append(i,s),document.body.appendChild(t),{destroy:()=>{window.removeEventListener("keydown",f),t.remove()}}}var p=null,h=document.readyState==="loading";function b(e){h=!1,p==null||p.destroy();let t=A(e);p=R(t)}function q(){h=!1,p==null||p.destroy(),p=null}var D={init:b,destroy:q};window.KingIAskWidget=D;document.readyState==="loading"?document.addEventListener("DOMContentLoaded",()=>{h&&b()},{once:!0}):b();})();
