export const WIDGET_STYLES = `
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
`;
