import * as path from 'node:path';
import { defineConfig } from '@rspress/core';

export default defineConfig({
  // Rspress 的文档根目录，所有 Markdown 和导航元数据都位于 docs 下。
  root: path.join(__dirname, 'docs'),
  title: 'KingFusion3.6帮助手册',
  markdown: {
    // 文档中存在历史遗留的外部图片和旧链接，关闭死链检查避免构建被阻断。
    link: { checkDeadLinks: false },
    shiki: { langs: ['js', 'html', 'css', 'json'], fallbackLanguage: 'js' },
  },
  themeConfig: {
    // 保持长文档阅读时的滚动体验，并启用页面切换动画。
    enableScrollToTop: true,
    enableContentAnimation: true,
  },
  builderConfig: {
    // 开发时关闭错误遮罩，避免单个历史文档资源问题遮挡整页预览。
    dev: { client: { overlay: false } },
    // 文档站页面和图片数量较多，关闭 Rspack 持久化缓存，避免
    // node_modules/.cache 持续增长。代价是重复构建会稍慢一些。
    tools: {
      rspack: {
        cache: false,
      },
    },
    html: {
      tags: [
        {
          tag: 'script',
          attrs: { src: '/helper-assistant.config.js' },
          head: false,
        },
        {
          tag: 'script',
          attrs: { src: '/kingiask-widget.js' },
          head: false,
        },
        {
          tag: 'script',
          children: `
document.addEventListener('DOMContentLoaded', () => {
  // 根路径没有对应 Markdown 页面时，直接进入入门指南的第一篇文档。
  if (window.location.pathname === '/' || window.location.pathname === '') {
    window.location.replace('/入门指南/从零搭建一个KF工程/1_从零搭建一个KF工程');
    return;
  }
  document.querySelectorAll('a[href$=".json"]').forEach(a => {
    // JSON 通常是示例数据，点击时直接下载而不是在浏览器中打开。
    a.setAttribute('download', '');
  });
  // 正文中的历史链接只作为文字说明展示，禁止页面跳转。
  // 导航栏、侧栏、页面大纲和附件下载链接不受影响。
  document.addEventListener('click', event => {
    const link = event.target.closest('.rspress-doc a[href]');
    if (!link || link.hasAttribute('download')) return;
    event.preventDefault();
  });
  const applyNavState = () => {
    // 顶部导航由 Rspress 异步渲染，因此根据当前 URL 持续补充选中样式。
    const currentPath = window.location.pathname;
    document.querySelectorAll('.rp-nav-menu .nav-current').forEach(item => item.classList.remove('nav-current'));
    document.querySelectorAll('.rp-nav-menu a[href]').forEach(link => {
      const href = link.getAttribute('href');
      if (!href || href.startsWith('http') || href === '/') return;
      const targetPath = new URL(href, window.location.origin).pathname;
      const section = targetPath.split('/')[1];
      if (section && currentPath.split('/')[1] === section) {
        link.classList.add('nav-current');
      }
    });
  };
  applyNavState();
  new MutationObserver(applyNavState).observe(document.body, { childList: true, subtree: true });
const style = document.createElement('style');
// 这些样式统一控制三栏宽度、侧栏标题、顶部栏目选中态。
style.textContent =
 ':root{'+
    '  --rp-sidebar-width: 340px;'+
    '  --rp-outline-width: 260px;'+
    '  --rp-content-max-width: 1200px;'+
  '}'+
  '.rp-doc-layout__sidebar, .rp-doc-layout__sidebar-placeholder {'+
    '  box-sizing: border-box;'+
    '  width: var(--rp-sidebar-width) !important;'+
    '  min-width: var(--rp-sidebar-width) !important;'+
    '  max-width: var(--rp-sidebar-width) !important;'+
  '}'+
 '.rp-doc-layout__sidebar > div{'+
    '  font-size: 16px;'+
     '  font-weight: bold;'+
  '}'+
 '.rp-doc-layout__sidebar > a > div{'+
    '  font-size: 16px;'+
     '  font-weight: bold;'+
  '}'+
  '.rp-nav-menu a:not(.nav-current) {'+
    '  color: var(--rp-c-text-1) !important;'+
    '  font-weight: 400 !important;'+
  '}'+
  '.rp-nav-menu a.nav-current {'+
    '  color: #1677ff !important;'+
    '  font-weight: 600 !important;'+
  '}'+
  '.rspress-doc a[href]:not([download]) {'+
    '  color: inherit !important;'+
    '  text-decoration: none !important;'+
    '  cursor: text !important;'+
  '}'
document.head.appendChild(style);
});
        `,
          head: false,
        },
      ],
    },
  },
});
