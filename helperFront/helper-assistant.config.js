window.KINGIASK_WIDGET_CONFIG = {
  enabled: true,
  apiBaseUrl: "http://127.0.0.1:8000",
  apiKey: "",
  title: "KingIAsk",
  welcomeText: "你好，我可以帮你查询 KF 产品手册。",
  position: "right-bottom",
  timeoutMs: 60000,
  persistSession: true,
  // 欢迎页推荐问题，点击直接提问，最多 4 个。
  suggestedQuestions: [
    "如何创建采集工程？",
    "客户端支持哪些系统？",
    "如何查看运维中心日志？"
  ]
  // 自定义品牌主色示例（覆盖默认 Apple 蓝）：
  // accentColor: "#ff6b00",
};
