import { askKingIAsk, buildManualImageUrl } from "./api";
import { WIDGET_STYLES } from "./styles";
import type { ChatResponse, ResolvedKingIAskWidgetConfig, SourceSnippet } from "./types";

type WidgetInstance = {
  destroy: () => void;
};

// 创建 HTML 元素并设置文本内容，避免把模型回答直接作为 HTML 注入。
function textElement<K extends keyof HTMLElementTagNameMap>(tag: K, className: string, text: string): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

// 根据来源资料生成展示节点，包含标题、路径、片段和图片入口。
function renderSource(config: ResolvedKingIAskWidgetConfig, source: SourceSnippet): HTMLElement {
  const wrapper = document.createElement("div");
  wrapper.className = "kiw-source";
  wrapper.appendChild(textElement("strong", "", source.title || source.source_path));
  wrapper.appendChild(textElement("div", "", source.source_path));
  wrapper.appendChild(textElement("div", "", source.snippet));
  source.images.slice(0, 3).forEach((image, index) => {
    const link = document.createElement("a");
    link.href = buildManualImageUrl(config, image);
    link.target = "_blank";
    link.rel = "noopener noreferrer";
    link.textContent = `相关图片 ${index + 1}`;
    wrapper.appendChild(link);
  });
  return wrapper;
}

// 把 RAG 返回结果渲染到消息区。
function renderAnswer(config: ResolvedKingIAskWidgetConfig, messages: HTMLElement, response: ChatResponse): void {
  const answer = textElement("div", "kiw-answer", response.answer);
  response.sources.slice(0, 3).forEach((source) => answer.appendChild(renderSource(config, source)));
  messages.appendChild(answer);
  messages.scrollTop = messages.scrollHeight;
}

// 创建 KingIAsk 浮动助手 DOM，并绑定打开、发送和销毁逻辑。
export function createKingIAskWidget(config: ResolvedKingIAskWidgetConfig): WidgetInstance | null {
  if (!config.enabled) {
    return null;
  }

  const host = document.createElement("div");
  host.setAttribute("data-kingiask-widget-root", "true");
  const shadow = host.attachShadow({ mode: "open" });
  const style = document.createElement("style");
  style.textContent = WIDGET_STYLES;

  const root = document.createElement("div");
  root.className = `kiw-root ${config.position}`;
  const launcher = textElement("button", "kiw-launcher", "问");
  launcher.type = "button";
  launcher.dataset.role = "launcher";

  const panel = document.createElement("section");
  panel.className = "kiw-panel";
  panel.innerHTML = `
    <header class="kiw-header">
      <h2 class="kiw-title"></h2>
      <button class="kiw-close" type="button" aria-label="关闭">×</button>
    </header>
    <div class="kiw-messages"></div>
    <form class="kiw-form">
      <textarea class="kiw-input" data-role="question" placeholder="输入 KF 产品使用问题"></textarea>
      <button class="kiw-send" data-role="send" type="submit">提问</button>
    </form>
  `;
  panel.querySelector(".kiw-title")!.textContent = config.title;
  const messages = panel.querySelector(".kiw-messages") as HTMLElement;
  const textarea = panel.querySelector("[data-role='question']") as HTMLTextAreaElement;
  const sendButton = panel.querySelector("[data-role='send']") as HTMLButtonElement;
  messages.appendChild(textElement("div", "kiw-welcome", config.welcomeText));

  const openPanel = () => {
    panel.classList.add("open");
    launcher.style.display = "none";
    textarea.focus();
  };
  const closePanel = () => {
    panel.classList.remove("open");
    launcher.style.display = "";
  };
  const setLoading = (loading: boolean) => {
    textarea.disabled = loading;
    sendButton.disabled = loading;
    sendButton.textContent = loading ? "检索中" : "提问";
  };
  const submitQuestion = async () => {
    const question = textarea.value.trim();
    if (!question) return;
    textarea.value = "";
    messages.appendChild(textElement("div", "kiw-answer", question));
    const loading = textElement("div", "kiw-loading", "正在检索手册...");
    messages.appendChild(loading);
    setLoading(true);
    try {
      const response = await askKingIAsk(config, question);
      loading.remove();
      renderAnswer(config, messages, response);
    } catch (error) {
      loading.remove();
      const message = error instanceof Error ? error.message : "助手暂时不可用，请稍后再试。";
      messages.appendChild(textElement("div", "kiw-error", message));
    } finally {
      setLoading(false);
    }
  };

  launcher.addEventListener("click", openPanel);
  panel.querySelector(".kiw-close")?.addEventListener("click", closePanel);
  panel.querySelector("form")?.addEventListener("submit", (event) => {
    event.preventDefault();
    void submitQuestion();
  });
  textarea.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      void submitQuestion();
    }
  });

  root.append(launcher, panel);
  shadow.append(style, root);
  document.body.appendChild(host);

  return {
    destroy: () => host.remove()
  };
}
