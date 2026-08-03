# KingIAsk Widget 插件使用说明

KingIAsk Widget 是一个可嵌入帮助文档站点的前端问答助手插件。它以一个右下角浮动入口显示，用户点击后可以向 RAG 后端提问，并在回答中查看资料来源、相关图片和对应的帮助文档原文。

## 一、目录说明

```text
kingiask-widget/
├── src/
│   ├── api.ts          # 请求 RAG 接口、构造图片和原文链接
│   ├── config.ts       # 合并默认配置和外部配置
│   ├── index.ts        # 浏览器全局入口 window.KingIAskWidget
│   ├── styles.ts       # Shadow DOM 内部样式
│   ├── types.ts        # 插件配置和接口返回类型
│   └── widget.ts       # 插件 DOM、交互和消息渲染逻辑
├── build.mjs           # 使用 esbuild 打包插件
├── helper-assistant.config.example.js
└── README.md
```

当前 `helperFront` 文档站的运行时文件仍放在：

```text
docs/public/kingiask-widget.js
docs/public/helper-assistant.config.js
```

原因是 Rspress 会把 `docs/public` 作为静态资源目录，浏览器最终从这里加载插件。

## 二、配置文件

宿主项目需要提供一个配置文件，例如：

```js
window.KINGIASK_WIDGET_CONFIG = {
  enabled: true,
  apiBaseUrl: "http://127.0.0.1:8000",
  apiKey: "",
  title: "KingIAsk",
  welcomeText: "你好，我可以帮你查询 KF 产品手册。",
  position: "right-bottom",
  timeoutMs: 60000,
  persistSession: true
};
```

配置项说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `enabled` | `boolean` | 是否显示助手。内网文档或不需要助手的页面可以设为 `false`。 |
| `apiBaseUrl` | `string` | RAG 后端服务地址，例如本地 `http://127.0.0.1:8000`，服务器部署后改成服务器地址。 |
| `apiKey` | `string` | 可选请求密钥。本地 `DISABLE_AUTH=true` 时可以留空。 |
| `title` | `string` | 助手显示名称。 |
| `welcomeText` | `string` | 打开助手后的欢迎语。 |
| `position` | `"right-bottom"` 或 `"left-bottom"` | 浮动入口位置。 |
| `timeoutMs` | `number` | 请求超时时间，单位毫秒。 |
| `persistSession` | `boolean` | 是否在当前浏览器标签页中保持会话。设为 `true` 后，点击资料原文跳转页面再打开助手，之前的问题和回答仍会显示。 |

注意：浏览器里的 `apiKey` 不是严格意义上的秘密。用户只要能访问页面，就能在浏览器开发者工具中看到这个值。正式企业部署时，更推荐使用同源代理、登录态 Cookie 或网关鉴权。

## 三、在 helperFront 中构建

进入 `helperFront` 目录：

```bash
cd helperFront
```

安装依赖：

```bash
npm install
```

构建插件：

```bash
npm run build:widget
```

构建后会生成：

```text
docs/public/kingiask-widget.js
docs/public/helper-assistant.config.js
```

启动文档站：

```bash
npm run dev
```

如果本机默认 Node 版本有问题，可以使用 Node 22：

```bash
PATH="$HOME/.nvm/versions/node/v22.14.0/bin:$PATH" npm run dev
```

## 四、在 Rspress 中接入

在 `rspress.config.ts` 的 `builderConfig.html.tags` 中加入两个脚本：

```ts
{
  tag: 'script',
  attrs: { src: '/helper-assistant.config.js' },
  head: false,
},
{
  tag: 'script',
  attrs: { src: '/kingiask-widget.js' },
  head: false,
}
```

顺序很重要：先加载配置，再加载插件。

## 五、在普通 HTML 页面中接入

把下面两个文件放到站点可访问的静态资源目录：

```text
helper-assistant.config.js
kingiask-widget.js
```

然后在 HTML 的 `body` 末尾引入：

```html
<script src="/helper-assistant.config.js"></script>
<script src="/kingiask-widget.js"></script>
```

页面加载后，插件会自动读取 `window.KINGIASK_WIDGET_CONFIG` 并初始化。

## 六、会话保持

默认配置中：

```js
persistSession: true
```

插件会把当前标签页里的问答历史保存到 `sessionStorage`。这样用户点击“查看原文”跳转到帮助文档页面后，再打开助手，之前的问题、回答和资料来源仍然存在。

这个存储只在当前浏览器标签页内有效。关闭标签页后，浏览器会自动清理这部分会话数据。

如果某些内网页面不希望保留会话，可以关闭：

```js
persistSession: false
```

## 七、手动控制显示

插件加载后会暴露全局对象：

```js
window.KingIAskWidget
```

隐藏助手：

```js
window.KingIAskWidget.destroy();
```

重新显示助手：

```js
window.KingIAskWidget.init({
  enabled: true,
  apiBaseUrl: "http://127.0.0.1:8000"
});
```

## 八、RAG 后端接口要求

插件默认请求：

```text
POST {apiBaseUrl}/api/chat
```

请求体：

```json
{
  "question": "如何创建采集工程？"
}
```

响应体需要包含：

```json
{
  "answer": "回答内容",
  "sources": [
    {
      "title": "资料标题",
      "source_path": "helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置.md",
      "snippet": "资料片段",
      "evidence_ids": ["资料 1"],
      "images": ["helperFront/入门指南/image/demo.png"],
      "score": 0.9
    }
  ]
}
```

如果 `source_path` 是 Markdown 路径，插件会把它转换成帮助文档页面链接。例如：

```text
helperFront/入门指南/2_从零搭建一个KF工程/2_数据采集配置.md
```

会转换为：

```text
/入门指南/2_从零搭建一个KF工程/2_数据采集配置
```

## 九、常见问题

### 1. 页面不显示助手

检查 `helper-assistant.config.js`：

```js
enabled: true
```

再检查浏览器是否能访问：

```text
/kingiask-widget.js
/helper-assistant.config.js
```

### 2. 助手提示接口不可用

检查 RAG 后端是否启动：

```bash
curl http://127.0.0.1:8000/api/health
```

如果文档站和后端不是同源，还要检查后端 CORS 是否允许当前文档站地址。

### 3. 点击资料原文后 404

说明 `source_path` 和文档站 URL 规则不一致。当前插件支持下面几类前缀：

```text
helperFront/
helperFront/docs/
docs/
```

如果后端返回的是其他路径格式，需要在 `src/api.ts` 的 `buildManualPageUrl()` 中补充映射规则。

### 4. 图片打不开

插件会把图片路径转换为：

```text
{apiBaseUrl}/manuals/{imagePath}
```

因此后端需要挂载 `/manuals` 静态资源，并且 `imagePath` 要能对应到后端的手册文件。
