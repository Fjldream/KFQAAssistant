import { askKingIAskStream, buildManualImageUrl, buildManualPageUrl } from "./api";
import { WIDGET_STYLES } from "./styles";
import type { ChatHistoryMessage, ChatResponse, ResolvedKingIAskWidgetConfig, SourceSnippet } from "./types";

type WidgetInstance = {
  destroy: () => void;
};

type StoredMessage =
  | { role: "user"; text: string }
  | { role: "assistant"; response: ChatResponse };

type StoredConversation = {
  messages: StoredMessage[];
  conversationSummary: string;
};

const SESSION_STORAGE_KEY = "kingiask-widget:conversation:v1";
const MAX_STORED_MESSAGES = 40;

// 品牌 LOGO：本地静态图片（OEM 图标），相对路径避免内网地址与证书问题。
const LOGO_IMG = `<img class="kiw-logo" src="/logo.png" alt="KingIAsk 标志" />`;

// 创建 HTML 元素并设置文本内容，避免把模型回答直接作为 HTML 注入。
function textElement<K extends keyof HTMLElementTagNameMap>(tag: K, className: string, text: string): HTMLElementTagNameMap[K] {
  const element = document.createElement(tag);
  element.className = className;
  element.textContent = text;
  return element;
}

// 判断 sessionStorage 中的一条历史消息结构是否可用于恢复。
function isStoredMessage(message: unknown): message is StoredMessage {
  if (!message || typeof message !== "object") {
    return false;
  }
  const candidate = message as StoredMessage;
  if (candidate.role === "user") {
    return typeof candidate.text === "string";
  }
  if (candidate.role === "assistant") {
    return typeof candidate.response?.answer === "string" && Array.isArray(candidate.response?.sources);
  }
  return false;
}

// 从当前标签页的 sessionStorage 中读取历史会话和摘要，页面跳转后可以恢复上下文。
function loadStoredConversation(config: ResolvedKingIAskWidgetConfig): StoredConversation {
  const emptyConversation = { messages: [], conversationSummary: "" };
  if (!config.persistSession) {
    return emptyConversation;
  }
  try {
    const raw = window.sessionStorage.getItem(SESSION_STORAGE_KEY);
    if (!raw) {
      return emptyConversation;
    }
    const parsed = JSON.parse(raw);
    if (Array.isArray(parsed)) {
      return { messages: parsed.filter(isStoredMessage), conversationSummary: "" };
    }
    if (!parsed || typeof parsed !== "object" || !Array.isArray(parsed.messages)) {
      return emptyConversation;
    }
    return {
      messages: parsed.messages.filter(isStoredMessage),
      conversationSummary: typeof parsed.conversationSummary === "string" ? parsed.conversationSummary : "",
    };
  } catch {
    return emptyConversation;
  }
}

// 将历史会话和摘要写入 sessionStorage；写入失败时静默降级为不持久化。
function saveStoredConversation(
  config: ResolvedKingIAskWidgetConfig,
  storedMessages: StoredMessage[],
  conversationSummary: string,
): void {
  if (!config.persistSession) {
    return;
  }
  try {
    window.sessionStorage.setItem(
      SESSION_STORAGE_KEY,
      JSON.stringify({
        messages: storedMessages.slice(-MAX_STORED_MESSAGES),
        conversationSummary,
      }),
    );
  } catch {
    // 浏览器隐私模式或存储空间不足时，不影响问答主流程。
  }
}

// 将插件本地消息裁剪为最近 4 轮，发送给后端理解追问。
function buildRecentMessages(messages: StoredMessage[]): ChatHistoryMessage[] {
  return messages.slice(-8).map((message) => {
    if (message.role === "user") {
      return { role: "user", content: message.text };
    }
    return { role: "assistant", content: message.response.answer };
  });
}

// 统计插件本次提问前已有几轮用户提问，用于后端控制摘要更新频率。
function countConversationTurns(messages: StoredMessage[]): number {
  return messages.filter((message) => message.role === "user").length;
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

// 把回答文本中的 [资料 N] 转成锚定链接（仅当对应资料卡存在时），其余内容保持纯文本。
function renderAnswerText(answer: string, sourceCount: number): HTMLElement {
  const container = document.createElement("div");
  container.className = "kiw-answer-text";
  const parts = answer.split(/(\[资料\s*\d+\])/g);
  parts.forEach((part) => {
    const match = part.match(/^\[资料\s*(\d+)\]$/);
    if (match) {
      const num = Number(match[1]);
      if (num >= 1 && num <= sourceCount) {
        const anchor = document.createElement("a");
        anchor.className = "kiw-anchor";
        anchor.href = `#kiw-source-${num}`;
        anchor.dataset.target = `kiw-source-${num}`;
        anchor.textContent = part;
        container.appendChild(anchor);
        return;
      }
    }
    container.appendChild(document.createTextNode(part));
  });
  return container;
}

// 创建复制回答按钮，点击后把回答写入剪贴板并短暂反馈。
function createCopyButton(answer: string): HTMLButtonElement {
  const copyButton = document.createElement("button");
  copyButton.className = "kiw-copy";
  copyButton.type = "button";
  copyButton.textContent = "复制";
  copyButton.addEventListener("click", () => {
    void navigator.clipboard
      ?.writeText(answer)
      .then(() => {
        copyButton.textContent = "已复制";
      })
      .catch(() => {
        copyButton.textContent = "复制失败";
      });
    window.setTimeout(() => {
      copyButton.textContent = "复制";
    }, 1600);
  });
  return copyButton;
}

// 根据来源资料生成展示节点，包含标题、路径、片段和图片缩略图预览。
function renderSource(
  config: ResolvedKingIAskWidgetConfig,
  source: SourceSnippet,
  index: number,
  openImage: (url: string) => void,
): HTMLElement {
  const pageUrl = buildManualPageUrl(source.source_path);
  const wrapper = document.createElement("div");
  wrapper.className = "kiw-source";
  wrapper.id = `kiw-source-${index + 1}`;
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
  source.images.slice(0, 3).forEach((image) => {
    const url = buildManualImageUrl(config, image);
    const thumb = document.createElement("button");
    thumb.className = "kiw-thumb";
    thumb.type = "button";
    thumb.title = image.split("/").pop() ?? "相关图片";
    const img = document.createElement("img");
    img.src = url;
    img.alt = image.split("/").pop() ?? "相关图片";
    img.loading = "lazy";
    img.addEventListener("error", () => img.remove());
    thumb.appendChild(img);
    thumb.appendChild(textElement("span", "kiw-thumb-label", "查看图片"));
    thumb.addEventListener("click", () => openImage(url));
    wrapper.appendChild(thumb);
  });
  return wrapper;
}

// 把 RAG 返回结果渲染到消息区，包含锚定资料、复制按钮和图片预览入口。
function renderAnswer(
  config: ResolvedKingIAskWidgetConfig,
  messages: HTMLElement,
  response: ChatResponse,
  openImage: (url: string) => void,
): void {
  const answer = document.createElement("article");
  answer.className = "kiw-message kiw-message-assistant";
  answer.appendChild(textElement("div", "kiw-message-label", "KingIAsk"));
  answer.appendChild(renderAnswerText(response.answer, response.sources.length));
  if (response.sources.length > 0) {
    const sources = document.createElement("section");
    sources.className = "kiw-sources";
    sources.appendChild(textElement("div", "kiw-sources-heading", "资料来源"));
    response.sources.slice(0, 3).forEach((source, index) =>
      sources.appendChild(renderSource(config, source, index, openImage)),
    );
    answer.appendChild(sources);
  }
  const actions = document.createElement("div");
  actions.className = "kiw-message-actions";
  actions.appendChild(createCopyButton(response.answer));
  answer.appendChild(actions);
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

// 创建 KingIAsk 浮动助手 DOM，并绑定打开、发送、预览和销毁逻辑。
export function createKingIAskWidget(config: ResolvedKingIAskWidgetConfig): WidgetInstance | null {
  if (!config.enabled) {
    return null;
  }

  const host = document.createElement("div");
  host.setAttribute("data-kingiask-widget-root", "true");
  // 自定义品牌主色：通过 CSS 变量覆盖默认 Apple 蓝，同时作用于浅色/深色模式。
  if (config.accentColor) {
    host.style.setProperty("--kiw-accent", config.accentColor);
  }
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
    <span class="kiw-launcher-mark" aria-hidden="true">${LOGO_IMG}</span>
    <span class="kiw-launcher-status" aria-hidden="true"></span>
  `;
  // 悬浮提示：显示助手名称与在线状态（原生 tooltip）。
  launcher.title = `${config.title} · 助手在线`;

  const panel = document.createElement("section");
  panel.className = "kiw-panel";
  panel.dataset.role = "panel";
  panel.setAttribute("role", "dialog");
  panel.setAttribute("aria-labelledby", "kiw-title");
  panel.innerHTML = `
    <header class="kiw-header">
      <div class="kiw-brand">
        <span class="kiw-brand-mark" aria-hidden="true">${LOGO_IMG}</span>
        <div>
          <h2 class="kiw-title" id="kiw-title"></h2>
          <p class="kiw-subtitle">企业知识问答助手 · 助手在线</p>
        </div>
      </div>
      <div class="kiw-header-actions">
        <button class="kiw-clear" type="button" title="清空会话" aria-label="清空会话">清空</button>
        <button class="kiw-close" type="button" aria-label="关闭 KingIAsk">×</button>
      </div>
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
  const storedConversation = loadStoredConversation(config);
  const storedMessages = storedConversation.messages;
  let conversationSummary = storedConversation.conversationSummary;
  // 图片灯箱：全屏遮罩预览资料截图，支持遮罩点击与关闭按钮。
  // 需在渲染历史消息前创建，供 renderAnswer 的缩略图回调引用。
  const lightbox = document.createElement("div");
  lightbox.className = "kiw-lightbox";
  lightbox.innerHTML = `
    <div class="kiw-lightbox-backdrop" data-role="lightbox-close"></div>
    <figure class="kiw-lightbox-body">
      <button class="kiw-lightbox-close" type="button" aria-label="关闭图片预览">×</button>
      <img class="kiw-lightbox-img" alt="资料图片预览" />
      <figcaption class="kiw-lightbox-caption"></figcaption>
    </figure>
  `;
  const lightboxImg = lightbox.querySelector(".kiw-lightbox-img") as HTMLImageElement;
  let lightboxOpen = false;
  const openImage = (url: string) => {
    lightboxImg.src = url;
    lightbox.querySelector(".kiw-lightbox-caption")!.textContent = url.split("/").pop() ?? "";
    lightbox.classList.add("open");
    lightboxOpen = true;
  };
  const closeLightbox = () => {
    lightbox.classList.remove("open");
    lightboxImg.src = "";
    lightboxOpen = false;
  };
  lightbox.querySelector('[data-role="lightbox-close"]')?.addEventListener("click", closeLightbox);
  lightbox.querySelector(".kiw-lightbox-close")?.addEventListener("click", closeLightbox);
  panel.appendChild(lightbox);

  const welcome = document.createElement("article");
  welcome.className = "kiw-message kiw-message-assistant";
  welcome.appendChild(textElement("div", "kiw-message-label", "KingIAsk"));
  welcome.appendChild(textElement("div", "kiw-answer-text", config.welcomeText));
  // 欢迎页推荐问题：点击直接发送，降低首次提问门槛。
  if (config.suggestedQuestions.length > 0) {
    const suggestions = document.createElement("div");
    suggestions.className = "kiw-suggestions";
    config.suggestedQuestions.forEach((question) => {
      const button = document.createElement("button");
      button.className = "kiw-suggestion";
      button.type = "button";
      button.textContent = question;
      button.addEventListener("click", () => void submitQuestion(question));
      suggestions.appendChild(button);
    });
    welcome.appendChild(suggestions);
  }
  messages.appendChild(welcome);
  storedMessages.forEach((message) => {
    if (message.role === "user") {
      renderUserMessage(messages, message.text);
    } else {
      renderAnswer(config, messages, message.response, openImage);
    }
  });

  const openPanel = () => {
    panel.classList.add("open");
    launcher.setAttribute("aria-expanded", "true");
    launcher.style.display = "none";
    window.addEventListener("keydown", onKeydown);
    textarea.focus();
  };
  const closePanel = () => {
    panel.classList.remove("open");
    launcher.setAttribute("aria-expanded", "false");
    launcher.style.display = "";
    window.removeEventListener("keydown", onKeydown);
  };
  // Escape 优先关闭图片灯箱，其次关闭面板。
  const onKeydown = (event: KeyboardEvent) => {
    if (event.key !== "Escape") {
      return;
    }
    if (lightboxOpen) {
      closeLightbox();
    } else {
      closePanel();
    }
  };
  const setLoading = (loading: boolean) => {
    textarea.disabled = loading;
    sendButton.disabled = loading;
    sendButton.textContent = loading ? "处理中" : "发送";
  };
  const submitQuestion = async (prefilled?: string) => {
    const question = (prefilled ?? textarea.value).trim();
    if (!question) return;
    const recentMessages = buildRecentMessages(storedMessages);
    const conversationTurnCount = countConversationTurns(storedMessages);
    if (!prefilled) {
      textarea.value = "";
    }
    renderUserMessage(messages, question);
    storedMessages.push({ role: "user", text: question });
    saveStoredConversation(config, storedMessages, conversationSummary);
    setLoading(true);

    // 创建流式回答气泡：先显示检索状态，收到第一个片段后逐字追加。
    const answer = document.createElement("article");
    answer.className = "kiw-message kiw-message-assistant";
    answer.appendChild(textElement("div", "kiw-message-label", "KingIAsk"));
    const answerText = document.createElement("div");
    answerText.className = "kiw-answer-text";
    answer.appendChild(answerText);
    const loading = renderLoading();
    answer.appendChild(loading);
    messages.appendChild(answer);
    messages.scrollTop = messages.scrollHeight;

    let streamed = "";
    let sources: SourceSnippet[] = [];
    try {
      await askKingIAskStream(
        config,
        question,
        conversationSummary,
        recentMessages,
        conversationTurnCount,
        {
          onChunk: (content) => {
            loading.remove();
            streamed += content;
            answerText.textContent = streamed;
            messages.scrollTop = messages.scrollHeight;
          },
          onSources: (nextSources) => {
            sources = nextSources;
          },
          onDone: (nextSummary) => {
            conversationSummary = nextSummary;
          },
        },
      );

      // 流结束：重建锚定文本，并渲染来源与复制按钮。
      answerText.replaceWith(renderAnswerText(streamed, sources.length));
      if (sources.length > 0) {
        const sourcesSection = document.createElement("section");
        sourcesSection.className = "kiw-sources";
        sourcesSection.appendChild(textElement("div", "kiw-sources-heading", "资料来源"));
        sources.slice(0, 3).forEach((source, index) =>
          sourcesSection.appendChild(renderSource(config, source, index, openImage)),
        );
        answer.appendChild(sourcesSection);
      }
      const actions = document.createElement("div");
      actions.className = "kiw-message-actions";
      actions.appendChild(createCopyButton(streamed));
      answer.appendChild(actions);

      storedMessages.push({ role: "assistant", response: { answer: streamed, sources } });
      saveStoredConversation(config, storedMessages, conversationSummary);
    } catch (error) {
      loading.remove();
      answer.remove();
      const message = error instanceof Error ? error.message : "助手暂时不可用，请稍后再试。";
      messages.appendChild(textElement("div", "kiw-error", message));
    } finally {
      setLoading(false);
    }
  };

  launcher.addEventListener("click", openPanel);
  panel.querySelector(".kiw-close")?.addEventListener("click", closePanel);
  panel.querySelector(".kiw-clear")?.addEventListener("click", () => {
    storedMessages.length = 0;
    conversationSummary = "";
    saveStoredConversation(config, storedMessages, conversationSummary);
    [...messages.children].forEach((child) => {
      if (child !== welcome) {
        child.remove();
      }
    });
    textarea.focus();
  });
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
  // 回答中的 [资料 N] 锚定：点击滚动到对应资料卡并短暂高亮。
  messages.addEventListener("click", (event) => {
    const anchor = (event.target as HTMLElement).closest("a.kiw-anchor") as HTMLAnchorElement | null;
    if (!anchor) {
      return;
    }
    event.preventDefault();
    const targetId = anchor.dataset.target ?? "";
    const sourceEl = targetId ? messages.querySelector(`#${CSS.escape(targetId)}`) : null;
    if (!sourceEl) {
      return;
    }
    sourceEl.scrollIntoView({ behavior: "smooth", block: "nearest" });
    sourceEl.classList.add("kiw-source-flash");
    window.setTimeout(() => sourceEl.classList.remove("kiw-source-flash"), 1600);
  });

  root.append(launcher, panel);
  shadow.append(style, root);
  document.body.appendChild(host);

  return {
    destroy: () => {
      window.removeEventListener("keydown", onKeydown);
      host.remove();
    }
  };
}
