import { askKingIAsk, buildManualImageUrl, buildManualPageUrl } from "./api";
import { WIDGET_STYLES } from "./styles";
import type { ChatResponse, ResolvedKingIAskWidgetConfig, SourceSnippet } from "./types";

type WidgetInstance = {
  destroy: () => void;
};

type StoredMessage =
  | { role: "user"; text: string }
  | { role: "assistant"; response: ChatResponse };

const SESSION_STORAGE_KEY = "kingiask-widget:conversation:v1";
const MAX_STORED_MESSAGES = 40;

// 创建 HTML 元素并设置文本内容，避免把模型回答直接作为 HTML 注入。
function textElement<K extends keyof HTMLElementTagNameMap>(tag: K, className: string, text: string): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

// 从当前标签页的 sessionStorage 中读取历史会话，页面跳转后可以恢复上下文。
function loadStoredMessages(config: ResolvedKingIAskWidgetConfig): StoredMessage[] {
  if (!config.persistSession) {
    return [];
  }
  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) {
      return [];
    }
    const parsed = JSON.parse(raw);
    if (!Array.isArray(parsed)) {
      return [];
    }
    return parsed.filter((message): message is StoredMessage => {
      if (message?.role === "user") {
        return typeof message.text === "string";
      }
      if (message?.role === "assistant") {
        return typeof message.response?.answer === "string" && Array.isArray(message.response?.sources);
      }
      return false;
    });
  } catch {
    return [];
  }
}

// 将历史会话写入 sessionStorage；写入失败时静默降级为不持久化。
function saveStoredMessages(config: ResolvedKingIAskWidgetConfig, storedMessages: StoredMessage[]): void {
  if (!config.persistSession) {
    return;
  }
  try {
    window.sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(storedMessages.slice(-MAX_STORED_MESSAGES)));
  } catch {
    // 浏览器隐私模式或存储空间不足时，不影响问答主流程。
  }
}

// 渲染用户消息，供新提问和历史恢复复用。
function renderUserMessage(messages: HTMLElement, question: string): void {
  const userMessage = document.createElement("article");
  userMessage.className = "kiw-message kiw-message-user";
  userMessage.appendChild(textElement("div", "kiw-answer-text", question));
  messages.appendChild(userMessage);
  messages.scrollTop = messages.scrollHeight;
}

// 提取资料编号，优先使用后端证据编号，没有时再退回到通用“资料”。
function getSourceBadge(source: SourceSnippet): string {
  return source.evidence_ids.find((id) => id.trim()) ?? "资料";
}

// 把后端标题或文件路径清洗成适合用户阅读的短标题，不暴露内部目录结构。
function getReadableSourceTitle(source: SourceSnippet): string {
  const rawTitle = source.title || source.source_path;
  const normalized = rawTitle.replace(/\\/g, "/").replace(/\.md$/i, "");
  const lastSegment = normalized.split("/").filter(Boolean).at(-1);
  return lastSegment || "相关资料";
}

// 清洗资料片段中由文档路径生成的 Markdown 标题，避免在前端暴露内部文件结构。
function getReadableSnippet(source: SourceSnippet): string {
  return source.snippet
    .split(/\r?\n/)
    .filter((line) => {
      const trimmed = line.trim();
      return !/^#*\s*(helperFront\/|docs\/).+\.md?$/i.test(trimmed) && !/^#*\s*(helperFront\/|docs\/)/i.test(trimmed);
    })
    .join("\n")
    .trim();
}

// 根据来源资料生成展示节点，包含标题、路径、片段和图片入口。
function renderSource(config: ResolvedKingIAskWidgetConfig, source: SourceSnippet): HTMLElement {
  const pageUrl = buildManualPageUrl(source.source_path);
  const wrapper = document.createElement("div");
  wrapper.className = "kiw-source";
  if (pageUrl) {
    wrapper.classList.add("kiw-source-link");
  }
  const badgeText = getSourceBadge(source);
  const titleText = getReadableSourceTitle(source);
  const header = document.createElement("div");
  header.className = "kiw-source-header";
  header.appendChild(textElement("span", "kiw-source-badge", badgeText));
  if (pageUrl) {
    const titleLink = document.createElement("a");
    titleLink.className = "kiw-source-title kiw-source-title-link";
    titleLink.href = pageUrl;
    titleLink.textContent = titleText;
    header.appendChild(titleLink);
  } else {
    header.appendChild(textElement("strong", "kiw-source-title", titleText));
  }
  wrapper.appendChild(header);
  wrapper.appendChild(textElement("div", "kiw-source-snippet", getReadableSnippet(source)));
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
  const storedMessages = loadStoredMessages(config);
  const welcome = document.createElement("article");
  welcome.className = "kiw-message kiw-message-assistant";
  welcome.appendChild(textElement("div", "kiw-message-label", "KingIAsk"));
  welcome.appendChild(textElement("div", "kiw-answer-text", config.welcomeText));
  messages.appendChild(welcome);
  storedMessages.forEach((message) => {
    if (message.role === "user") {
      renderUserMessage(messages, message.text);
    } else {
      renderAnswer(config, messages, message.response);
    }
  });

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
    renderUserMessage(messages, question);
    storedMessages.push({ role: "user", text: question });
    saveStoredMessages(config, storedMessages);
    const loading = renderLoading();
    messages.appendChild(loading);
    setLoading(true);
    try {
      const response = await askKingIAsk(config, question);
      loading.remove();
      renderAnswer(config, messages, response);
      storedMessages.push({ role: "assistant", response });
      saveStoredMessages(config, storedMessages);
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
