# 摄影网站维护手册

最后更新：2026-09-09

## 1. 网站概览

- 线上地址：https://zncu-photo.pages.dev/
- Cloudflare Pages 项目：`zncu-photo`
- 本地项目：`D:\Claude_gc\photography-home`
- 原始照片：`D:\Nikon z30\zfc`
- 技术栈：Hexo 8.1.2 + NexT 8.29.0，Scheme 为 Muse
- 内容形式：每个照片文件夹对应一篇摄影日志
- 永久链接：`/album/YYYYMMDD/`
- 联系邮箱：`liam1093909131@gmail.com`
- GitHub：https://github.com/Ramsey-L
- 访问统计：Cloudflare Pages Functions + D1（数据库 `zncu-photo-stats`，绑定名 `VISITS_DB`）
- 趣味入口：`/explore/` 摄影地图

## 2. 当前内容

截至 2026-09-09：

- 相册：15 个
- 公开照片：215 张
- 隐藏照片：23 张
- 首页：每页显示 8 篇摄影日志，按日期倒序
- 第二页：`/page/2/`
- 归档：`/archives/`
- 关于我：`/about/`
- 摄影地图：`/explore/`，包含 15 个相册地点、到访盖章、摄影向导、6 个可收集胶卷和时间暗房
- 首页统计：累计匿名访客、累计浏览量、今日访问量和运行天数

最新加入：

| 日期 | 相册 | 公开照片 |
| --- | --- | ---: |
| 2026-07-30 | 拍月 | 2 |
| 2026-08-09 | 海边半日 | 11 |
| 2026-08-31 | 抚宁记忆 | 8 |
| 2026-09-04 | 嘉定闲游 | 8 |
| 2026-09-05 | 南翔古镇 | 17 |

`南翔古镇`中的 `佰宁.JPG` 被隐私规则排除。

## 3. 目录结构

```text
photography-home/
├── _config.yml                  # Hexo 主配置
├── _config.next.yml             # NexT Muse 配置
├── package.json
├── package-lock.json
├── requirements.txt
├── wrangler.toml               # Pages 项目与 D1 绑定
├── functions/api/visit.js      # 匿名访问统计接口
├── migrations/0001_visit_stats.sql
├── scripts/copy-routes.js      # 输出 Cloudflare Functions 路由规则
├── source/
│   ├── _posts/                  # 自动生成的摄影日志
│   ├── about/index.md           # 自动生成的关于页
│   ├── explore/                 # 独立摄影探索界面与地图数据
│   ├── _routes.json             # 仅 /api/* 调用 Pages Functions
│   ├── images/
│   │   ├── avatar.jpg
│   │   └── albums/              # 公开大图与 thumbs 缩略图
│   └── _data/
│       ├── body-end.njk         # 首页首屏、访问统计脚本与页尾信息
│       ├── photo-manifest.json  # 导入结果和排除记录
│       └── styles.styl          # 摄影站定制样式
├── tools/
│   ├── import_photos.py         # 照片导入器
│   └── verify_public.py         # 发布前检查
├── public/                      # Hexo 生产输出
└── SITE_MAINTENANCE.md
```

`public/`、`source/_posts/` 和 `source/images/albums/` 都由工具生成，不应手工修改。

## 4. 照片目录规则

每个相册必须放在：

```text
D:\Nikon z30\zfc\YYYYMMDD相册名称\
```

例如：

```text
D:\Nikon z30\zfc\20260905南翔古镇\
```

要求：

1. 文件夹名称必须以 8 位日期开头。
2. 支持 `.jpg`、`.jpeg`、`.png`。
3. 照片按文件名自然排序。
4. 文件夹名称去掉日期后作为日志标题。
5. 路由只使用日期，避免中文 URL 和改名导致链接失效。

特殊显示名在 `tools/import_photos.py` 的 `ROLL_PLACE_OVERRIDES` 中维护。

跨日期相册在 `ROLL_DATE_OVERRIDES` 中维护。

## 5. 隐私规则

隐私规则集中在 `tools/import_photos.py`：

```python
EXCLUDED_WORDS = ("苑", "佰宁")
EXCLUDED_PHOTO_TITLES = {
    "我在乍浦路",
    "镜中的我们",
    "滨江的我",
    "我在静安寺",
}
```

照片标题、文件名或相册名命中规则时：

- 不生成公开图片；
- 不写入摄影日志；
- 只把相对于 `zfc` 的路径记录到本地 manifest；
- 发布检查会再次扫描 HTML、CSS、JS、JSON 和 XML。

绝对不要直接部署原始照片目录，也不要绕过 `npm run check`。

## 6. 图片处理

`tools/import_photos.py` 会：

- 读取并应用 EXIF 方向；
- 转换为 RGB JPEG；
- 大图最大宽度 2200px，质量 88；
- 缩略图最大宽度 960px，质量 82；
- 使用源文件相对路径哈希生成稳定文件名；
- 保留拍摄日期、光圈、快门、ISO 和焦距；
- 只重新处理新增或修改过的照片；
- 删除已经从源目录移除的生成图片和日志。

大图用于首页封面和 Fancybox，缩略图用于日志内照片墙。

## 7. 日常更新流程

打开 PowerShell：

```powershell
cd D:\Claude_gc\photography-home
python tools\import_photos.py
npm run build
npm run check
```

本地预览：

```powershell
npm run server -- -p 4173
```

浏览器访问：

```text
http://localhost:4173/
```

至少检查：

- 首页最新日志标题和封面；
- 新相册详情页；
- Fancybox 是否能打开、翻页和关闭；
- `/archives/`；
- `/about/`；
- 手机宽度是否有横向滚动；
- 浏览器控制台是否为 0 error。

## 8. 部署

确认构建和检查通过后：

```powershell
cd D:\Claude_gc\photography-home
npx --yes wrangler@4.130.0 pages deploy --branch main
```

只部署 `public/`，不要部署项目根目录。

部署完成后在线检查：

- `https://zncu-photo.pages.dev/`
- `https://zncu-photo.pages.dev/album/最新日期/`
- `https://zncu-photo.pages.dev/about/`
- `https://zncu-photo.pages.dev/archives/`
- `https://zncu-photo.pages.dev/explore/`
- `https://zncu-photo.pages.dev/api/visit`

必要时在 URL 后添加查询参数绕过浏览器缓存，例如 `?v=20260909`。

## 8.1 访问统计维护

统计口径：

- 访客人数：浏览器首次访问时生成随机 ID，服务端只保存其 SHA-256 摘要；
- 访问次数：每次完整页面加载计为一次浏览；
- 今日访问：按上海时区统计当天浏览次数；
- 不保存原始 IP、User-Agent、访问路径或个人资料；
- 探索页的胶卷与地标到访进度只保存在浏览器 `localStorage`，键名分别为 `zncu-photo-films` 和 `zncu-photo-visited`。

首次重建数据库时执行：

```powershell
npx --yes wrangler@4.130.0 d1 execute zncu-photo-stats --remote --file migrations\0001_visit_stats.sql
```

`wrangler.toml` 是 Pages 配置来源，`VISITS_DB` 必须绑定到 `zncu-photo-stats`。静态资源不调用 Function，只有 `/api/*` 进入 Pages Functions。

## 9. 前端定制

主题配置只修改：

- `_config.next.yml`
- `source/_data/styles.styl`
- `source/_data/body-end.njk`

不要编辑：

- `node_modules/hexo-theme-next/`
- `public/css/main.css`
- `public/*.html`

原因：这些内容会在 `npm install` 或 `npm run build` 后被覆盖。

当前视觉原则：

- NexT Muse 黑白个人博客结构；
- 首页按日期展示大封面摄影日志；
- 正文最大宽度 1120px；
- 相册详情使用全宽图片网格；
- 手机端改为单列；
- 首页顶部显示匿名访问统计，并提供醒目的 GitHub 入口；
- 首页角色可随机打开相册，`/explore/` 提供键盘与触摸探索；
- 探索页会记录地标到访状态，未到访照片以灰度显示，到访后恢复彩色并盖章；
- 胶卷收集进度保存在浏览器本地，每卷胶片在时间暗房显影一张照片，集齐后形成完整接触印样；
- 页尾以小字号显示“关于我”、邮箱和 `Powered by Hexo & NexT.Muse`；
- 支持 reduced-motion；
- 不启用评论系统；
- Fancybox 开启，PJAX 关闭。

## 10. 依赖维护

当前锁定：

- Node.js：本机 24.x
- Hexo：8.1.2
- NexT：8.29.0

安装：

```powershell
npm install
```

不要全局安装 Hexo CLI。项目命令会自动使用 `node_modules/.bin/hexo`。

升级 NexT 前必须：

1. 备份项目；
2. 阅读 NexT release notes；
3. 更新锁定版本；
4. 运行 `npm install`；
5. 重新导入、构建、检查；
6. 完整执行桌面端和手机端测试。

## 11. 回退

本次迁移前备份：

```text
D:\Claude_gc\photography-home-backup-20260909
```

如果必须回退：

1. 不要删除备份；
2. 先保存当前 Hexo 工程；
3. 将备份恢复为 `D:\Claude_gc\photography-home`；
4. 按旧版维护手册中的 `prepare_deploy.py` 流程重新部署。

## 12. 故障排查

### Hexo 只显示 help/init/version

确认 `package.json` 中存在：

```json
"hexo": {
  "version": "8.1.2"
}
```

### 首页不显示封面

确认 `_config.next.yml`：

```yaml
excerpt_description: false
read_more_btn: true
```

不要在日志 Front Matter 使用 `photos` 字段，它是 NexT 保留字段。本站使用 `photo_count`。

### 构建出现 Stylus min() 错误

Stylus 会把 CSS `min()` 当作数学函数。使用 `max-width` 与 `calc()` 组合，不直接写 `width: min(...)`。

### Fancybox 不工作

确认：

```yaml
fancybox: true
mediumzoom: false
```

并检查 CDN 资源是否被网络拦截。

### Wrangler 登录失效

运行：

```powershell
npx --yes wrangler@4.130.0 login --device
```

浏览器授权后重新执行部署命令。
