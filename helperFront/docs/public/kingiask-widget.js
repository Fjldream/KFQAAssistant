"use strict";(()=>{var P={enabled:!1,apiBaseUrl:"",apiKey:"",title:"KingIAsk",welcomeText:"\u4F60\u597D\uFF0C\u6211\u53EF\u4EE5\u5E2E\u4F60\u67E5\u8BE2 KF \u4EA7\u54C1\u624B\u518C\u3002",position:"right-bottom",timeoutMs:6e4,persistSession:!0,accentColor:"",suggestedQuestions:[]};function j(t={}){var r,n,c,i,o,s;let e={...P,...(r=window.KINGIASK_WIDGET_CONFIG)!=null?r:{},...t};return{...e,apiBaseUrl:String((n=e.apiBaseUrl)!=null?n:"").replace(/\/+$/,""),apiKey:String((c=e.apiKey)!=null?c:""),title:String((i=e.title)!=null?i:P.title),welcomeText:String((o=e.welcomeText)!=null?o:P.welcomeText),position:e.position==="left-bottom"?"left-bottom":"right-bottom",timeoutMs:Number(e.timeoutMs||P.timeoutMs),persistSession:e.persistSession!==!1,accentColor:String((s=e.accentColor)!=null?s:"").trim(),suggestedQuestions:Array.isArray(e.suggestedQuestions)?e.suggestedQuestions.map(String).filter(Boolean).slice(0,4):[]}}function Y(t,e){return/^https?:\/\//i.test(e)?e:`${t.apiBaseUrl}/manuals/${e.replace(/^\/+/,"")}`}function G(t){let e=t.replace(/\\/g,"/").replace(/^\/+/,"");return e.toLowerCase().endsWith(".md")?`/${e.replace(/^(helperFront\/docs\/|helperFront\/|docs\/)/,"").replace(/\.md$/i,"")}`:null}async function Q(t,e,r="",n=[],c=0,i){var y,l,u,g,S;if(!t.apiBaseUrl)throw new Error("\u52A9\u624B\u914D\u7F6E\u7F3A\u5C11\u670D\u52A1\u5730\u5740\u3002");let o=new AbortController,s=window.setTimeout(()=>o.abort(),t.timeoutMs),w=new Headers({"Content-Type":"application/json"});t.apiKey.trim()&&w.set("X-API-Key",t.apiKey.trim());let d={question:e};r.trim()&&(d.conversation_summary=r),c>0&&(d.conversation_turn_count=c),n.length>0&&(d.recent_messages=n);try{let p=await fetch(`${t.apiBaseUrl}/api/chat/stream`,{method:"POST",headers:w,body:JSON.stringify(d),signal:o.signal});if(p.status===401||p.status===403)throw new Error("\u52A9\u624B\u8BA4\u8BC1\u5931\u8D25\uFF0C\u8BF7\u68C0\u67E5\u914D\u7F6E\u3002");if(!p.ok)throw new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002");if(!p.body)throw new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002");let R=p.body.getReader(),I=new TextDecoder,f="";for(;;){let{done:$,value:z}=await R.read();if($)break;f+=I.decode(z,{stream:!0});let E=f.split(`

`);f=(y=E.pop())!=null?y:"";for(let _ of E){let A=_.split(`
`).find(T=>T.startsWith("data:"));if(!A)continue;let K=A.slice(5).trim();if(K==="[DONE]")return;let x;try{x=JSON.parse(K)}catch{continue}switch(x.type){case"chunk":case"answer":i.onChunk(String((l=x.content)!=null?l:""));break;case"sources":i.onSources(Array.isArray(x.sources)?x.sources:[]);break;case"done":i.onDone(String((u=x.conversation_summary)!=null?u:""),String((g=x.standalone_question)!=null?g:""));break;case"error":{let T=String((S=x.message)!=null?S:"\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002"),N=new Error(T);throw N.fromServer=!0,N}default:break}}}}catch(p){throw p instanceof DOMException&&p.name==="AbortError"?new Error("\u8BF7\u6C42\u8D85\u65F6\uFF0C\u8BF7\u7A0D\u540E\u91CD\u8BD5\u3002"):p instanceof Error&&p.fromServer||p instanceof Error&&p.message.startsWith("\u52A9\u624B")?p:new Error("\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002")}finally{window.clearTimeout(s)}}var J=`
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
  position: relative;
  display: grid; place-items: center;
  width: 52px; height: 52px; padding: 7px;
  border: 1px solid rgba(255, 255, 255, 0.28);
  border-radius: 999px;
  background: linear-gradient(135deg, var(--kiw-accent) 0%, #5ac8fa 100%);
  cursor: pointer;
  box-shadow:
    0 12px 26px var(--kiw-accent-ring),
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 -10px 18px rgba(0, 0, 0, 0.08);
  transition:
    transform 180ms var(--kiw-ease-out),
    box-shadow 180ms ease;
}
.kiw-launcher:hover {
  transform: translateY(-2px) scale(1.04);
  box-shadow:
    0 16px 36px var(--kiw-accent-ring),
    inset 0 1px 0 rgba(255, 255, 255, 0.28),
    inset 0 -10px 18px rgba(0, 0, 0, 0.08);
}
.kiw-launcher:active { transform: scale(0.94); transition-duration: 100ms; }

.kiw-launcher-mark, .kiw-brand-mark {
  display: grid; place-items: center;
}
/* \u56FE\u6807\u653E\u5728\u767D\u8272\u5706\u5E95\u4E0A\uFF0C\u4E0E\u6E10\u53D8\u80CC\u666F\u5E72\u51C0\u5206\u5C42\uFF0C\u907F\u514D\u540C\u8272\u7CFB\u7CCA\u5728\u4E00\u8D77 */
.kiw-launcher-mark {
  width: 38px; height: 38px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.96);
  box-shadow: inset 0 -2px 6px rgba(0, 0, 0, 0.06);
  padding: 6px;
}
.kiw-brand-mark {
  width: 42px; height: 42px; border-radius: 15px;
}
.kiw-launcher-mark .kiw-logo, .kiw-brand-mark .kiw-logo {
  display: block; width: 100%; height: 100%; object-fit: contain;
}

/* \u5728\u7EBF\u72B6\u6001\u89D2\u6807\uFF1A\u53F3\u4E0B\u89D2\u7EFF\u70B9 */
.kiw-launcher-status {
  position: absolute; right: 3px; bottom: 3px;
  width: 13px; height: 13px; border-radius: 999px;
  background: #34c759;
  border: 2.5px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.25);
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

/* \u2014\u2014 \u6D88\u606F\u64CD\u4F5C\u4E0E\u8BC1\u636E\u951A\u5B9A \u2014\u2014 */
.kiw-message-actions {
  display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px;
}
.kiw-copy {
  display: inline-flex; align-items: center; min-height: 28px; border-radius: 999px;
  border: 1px solid var(--kiw-border); background: var(--kiw-surface-muted);
  color: var(--kiw-text-secondary); padding: 0 12px; cursor: pointer;
  font-size: 12px; font-weight: 700;
  transition: background 150ms ease, color 150ms ease, transform 150ms var(--kiw-ease-out);
}
.kiw-copy:hover { background: var(--kiw-surface-muted); color: var(--kiw-text); }
.kiw-copy:active { transform: scale(0.95); }
.kiw-anchor {
  color: var(--kiw-accent); font-weight: 700; text-decoration: none; cursor: pointer;
}
.kiw-anchor:hover { text-decoration: underline; text-underline-offset: 3px; }

/* \u2014\u2014 \u8D44\u6599\u6765\u6E90\u951A\u5B9A\u6EDA\u52A8\u4E0E\u9AD8\u4EAE \u2014\u2014 */
.kiw-source { scroll-margin: 14px; }
.kiw-source-flash {
  animation: kiw-source-flash 1.6s ease-out;
}
@keyframes kiw-source-flash {
  0% { border-color: var(--kiw-accent); background: var(--kiw-accent-soft); }
  100% { border-color: var(--kiw-border); background: var(--kiw-surface-muted); }
}

/* \u2014\u2014 \u56FE\u7247\u7F29\u7565\u56FE \u2014\u2014 */
.kiw-thumb {
  display: inline-flex; align-items: center; gap: 8px; width: fit-content; margin-top: 4px;
  border: 1px solid var(--kiw-border); border-radius: 12px; background: var(--kiw-surface-solid);
  padding: 4px 10px 4px 4px; cursor: pointer;
  transition: border-color 150ms ease, transform 150ms var(--kiw-ease-out);
}
.kiw-thumb:hover { border-color: var(--kiw-accent-ring); }
.kiw-thumb:active { transform: scale(0.97); }
.kiw-thumb img {
  width: 44px; height: 44px; object-fit: cover; border-radius: 9px;
  background: var(--kiw-surface-muted);
}
.kiw-thumb-label {
  color: var(--kiw-accent); font-size: 12px; font-weight: 700;
}

/* \u2014\u2014 \u6E05\u7A7A\u4F1A\u8BDD \u2014\u2014 */
.kiw-header-actions { display: flex; align-items: center; gap: 8px; }
.kiw-clear {
  display: inline-flex; align-items: center; min-height: 30px; border-radius: 999px;
  border: 1px solid var(--kiw-border); background: var(--kiw-surface-muted);
  color: var(--kiw-text-secondary); padding: 0 12px; cursor: pointer;
  font-size: 12px; font-weight: 700;
  transition: background 150ms ease, color 150ms ease, transform 150ms var(--kiw-ease-out);
}
.kiw-clear:hover { background: var(--kiw-red-soft); color: var(--kiw-red); border-color: transparent; }
.kiw-clear:active { transform: scale(0.95); }

/* \u2014\u2014 \u63A8\u8350\u95EE\u9898 \u2014\u2014 */
.kiw-suggestions {
  display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; margin-top: 12px;
}
.kiw-suggestion {
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  border: 1px solid var(--kiw-border); border-radius: 12px; background: var(--kiw-surface-muted);
  color: var(--kiw-text-secondary); padding: 9px 11px; cursor: pointer;
  font-size: 12px; font-weight: 650; text-align: left;
  transition: border-color 150ms ease, background-color 150ms ease, transform 150ms var(--kiw-ease-out);
}
.kiw-suggestion:hover { border-color: var(--kiw-accent-ring); background: var(--kiw-accent-soft); color: var(--kiw-accent); }
.kiw-suggestion:active { transform: scale(0.97); }

/* \u2014\u2014 \u56FE\u7247\u706F\u7BB1 \u2014\u2014 */
.kiw-lightbox {
  position: fixed; inset: 0; z-index: 10; display: none;
  align-items: center; justify-content: center; padding: 24px;
}
.kiw-lightbox.open { display: flex; animation: kiw-lightbox-in 200ms ease both; }
.kiw-lightbox-backdrop {
  position: absolute; inset: 0; background: rgba(0, 0, 0, 0.5);
  -webkit-backdrop-filter: blur(14px) saturate(140%); backdrop-filter: blur(14px) saturate(140%);
}
.kiw-lightbox-body {
  position: relative; max-width: min(880px, 92vw); max-height: 88vh; margin: 0;
  border-radius: 18px; overflow: hidden;
  background: var(--kiw-surface-solid); box-shadow: var(--kiw-shadow-pop);
  animation: kiw-msg-in 240ms var(--kiw-ease-out) both;
}
.kiw-lightbox-img {
  display: block; max-width: 100%; max-height: 82vh; object-fit: contain;
}
.kiw-lightbox-caption {
  padding: 10px 14px; color: var(--kiw-text-secondary); font-size: 12px;
  overflow-wrap: anywhere; border-top: 1px solid var(--kiw-border);
}
.kiw-lightbox-close {
  position: absolute; top: 10px; right: 10px; z-index: 1;
  display: grid; place-items: center; width: 32px; height: 32px;
  border-radius: 999px; background: rgba(255, 255, 255, 0.85);
  color: #1d1d1f; cursor: pointer; font-size: 18px; line-height: 1;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
  transition: transform 150ms var(--kiw-ease-out);
}
.kiw-lightbox-close:active { transform: scale(0.9); }
@keyframes kiw-lightbox-in {
  from { opacity: 0; }
  to { opacity: 1; }
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
  .kiw-launcher { width: 48px; height: 48px; padding: 6px; }
  .kiw-launcher-mark { width: 36px; height: 36px; padding: 5px; }
  .kiw-panel { width: 100%; height: min(620px, calc(100vh - 28px)); border-radius: 22px; }
  .kiw-suggestions { grid-template-columns: 1fr; }
  .kiw-lightbox { padding: 12px; }
  .kiw-lightbox-body { max-height: 90vh; border-radius: 14px; }
  .kiw-lightbox-img { max-height: 84vh; }
}

/* \u2014\u2014 \u51CF\u5C11\u52A8\u6548 \u2014\u2014 */
@media (prefers-reduced-motion: reduce) {
  .kiw-panel.open, .kiw-message, .kiw-error, .kiw-loading,
  .kiw-loading-dots span, .kiw-source-flash, .kiw-lightbox.open,
  .kiw-lightbox-body { animation: none; }
}
`;var ee="kingiask-widget:conversation:v1",se=40,X='<img class="kiw-logo" src="/logo.png" alt="KingIAsk \u6807\u5FD7" />';function h(t,e,r){let n=document.createElement(t);return n.className=e,n.textContent=r,n}function V(t){var r,n;if(!t||typeof t!="object")return!1;let e=t;return e.role==="user"?typeof e.text=="string":e.role==="assistant"?typeof((r=e.response)==null?void 0:r.answer)=="string"&&Array.isArray((n=e.response)==null?void 0:n.sources):!1}function ce(t){let e={messages:[],conversationSummary:""};if(!t.persistSession)return e;try{let r=window.sessionStorage.getItem(ee);if(!r)return e;let n=JSON.parse(r);return Array.isArray(n)?{messages:n.filter(V),conversationSummary:""}:!n||typeof n!="object"||!Array.isArray(n.messages)?e:{messages:n.messages.filter(V),conversationSummary:typeof n.conversationSummary=="string"?n.conversationSummary:""}}catch{return e}}function D(t,e,r){if(t.persistSession)try{window.sessionStorage.setItem(ee,JSON.stringify({messages:e.slice(-se),conversationSummary:r}))}catch{}}function de(t){return t.slice(-8).map(e=>e.role==="user"?{role:"user",content:e.text}:{role:"assistant",content:e.response.answer})}function le(t){return t.filter(e=>e.role==="user").length}function Z(t,e){let r=document.createElement("article");r.className="kiw-message kiw-message-user",r.appendChild(h("div","kiw-answer-text",e)),t.appendChild(r),t.scrollTop=t.scrollHeight}function pe(t){var e;return(e=t.evidence_ids.find(r=>r.trim()))!=null?e:"\u8D44\u6599"}function we(t){return(t.title||t.source_path).replace(/\\/g,"/").replace(/\.md$/i,"").split("/").filter(Boolean).at(-1)||"\u76F8\u5173\u8D44\u6599"}function ue(t){return t.snippet.split(/\r?\n/).filter(e=>{let r=e.trim();return!/^#*\s*(helperFront\/|docs\/).+\.md?$/i.test(r)&&!/^#*\s*(helperFront\/|docs\/)/i.test(r)}).join(`
`).trim()}function te(t,e){let r=document.createElement("div");return r.className="kiw-answer-text",t.split(/(\[资料\s*\d+\])/g).forEach(c=>{let i=c.match(/^\[资料\s*(\d+)\]$/);if(i){let o=Number(i[1]);if(o>=1&&o<=e){let s=document.createElement("a");s.className="kiw-anchor",s.href=`#kiw-source-${o}`,s.dataset.target=`kiw-source-${o}`,s.textContent=c,r.appendChild(s);return}}r.appendChild(document.createTextNode(c))}),r}function re(t){let e=document.createElement("button");return e.className="kiw-copy",e.type="button",e.textContent="\u590D\u5236",e.addEventListener("click",()=>{var r;(r=navigator.clipboard)==null||r.writeText(t).then(()=>{e.textContent="\u5DF2\u590D\u5236"}).catch(()=>{e.textContent="\u590D\u5236\u5931\u8D25"}),window.setTimeout(()=>{e.textContent="\u590D\u5236"},1600)}),e}function ie(t,e,r,n){let c=G(e.source_path),i=document.createElement("div");i.className="kiw-source",i.id=`kiw-source-${r+1}`,c&&i.classList.add("kiw-source-link");let o=pe(e),s=we(e),w=document.createElement("div");if(w.className="kiw-source-header",w.appendChild(h("span","kiw-source-badge",o)),c){let d=document.createElement("a");d.className="kiw-source-title kiw-source-title-link",d.href=c,d.textContent=s,w.appendChild(d)}else w.appendChild(h("strong","kiw-source-title",s));if(i.appendChild(w),i.appendChild(h("div","kiw-source-snippet",ue(e))),c){let d=document.createElement("a");d.className="kiw-source-action",d.href=c,d.textContent="\u67E5\u770B\u539F\u6587",i.appendChild(d)}return e.images.slice(0,3).forEach(d=>{var g,S;let y=Y(t,d),l=document.createElement("button");l.className="kiw-thumb",l.type="button",l.title=(g=d.split("/").pop())!=null?g:"\u76F8\u5173\u56FE\u7247";let u=document.createElement("img");u.src=y,u.alt=(S=d.split("/").pop())!=null?S:"\u76F8\u5173\u56FE\u7247",u.loading="lazy",u.addEventListener("error",()=>u.remove()),l.appendChild(u),l.appendChild(h("span","kiw-thumb-label","\u67E5\u770B\u56FE\u7247")),l.addEventListener("click",()=>n(y)),i.appendChild(l)}),i}function ge(t,e,r,n){let c=document.createElement("article");if(c.className="kiw-message kiw-message-assistant",c.appendChild(h("div","kiw-message-label","KingIAsk")),c.appendChild(te(r.answer,r.sources.length)),r.sources.length>0){let o=document.createElement("section");o.className="kiw-sources",o.appendChild(h("div","kiw-sources-heading","\u8D44\u6599\u6765\u6E90")),r.sources.slice(0,3).forEach((s,w)=>o.appendChild(ie(t,s,w,n))),c.appendChild(o)}let i=document.createElement("div");i.className="kiw-message-actions",i.appendChild(re(r.answer)),c.appendChild(i),e.appendChild(c),e.scrollTop=e.scrollHeight}function ke(){let t=document.createElement("div");return t.className="kiw-loading",t.setAttribute("aria-live","polite"),t.innerHTML=`
    <span class="kiw-loading-text">\u6B63\u5728\u68C0\u7D22\u8D44\u6599</span>
    <span class="kiw-loading-dots" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
  `,t}function oe(t){var K,x,T,N,F;if(!t.enabled)return null;let e=document.createElement("div");e.setAttribute("data-kingiask-widget-root","true"),t.accentColor&&e.style.setProperty("--kiw-accent",t.accentColor);let r=e.attachShadow({mode:"open"}),n=document.createElement("style");n.textContent=J;let c=document.createElement("div");c.className=`kiw-root ${t.position}`;let i=document.createElement("button");i.className="kiw-launcher",i.type="button",i.dataset.role="launcher",i.setAttribute("aria-label",`\u6253\u5F00 ${t.title} \u52A9\u624B`),i.innerHTML=`
    <span class="kiw-launcher-mark" aria-hidden="true">${X}</span>
    <span class="kiw-launcher-status" aria-hidden="true"></span>
  `,i.title=`${t.title} \xB7 \u52A9\u624B\u5728\u7EBF`;let o=document.createElement("section");o.className="kiw-panel",o.dataset.role="panel",o.setAttribute("role","dialog"),o.setAttribute("aria-labelledby","kiw-title"),o.innerHTML=`
    <header class="kiw-header">
      <div class="kiw-brand">
        <span class="kiw-brand-mark" aria-hidden="true">${X}</span>
        <div>
          <h2 class="kiw-title" id="kiw-title"></h2>
          <p class="kiw-subtitle">\u4F01\u4E1A\u77E5\u8BC6\u95EE\u7B54\u52A9\u624B \xB7 \u52A9\u624B\u5728\u7EBF</p>
        </div>
      </div>
      <div class="kiw-header-actions">
        <button class="kiw-clear" type="button" title="\u6E05\u7A7A\u4F1A\u8BDD" aria-label="\u6E05\u7A7A\u4F1A\u8BDD">\u6E05\u7A7A</button>
        <button class="kiw-close" type="button" aria-label="\u5173\u95ED KingIAsk">\xD7</button>
      </div>
    </header>
    <div class="kiw-messages"></div>
    <form class="kiw-form">
      <div class="kiw-input-shell">
        <textarea class="kiw-input" data-role="question" placeholder="\u8F93\u5165 KF \u4EA7\u54C1\u4F7F\u7528\u95EE\u9898"></textarea>
        <button class="kiw-send" data-role="send" type="submit">\u53D1\u9001</button>
      </div>
    </form>
  `,o.querySelector(".kiw-title").textContent=t.title;let s=o.querySelector(".kiw-messages"),w=o.querySelector("[data-role='question']"),d=o.querySelector("[data-role='send']"),y=ce(t),l=y.messages,u=y.conversationSummary,g=document.createElement("div");g.className="kiw-lightbox",g.innerHTML=`
    <div class="kiw-lightbox-backdrop" data-role="lightbox-close"></div>
    <figure class="kiw-lightbox-body">
      <button class="kiw-lightbox-close" type="button" aria-label="\u5173\u95ED\u56FE\u7247\u9884\u89C8">\xD7</button>
      <img class="kiw-lightbox-img" alt="\u8D44\u6599\u56FE\u7247\u9884\u89C8" />
      <figcaption class="kiw-lightbox-caption"></figcaption>
    </figure>
  `;let S=g.querySelector(".kiw-lightbox-img"),p=!1,R=a=>{var k;S.src=a,g.querySelector(".kiw-lightbox-caption").textContent=(k=a.split("/").pop())!=null?k:"",g.classList.add("open"),p=!0},I=()=>{g.classList.remove("open"),S.src="",p=!1};(K=g.querySelector('[data-role="lightbox-close"]'))==null||K.addEventListener("click",I),(x=g.querySelector(".kiw-lightbox-close"))==null||x.addEventListener("click",I),o.appendChild(g);let f=document.createElement("article");if(f.className="kiw-message kiw-message-assistant",f.appendChild(h("div","kiw-message-label","KingIAsk")),f.appendChild(h("div","kiw-answer-text",t.welcomeText)),t.suggestedQuestions.length>0){let a=document.createElement("div");a.className="kiw-suggestions",t.suggestedQuestions.forEach(k=>{let v=document.createElement("button");v.className="kiw-suggestion",v.type="button",v.textContent=k,v.addEventListener("click",()=>void A(k)),a.appendChild(v)}),f.appendChild(a)}s.appendChild(f),l.forEach(a=>{a.role==="user"?Z(s,a.text):ge(t,s,a.response,R)});let $=()=>{o.classList.add("open"),i.setAttribute("aria-expanded","true"),i.style.display="none",window.addEventListener("keydown",E),w.focus()},z=()=>{o.classList.remove("open"),i.setAttribute("aria-expanded","false"),i.style.display="",window.removeEventListener("keydown",E)},E=a=>{a.key==="Escape"&&(p?I():z())},_=a=>{w.disabled=a,d.disabled=a,d.textContent=a?"\u5904\u7406\u4E2D":"\u53D1\u9001"},A=async a=>{let k=(a!=null?a:w.value).trim();if(!k)return;let v=de(l),M=le(l);a||(w.value=""),Z(s,k),l.push({role:"user",text:k}),D(t,l,u),_(!0);let b=document.createElement("article");b.className="kiw-message kiw-message-assistant",b.appendChild(h("div","kiw-message-label","KingIAsk"));let O=document.createElement("div");O.className="kiw-answer-text",b.appendChild(O);let B=ke();b.appendChild(B),s.appendChild(b),s.scrollTop=s.scrollHeight;let W="",H=[];try{if(await Q(t,k,u,v,M,{onChunk:m=>{B.remove(),W+=m,O.textContent=W,s.scrollTop=s.scrollHeight},onSources:m=>{H=m},onDone:m=>{u=m}}),O.replaceWith(te(W,H.length)),H.length>0){let m=document.createElement("section");m.className="kiw-sources",m.appendChild(h("div","kiw-sources-heading","\u8D44\u6599\u6765\u6E90")),H.slice(0,3).forEach((ae,ne)=>m.appendChild(ie(t,ae,ne,R))),b.appendChild(m)}let L=document.createElement("div");L.className="kiw-message-actions",L.appendChild(re(W)),b.appendChild(L),l.push({role:"assistant",response:{answer:W,sources:H}}),D(t,l,u)}catch(L){B.remove(),b.remove();let m=L instanceof Error?L.message:"\u52A9\u624B\u6682\u65F6\u4E0D\u53EF\u7528\uFF0C\u8BF7\u7A0D\u540E\u518D\u8BD5\u3002";s.appendChild(h("div","kiw-error",m))}finally{_(!1)}};return i.addEventListener("click",$),(T=o.querySelector(".kiw-close"))==null||T.addEventListener("click",z),(N=o.querySelector(".kiw-clear"))==null||N.addEventListener("click",()=>{l.length=0,u="",D(t,l,u),[...s.children].forEach(a=>{a!==f&&a.remove()}),w.focus()}),(F=o.querySelector("form"))==null||F.addEventListener("submit",a=>{a.preventDefault(),A()}),w.addEventListener("keydown",a=>{a.key==="Enter"&&!a.shiftKey&&!a.isComposing&&(a.preventDefault(),A())}),s.addEventListener("click",a=>{var b;let k=a.target.closest("a.kiw-anchor");if(!k)return;a.preventDefault();let v=(b=k.dataset.target)!=null?b:"",M=v?s.querySelector(`#${CSS.escape(v)}`):null;M&&(M.scrollIntoView({behavior:"smooth",block:"nearest"}),M.classList.add("kiw-source-flash"),window.setTimeout(()=>M.classList.remove("kiw-source-flash"),1600))}),c.append(i,o),r.append(n,c),document.body.appendChild(e),{destroy:()=>{window.removeEventListener("keydown",E),e.remove()}}}var C=null,U=document.readyState==="loading";function q(t){U=!1,C==null||C.destroy();let e=j(t);C=oe(e)}function me(){U=!1,C==null||C.destroy(),C=null}var he={init:q,destroy:me};window.KingIAskWidget=he;document.readyState==="loading"?document.addEventListener("DOMContentLoaded",()=>{U&&q()},{once:!0}):q();})();
