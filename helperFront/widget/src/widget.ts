import { askKingIAsk, buildManualImageUrl, buildManualPageUrl } from "./api";
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
  const pageUrl = buildManualPageUrl(source.source_path);
  const wrapper = document.createElement("div");
  wrapper.className = "kiw-source";
  if (pageUrl) {
    wrapper.classList.add("kiw-source-link");
  }
  const titleText = source.title || source.source_path;
  if (pageUrl) {
    const titleLink = document.createElement("a");
    titleLink.className = "kiw-source-title kiw-source-title-link";
    titleLink.href = pageUrl;
    titleLink.textContent = titleText;
    wrapper.appendChild(titleLink);
  } else {
    wrapper.appendChild(textElement("strong", "kiw-source-title", titleText));
  }
  wrapper.appendChild(textElement("div", "kiw-source-path", source.source_path));
  wrapper.appendChild(textElement("div", "kiw-source-snippet", source.snippet));
  if (pageUrl) {
    const pageLink = document.createElement("a");
    pageLink.className = "kiw-source-action";
    pageLink.href = pageUrl;
    pageLink.textContent = "查看原文";
    wrapper.appendChild(pageLink);
  }
  source.images.slice(0, 3).forEach((image, index) => {
    const link = document.createElement("a");
    link.className = "kiw-source-image";
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
  const answer = document.createElement("article");
  answer.className = "kiw-message kiw-message-assistant";
  answer.appendChild(textElement("div", "kiw-message-label", "KingIAsk"));
  answer.appendChild(textElement("div", "kiw-answer-text", response.answer));
  if (response.sources.length > 0) {
    const sources = document.createElement("section");
    sources.className = "kiw-sources";
    sources.appendChild(textElement("div", "kiw-sources-heading", "资料来源"));
    response.sources.slice(0, 3).forEach((source) => sources.appendChild(renderSource(config, source)));
    answer.appendChild(sources);
  }
  messages.appendChild(answer);
  messages.scrollTop = messages.scrollHeight;
}

// 创建等待回答时的思考状态，让用户知道助手正在检索资料和生成答案。
function renderLoading(): HTMLElement {
  const loading = document.createElement("div");
  loading.className = "kiw-loading";
  loading.setAttribute("aria-live", "polite");
  loading.innerHTML = `
    <span class="kiw-loading-text">正在检索资料</span>
    <span class="kiw-loading-dots" aria-hidden="true">
      <span></span><span></span><span></span>
    </span>
  `;
  return loading;
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
  const launcher = document.createElement("button");
  launcher.className = "kiw-launcher";
  launcher.type = "button";
  launcher.dataset.role = "launcher";
  launcher.setAttribute("aria-label", `打开 ${config.title} 助手`);
  launcher.innerHTML = `
    <span class="kiw-launcher-mark" aria-hidden="true">K</span>
    <span class="kiw-launcher-copy">
      <span class="kiw-launcher-title"></span>
      <span class="kiw-launcher-status">助手在线</span>
    </span>
  `;
  launcher.querySelector(".kiw-launcher-title")!.textContent = config.title;

  const panel = document.createElement("section");
  panel.className = "kiw-panel";
  panel.dataset.role = "panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-labelledby", "kiw-title");
  panel.innerHTML = `
    <header class="kiw-header">
      <div class="kiw-brand">
        <span class="kiw-brand-mark" aria-hidden="true">K</span>
        <div>
          <h2 class="kiw-title" id="kiw-title"></h2>
          <p class="kiw-subtitle">企业知识问答助手 · 助手在线</p>
        </div>
      </div>
      <button class="kiw-close" type="button" aria-label="关闭 KingIAsk">×</button>
    </header>
    <div class="kiw-messages"></div>
    <form class="kiw-form">
      <div class="kiw-input-shell">
        <textarea class="kiw-input" data-role="question" placeholder="输入 KF 产品使用问题"></textarea>
        <button class="kiw-send" data-role="send" type="submit">发送</button>
      </div>
    </form>
  `;
  panel.querySelector(".kiw-title")!.textContent = config.title;
  const messages = panel.querySelector(".kiw-messages") as HTMLElement;
  const textarea = panel.querySelector("[data-role='question']") as HTMLTextAreaElement;
  const sendButton = panel.querySelector("[data-role='send']") as HTMLButtonElement;
  const welcome = document.createElement("article");
  welcome.className = "kiw-message kiw-message-assistant";
  welcome.appendChild(textElement("div", "kiw-message-label", "KingIAsk"));
  welcome.appendChild(textElement("div", "kiw-answer-text", config.welcomeText));
  messages.appendChild(welcome);

  const openPanel = () => {
    panel.classList.add("open");
    launcher.setAttribute("aria-expanded", "true");
    launcher.style.display = "none";
    textarea.focus();
  };
  const closePanel = () => {
    panel.classList.remove("open");
    launcher.setAttribute("aria-expanded", "false");
    launcher.style.display = "";
  };
  const setLoading = (loading: boolean) => {
    textarea.disabled = loading;
    sendButton.disabled = loading;
    sendButton.textContent = loading ? "处理中" : "发送";
  };
  const submitQuestion = async () => {
    const question = textarea.value.trim();
    if (!question) return;
    textarea.value = "";
    const userMessage = document.createElement("article");
    userMessage.className = "kiw-message kiw-message-user";
    userMessage.appendChild(textElement("div", "kiw-answer-text", question));
    messages.appendChild(userMessage);
    const loading = renderLoading();
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
