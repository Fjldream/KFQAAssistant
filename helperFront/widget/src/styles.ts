export const WIDGET_STYLES = `
:host { all: initial; font-family: Inter, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif; }
.kiw-root { position: fixed; z-index: 2147483000; bottom: 24px; }
.kiw-root.right-bottom { right: 24px; }
.kiw-root.left-bottom { left: 24px; }
.kiw-launcher { width: 56px; height: 56px; border: 0; border-radius: 18px; background: linear-gradient(135deg, #0b776d, #c99335); color: #fff; font-weight: 800; box-shadow: 0 18px 42px rgb(0 0 0 / 24%); cursor: pointer; }
.kiw-panel { display: none; width: min(380px, calc(100vw - 32px)); height: min(560px, calc(100vh - 96px)); overflow: hidden; border: 1px solid #dce4e8; border-radius: 16px; background: #fff; box-shadow: 0 22px 55px rgb(23 33 43 / 18%); }
.kiw-panel.open { display: grid; grid-template-rows: auto minmax(0, 1fr) auto; }
.kiw-header { display: flex; align-items: center; justify-content: space-between; gap: 12px; padding: 14px 16px; border-bottom: 1px solid #edf2f4; }
.kiw-title { margin: 0; color: #17212b; font-size: 16px; font-weight: 800; }
.kiw-close { border: 0; background: transparent; color: #6b7785; cursor: pointer; font-size: 18px; }
.kiw-messages { min-height: 0; overflow: auto; padding: 14px; background: #f7fafb; }
.kiw-welcome, .kiw-answer, .kiw-error, .kiw-loading { margin: 0 0 10px; border: 1px solid #e4ebee; border-radius: 12px; background: #fff; color: #17212b; padding: 12px; line-height: 1.6; font-size: 14px; white-space: pre-wrap; }
.kiw-error { border-color: #f4c7c3; color: #b42318; }
.kiw-source { margin-top: 8px; border-top: 1px solid #edf2f4; padding-top: 8px; color: #4f5f6d; font-size: 12px; }
.kiw-source strong { display: block; color: #17212b; }
.kiw-source a { display: inline-block; margin-top: 6px; color: #0b776d; text-decoration: none; }
.kiw-form { display: grid; gap: 8px; padding: 12px; border-top: 1px solid #edf2f4; }
.kiw-input { min-height: 70px; resize: none; border: 1px solid #cfdbe1; border-radius: 10px; padding: 10px; color: #17212b; font: inherit; outline: none; }
.kiw-send { min-height: 36px; border: 0; border-radius: 10px; background: #0b776d; color: #fff; cursor: pointer; font-weight: 700; }
.kiw-send:disabled { cursor: not-allowed; opacity: 0.6; }
`;
