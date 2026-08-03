import fs from 'node:fs/promises';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), 'docs');

// 文档源目录。所有导航元数据都从这里扫描生成，不需要手工维护 _meta.json。
// Rspress 会自动处理 Markdown 页面，但不会自动复制所有附件，因此下面还会
// 单独复制图片、JSON、Excel 等静态资源。
const staticExtensions = new Set([
  '.xlsx',
  '.json',
  '.zip',
  '.rar',
  '.png',
  '.jpg',
  '.jpeg',
  '.gif',
  '.bmp',
  '.svg',
  '.webp',
]);

const sortEntries = (entries) =>
  // 使用中文排序并启用 numeric，确保 2_项目 排在 10_项目 前面。
  entries.sort((a, b) =>
    a.label.localeCompare(b.label, 'zh-CN', { numeric: true }),
  );

// 仅格式化导航显示名称，不修改真实文件名和路由路径。
// 例如：2_页面管理 -> 2.页面管理，10_移动端布局 -> 10.移动端布局。
const formatLabel = (name) => name.replace(/^(\d+)_/, '$1.');

async function scanDirectory(directory) {
  // 递归扫描一个目录并生成该目录的 _meta.json。
  // image、media 等只存放附件的目录会保留在文件系统中，但不额外占用导航层级。
  const entries = await fs.readdir(directory, { withFileTypes: true });
  const files = entries.filter(
    (entry) => entry.isFile() && entry.name.endsWith('.md'),
  );
  const directories = entries.filter(
    (entry) =>
      entry.isDirectory() &&
      !['superpowers', 'public', 'image', 'images', 'media', 'assets'].includes(
        entry.name.toLowerCase(),
      ),
  );

  const meta = [
    ...files.map((file) => ({
      type: 'file',
      name: file.name.slice(0, -3),
      label: formatLabel(file.name.slice(0, -3)),
    })),
    ...(await Promise.all(
      directories.map(async (dir) => {
        const child = await fs.readdir(path.join(directory, dir.name), {
          withFileTypes: true,
        });
        const childFiles = child.filter(
          (entry) => entry.isFile() && entry.name.endsWith('.md'),
        );
        const contentDirectories = child.filter(
          (entry) =>
            entry.isDirectory() &&
            !['image', 'images', 'media', 'assets'].includes(
              entry.name.toLowerCase(),
            ),
        );
        if (childFiles.length === 1 && contentDirectories.length === 0) {
          return {
            type: 'file',
            name: `${dir.name}/${childFiles[0].name.slice(0, -3)}`,
            label: formatLabel(dir.name),
          };
        }
        return {
          type: 'dir',
          name: dir.name,
          label: formatLabel(dir.name),
          collapsed: true,
        };
      }),
    )),
  ];

  sortEntries(meta);
  if (directory !== root) {
    await fs.writeFile(
      path.join(directory, '_meta.json'),
      `${JSON.stringify(meta, null, 2)}\n`,
    );
  }

  for (const dir of directories) {
    await scanDirectory(path.join(directory, dir.name));
  }
}

async function generateRootNav() {
  // 生成顶部导航。目录名可能发生调整，因此这里明确规定用户看到的顺序，
  // 同时为每个栏目选择第一个 Markdown 页面作为进入该栏目的默认页面。
  const entries = await fs.readdir(root, { withFileTypes: true });
  const directoryOrder = ['入门指南', '详细教程', '实战案例'];
  const directories = directoryOrder
    .map((name) =>
      entries.find((entry) => entry.isDirectory() && entry.name === name),
    )
    .filter(Boolean);
  const nav = [];
  for (const dir of directories) {
    const files = await findMarkdownFiles(path.join(root, dir.name));
    const first = files[0];
    nav.push({
      text: formatLabel(dir.name),
      link: `/${first ? path.relative(root, first).replace(/\\/g, '/').replace(/\.md$/, '.html') : dir.name}`,
      activeMatch: `^/${dir.name}/`,
    });
  }
  await fs.writeFile(
    path.join(root, '_nav.json'),
    `${JSON.stringify(nav, null, 2)}\n`,
  );
}

async function findMarkdownFiles(directory) {
  // 查找目录下所有 Markdown，用于确定顶部导航的默认入口页面。
  const result = [];
  for (const entry of await fs.readdir(directory, { withFileTypes: true })) {
    const source = path.join(directory, entry.name);
    if (entry.isDirectory()) result.push(...(await findMarkdownFiles(source)));
    else if (entry.isFile() && entry.name.endsWith('.md')) result.push(source);
  }
  return result.sort((a, b) => a.localeCompare(b, 'zh-CN', { numeric: true }));
}

async function copyStaticFiles() {
  // 将文档引用的附件复制到 doc_build，并保持相对于 docs 的目录结构。
  // 只复制白名单扩展名，避免把导航元数据或临时文件带进产物。
  const output = path.resolve(path.dirname(root), 'doc_build');
  const stack = [root];
  while (stack.length) {
    const directory = stack.pop();
    const entries = await fs.readdir(directory, { withFileTypes: true });
    for (const entry of entries) {
      const source = path.join(directory, entry.name);
      if (entry.isDirectory()) {
        if (entry.name !== 'superpowers') stack.push(source);
        continue;
      }
      if (!staticExtensions.has(path.extname(entry.name).toLowerCase()))
        continue;
      const target = path.join(output, path.relative(root, source));
      await fs.mkdir(path.dirname(target), { recursive: true });
      await fs.copyFile(source, target);
    }
  }
}

await generateRootNav();
await scanDirectory(root);
// await copyStaticFiles();
