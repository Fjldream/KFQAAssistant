# KingFusion 帮助手册

这是一个基于 [Rspress](https://rspress.dev/) 的静态文档网站项目。项目将 `docs` 目录中的 Markdown 文档编译为 HTML，并自动生成顶部导航、左侧目录、右侧页面大纲以及图片、JSON、Excel 等静态资源。

## 一、项目定位

本项目不是业务系统，也不是后端服务，而是一个可以部署到 Nginx、IIS、Apache、对象存储或 CDN 的静态网站。

主要特点：

- 使用 Markdown 编写文档。
- 使用 Rspress 负责页面渲染、搜索、代码高亮、侧栏和页面大纲。
- 使用 `genMeta.js` 自动扫描 `docs` 并生成导航元数据。
- 构建结果输出到 `doc_build`，部署时只需要上传该目录。
- 文档新增、删除、移动后，不需要手工维护大量 `_meta.json`。

## 二、目录结构

```text
helper_KF3.6/
├── docs/                 # 文档源文件，只在这里新增或修改文档
│   ├── 入门指南/          # 第一栏：入门指南
│   ├── 详细教程/          # 第二栏：详细信息
│   ├── 实战案例/          # 第三栏：实战案例
│   └── _nav.json          # 自动生成的顶部导航
├── doc_build/             # npm run build 生成的部署产物
├── genMeta.js             # 自动生成导航和复制静态资源
├── create-entry.mjs       # 构建后补充根路径 index.html
├── rspress.config.ts      # Rspress、主题和页面样式配置
├── package.json            # 命令和依赖
├── package-lock.json       # 依赖锁定文件
└── README.md               # 项目说明
```

`node_modules`、`.cache`、`.rspress` 等目录属于依赖或构建缓存，不是文档内容，也不需要部署到服务器。

## 三、docs 文档放置规则

### 3.1 顶层目录

`docs` 下目前使用三个顶层栏目，名称和顺序由 `genMeta.js` 中的 `directoryOrder` 控制：

```text
docs/
├── 入门指南/
├── 详细教程/
└── 实战案例/
```

新增顶层栏目时，需要同时修改 `genMeta.js` 的栏目顺序数组，否则它不会出现在顶部导航中。

### 3.2 Markdown 文件

所有页面使用 `.md` 文件：

```text
docs/详细教程/基础配置/安装配置.md
```

文件名会作为页面路由和默认菜单标题。建议遵守以下命名规则：

- 使用中文或清晰的功能名称。
- 同一目录下需要排序时，使用 `1_`、`2_`、`10_` 等数字前缀。
- 数字前缀必须保持一致，不要混用 `1.`、`01`、`一、` 等多种形式。
- 文件名不要包含 `?`、`#`、`%` 等 URL 特殊字符。
- 不要使用同一目录下完全相同的文件名。

例如：

```text
2_页面管理/
├── 1_基础配置介绍.md
├── 2_页面设计.md
└── 3_发布管理.md
```

### 3.3 子目录和层级

目录层级就是左侧目录层级。推荐一个目录只承担一个清晰的功能分类：

```text
2_页面管理/
├── 1_基础配置介绍.md
├── 2_布局容器/
│   ├── 1_基础配置介绍.md
│   ├── 2_水平布局.md
│   └── 3_垂直布局.md
└── 3_组件管理/
```

如果一个目录只有一个 Markdown 页面，脚本会将它自动扁平化为一个菜单项，避免出现“目录 -> 同名页面”的重复层级。

如果一个目录同时包含多个 Markdown 页面，它会作为父目录展开，页面显示为子项。

### 3.4 图片和附件

图片建议放在当前 Markdown 文件旁边的 `image` 目录中：

```text
页面管理/
├── 页面管理.md
└── image/
    ├── 页面管理.png
    └── 页面管理-配置.png
```

Markdown 中使用相对路径，并统一使用 `/`：

```markdown
![页面管理](./image/页面管理.png)
```

不要使用：

```markdown
![错误路径](.\image\页面管理.png)
![本机路径](F:\测试技术\图片.png)
```

支持自动复制的静态文件扩展名包括：`.png`、`.jpg`、`.jpeg`、`.gif`、`.bmp`、`.svg`、`.webp`、`.json`、`.xlsx`、`.zip` 和 `.rar`。

### 3.5 `_meta.json` 和 `_nav.json`

通常不要手工编辑这些文件。运行以下命令会根据目录重新生成：

```bash
npm run generate:meta
```

- 根目录 `docs/_nav.json` 控制顶部导航。
- 各级目录 `_meta.json` 控制左侧目录。
- `image`、`media`、`assets` 等资源目录不会被作为普通导航层级展开。

## 四、主要文件说明

### `genMeta.js`

这是项目的导航生成器，负责：

1. 递归扫描 `docs` 中的目录和 Markdown。
2. 为各级目录生成 `_meta.json`。
3. 按固定顺序生成 `docs/_nav.json`。
4. 为顶部栏目选择第一个 Markdown 页面作为入口。
5. 将图片、JSON、Excel 等附件复制到 `doc_build`。

每次执行 `npm run dev` 或 `npm run build` 都会先运行它。

### `rspress.config.ts`

这是 Rspress 主配置文件，负责：

- 设置 `docs` 为文档根目录。
- 设置网站标题。
- 配置 Markdown 链接检查和代码高亮语言。
- 配置页面动画、滚动行为和开发错误遮罩。
- 设置三栏布局宽度。
- 在根路径跳转到入门指南。
- 将 JSON 链接设置为下载行为。
- 保持顶部导航当前栏目高亮。

### `create-entry.mjs`

Rspress 对没有根级 `index.md` 的项目不会自动生成根 `index.html`。该脚本在构建完成后补充 `doc_build/index.html`，并将访问根地址的用户跳转到入门指南。

### `package.json`

主要命令如下：

| 命令                    | 作用                       |
| ----------------------- | -------------------------- |
| `npm install`           | 安装依赖                   |
| `npm run generate:meta` | 重新生成导航和复制静态资源 |
| `npm run dev`           | 启动开发服务器             |
| `npm run build`         | 生成生产构建产物           |
| `npm run preview`       | 预览生产构建结果           |
| `npm run format`        | 使用 Prettier 格式化项目   |

## 五、开发和调试

### 5.1 环境要求

建议使用 Node.js 20 或更高版本。Rspress 及其构建依赖可能使用 Node.js 20 提供的 API，Node.js 18 可能出现 `node:util.styleText` 错误。

检查版本：

```bash
node --version
npm --version
```

### 5.2 启动开发服务器

```bash
npm install
npm run dev
```

开发服务器启动后，按照终端提示打开地址。修改 Markdown、导航配置或页面样式后，浏览器通常会自动刷新；如果旧样式仍存在，请使用 `Ctrl+F5` 强制刷新。

### 5.3 调试导航

如果页面没有出现在左侧目录：

```bash
npm run generate:meta
```

然后检查：

- 当前 Markdown 是否位于 `docs` 下。
- 文件扩展名是否为 `.md`。
- 所在目录是否被命名为 `image`、`media` 等资源目录。
- 对应目录的 `_meta.json` 是否已经生成。

如果顶部栏目不显示，检查 `genMeta.js` 的 `directoryOrder` 是否包含该目录名。

### 5.4 调试图片

图片无法显示时，优先检查：

1. 图片是否真实存在。
2. Markdown 路径是否以 `./` 开头。
3. 路径是否使用 `/` 而不是 `\`。
4. 文件名大小写是否一致。
5. 图片是否放在当前 Markdown 文件的相对目录下。

可以先运行：

```bash
npm run build
```

Rspress 会在构建阶段报告找不到的图片路径。

### 5.5 清理缓存

项目已在 `rspress.config.ts` 中关闭 Rspack 持久化文件缓存，后续构建不会继续累积 `node_modules/.cache`。之前已经产生的旧缓存仍然可以安全删除一次：

```powershell
Remove-Item node_modules\.cache -Recurse -Force
```

关闭缓存后，重复构建的速度可能比默认配置稍慢，但可以避免缓存持续占用磁盘空间。

## 六、构建和部署

### 6.1 构建

```bash
npm run build
```

构建流程依次执行：

1. `npm run generate:meta`：生成导航和复制静态资源。
2. `rspress build`：将 Markdown 编译为静态 HTML、CSS 和 JavaScript。
3. `node create-entry.mjs`：补充根目录 `index.html`。

成功后产物位于：

```text
doc_build/
├── index.html
├── 404.html
├── static/
├── 入门指南/
├── 详细教程/
└── 实战案例/
```

### 6.2 部署原则

正式服务器只需要上传整个 `doc_build` 目录，不需要上传：

- `node_modules`
- `docs`
- `.cache`
- `.rspress`
- `genMeta.js`
- `rspress.config.ts`

生产环境甚至不需要安装 Node.js，只要有静态文件服务器即可。

### 6.3 Nginx 部署

```nginx
server {
    listen 80;
    server_name help.example.com;

    root /var/www/helper/doc_build;
    index index.html;

    location / {
        try_files $uri $uri/ $uri.html /index.html;
    }
}
```

检查并重载：

```bash
sudo nginx -t
sudo systemctl reload nginx
```

### 6.4 IIS、Apache 和对象存储

- IIS：将 `doc_build` 设置为网站根目录，默认文档设置为 `index.html`。
- Apache：将 `doc_build` 设置为 `DocumentRoot`，确保启用静态文件访问。
- 对象存储/CDN：上传 `doc_build` 全部文件，并设置默认首页为 `index.html`。

## 七、常见问题

### 构建时报 `styleText` 不存在

这是 Node.js 版本过低导致的。升级到 Node.js 20 或更高版本。

### 顶部导航点击后不切换

先重新生成导航并重新启动服务：

```bash
npm run generate:meta
npm run dev
```

部署静态文件时，确认服务器允许访问带中文目录和 `.html` 后缀的路径。

### 根目录显示 404

确认已经执行完整构建：

```bash
npm run build
```

并确认 `doc_build/index.html` 存在。

### 服务器显示目录但页面打不开

确认上传的是整个 `doc_build`，而不是只上传其中的 `static`、某个栏目目录或单个 HTML 文件。

## 八、推荐工作流

新增文档时建议按以下顺序：

```bash
# 1. 在 docs 对应栏目下创建 Markdown 和资源目录
# 2. 使用相对路径插入图片
# 3. 生成导航
npm run generate:meta

# 4. 启动开发服务器检查页面
npm run dev

# 5. 构建生产版本
npm run build

# 6. 将 doc_build 上传到服务器
```

只要遵守“Markdown 放在对应栏目、附件使用相对路径、导航由脚本生成”这三条规则，就可以持续扩展整个帮助文档系统。
