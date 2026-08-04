export const WIDGET_STYLES = `
/* ============================================================
   KingIAsk Widget · Apple 风格
   - 玻璃质感（backdrop-filter blur + saturate）
   - 浅色 / 深色自适应（prefers-color-scheme）
   - iOS spring 缓动（--kiw-ease-drawer）
   - SF Pro 系统字体 + 负 tracking
   ============================================================ */
:host {
  all: initial;
  font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", "SF Pro Display",
    "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif;

  /* 浅色 tokens */
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

  /* iOS spring 缓动 */
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

/* —— 浮动入口 —— */
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
/* 图标放在白色圆底上，与渐变背景干净分层，避免同色系糊在一起 */
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

/* 在线状态角标：右下角绿点 */
.kiw-launcher-status {
  position: absolute; right: 3px; bottom: 3px;
  width: 13px; height: 13px; border-radius: 999px;
  background: #34c759;
  border: 2.5px solid rgba(255, 255, 255, 0.92);
  box-shadow: 0 0 0 3px rgba(52, 199, 89, 0.25);
}

/* —— 面板 —— */
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

/* —— 头部 —— */
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

/* —— 消息区 —— */
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

/* —— 错误 / 加载 —— */
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

/* —— 资料来源 —— */
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

/* —— 输入区 —— */
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

/* —— 焦点可见 —— */
.kiw-launcher:focus-visible, .kiw-close:focus-visible, .kiw-send:focus-visible,
.kiw-source-title-link:focus-visible, .kiw-source-action:focus-visible, .kiw-source-image:focus-visible {
  outline: 3px solid var(--kiw-accent-ring); outline-offset: 2px;
}

/* —— 消息操作与证据锚定 —— */
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

/* —— 资料来源锚定滚动与高亮 —— */
.kiw-source { scroll-margin: 14px; }
.kiw-source-flash {
  animation: kiw-source-flash 1.6s ease-out;
}
@keyframes kiw-source-flash {
  0% { border-color: var(--kiw-accent); background: var(--kiw-accent-soft); }
  100% { border-color: var(--kiw-border); background: var(--kiw-surface-muted); }
}

/* —— 图片缩略图 —— */
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

/* —— 清空会话 —— */
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

/* —— 推荐问题 —— */
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

/* —— 图片灯箱 —— */
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

/* —— 动画 —— */
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

/* —— 移动端 —— */
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

/* —— 减少动效 —— */
@media (prefers-reduced-motion: reduce) {
  .kiw-panel.open, .kiw-message, .kiw-error, .kiw-loading,
  .kiw-loading-dots span, .kiw-source-flash, .kiw-lightbox.open,
  .kiw-lightbox-body { animation: none; }
}
`;
