import fs from 'node:fs/promises';

const entry = `<!doctype html>
<html lang="zh-CN">
  <head>
    <meta charset="UTF-8" />
    <meta http-equiv="refresh" content="0;url=/入门指南/1_KF核心概念与基础入门/1_KF核心概念与基础入门.html" />
    <title>KingFusion4.5 帮助手册</title>
  </head>
  <body>
    <a href="/入门指南/从零搭建一个KF工程/1_KF核心概念与基础入门/1_KF核心概念与基础入门.html">进入入门指南</a>
  </body>
</html>
`;

await fs.writeFile('doc_build/index.html', entry, 'utf8');
