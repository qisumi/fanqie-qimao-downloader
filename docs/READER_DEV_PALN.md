# 在线阅读组件开发计划

## 目标与范围
- 为 v1.6.0 引入在线阅读能力，支持分章 TXT 与 EPUB；保持架构可拓展以便后续新增格式（mobi/pdf 等）。
- 以“少造轮子”为原则，优先选用成熟组件完成排版、翻页和 EPUB 渲染；前后端解耦，阅读器以 API/文件流获取内容。

## 必备功能（MVP）
- 字体/字号/行距/段间距可调，设置持久化（localStorage + 服务端用户进度记录）。
- 背景主题预置：米黄纸、护眼绿、夜间灰黑，并允许自定义颜色。
- 格式：分章 TXT（现有章节存储）与 EPUB（直接渲染/按需生成）；留接口以扩展更多格式。
- 目录与章节跳转，支持定位到上次阅读进度。
- 阅读模式：左右翻页（平移/覆盖效果）与上下连续滚动可切换。

## 建议增强功能
- 进度同步：按用户 + 设备存储当前章节与偏移量，前端可在无认证时回落到本地存储。
- 书签与批注：章节级书签（附简短备注），后续可扩展段落高亮与笔记列表。
- 章节内搜索：分章 TXT 先做章节内简单搜索（逐章扫描），EPUB 利用 `epubjs` 的 spine 文本。
- 朗读/TTS：调用浏览器 Speech Synthesis，提供朗读、倍速、播放控制。
- 离线/弱网体验：当前章节与相邻章节预取，结合现有 PWA 缓存策略缓存阅读资源与字体。
- 阅读统计：阅读时长、天/周阅读量、连续阅读天数（前端计时 + 后端上报）。
- PWA 缓存可视化：在阅读器 UI 中显示“已缓存章节/EPUB”状态，允许一键缓存/清除指定书籍的 EPUB 与最近 N 章。

## 依赖选型
- 前端
  - `epubjs`：成熟的 EPUB 渲染库，支持分页/滚动两种流式排版，可直接加载本地/URL EPUB。
  - `@egjs/vue3-flicking`：实现左右翻页动画（slide/coverflow），支持手势/鼠标滚轮并能与自定义渲染区组合。
  - `@vueuse/core`：使用 `useStorage`/`useMediaQuery`/`useFullscreen` 等简化设置持久化、系统主题跟随与全屏切换。
  - 字体（可选）：`@fontsource/noto-serif-sc`、`@fontsource/noto-sans-sc`、`@fontsource/lxgw-wenkai` 提供衬线/无衬线/楷体三套常用中文字体。
- 后端
  - 暂无新增依赖，复用 `StorageService`/`BookService` 读取章节文本、生成/读取 EPUB。

## 架构与实现思路
- 数据流
  - 目录/基础信息：复用现有 `/api/books/{id}` 返回的章节元数据；新增“阅读态”轻量接口避免一次性传输大文本（仅 id/index/title/word_count）。
  - 章节内容：新增 `/api/books/{id}/chapters/{chapter_id}/content?format=html|text`，后端从磁盘读取已下载章节并输出 HTML（带段落/空行标记），可选 `range=prev|next` 获取相邻；若章节尚未下载，则同步触发后台下载该章并可选预取后续 N 章（返回时带状态标记）。
  - EPUB：复用 `/api/books/{id}/epub` 生成/返回文件；前端使用 `epubjs` 以 URL（流式下载）或 Blob 渲染；必要时先检查生成状态再拉取。
- 阅读器前端视图
  - 新路由 `reader/:bookId`，包含组件：`ReaderViewport`（渲染区，封装 epubjs/文本两套渲染器）、`ReaderToolbar`（顶部/底部工具栏，含模式切换/字体/背景/朗读/全屏）、`SettingsDrawer`（字体/背景/行距等）、`TocDrawer`（目录）、`ProgressBar`（章节进度/滑块）。
  - Pinia `readerStore`：状态字段建议 `bookMeta`/`toc`/`currentChapterId`/`currentOffset`/`mode`(scroll|page)/`settings`/`bookmarks`/`epubHandle`/`loading`/`error`；与 `bookStore` 解耦，通过 API 拉取数据。
- 阅读模式
  - 连续滚动：原生滚动 + 段落样式控制（行距/段间距/首行缩进）。章节切换时保持滚动位置同步到 `offset`（像素或百分比）。
  - 翻页：`@egjs/vue3-flicking` 包裹章节分页或 `epubjs` pagination；TXT 以“单章一个面板 + 相邻章节预加载”的方式，翻页触发时加载下一章节并追加到面板队列，保持最多 3-5 面板。
- 设置与主题
  - 设置对象：`fontFamily`/`fontSize`/`lineHeight`/`paragraphSpacing`/`background`/`textColor`/`readingMode`/`pageTransition`（flicking 的 `circular=false`，自定义 `panelEffect` 可选）。
  - 本地持久化（`useStorage`），首次加载根据系统深色模式选择主题；夜间主题与 `themeStore` 同步，防止重复覆盖。
- 进度/书签同步
  - 后端新增 `GET/POST /api/books/{id}/reader/progress`（入参：章节 id + 百分比 + 段落偏移 + 设备标识）；`/api/books/{id}/reader/bookmarks` CRUD。前端在章节切换、退出、定时（例如 10s）触发上报。
  - 未登录/无用户态时只落本地；有用户/私人书架时同步到后端并覆盖本地。
- 性能与离线
  - 章节按需加载 + 相邻预取（上一/下一章）；长章节滚动模式下使用懒加载图片/插图（若存在）；EPUB 以 spine 预取相邻章节。
  - 在线补全：当请求的章节未下载时，后端触发下载该章并异步预取后续 N 章，前端收到 “fetching” 状态可显示加载占位。
  - PWA 缓存：将“当前书籍目录 + 最近 N 章文本/EPUB + 字体”加入运行时缓存；离线回退提示（沿用现有 offline.html）；提供“缓存 EPUB”按钮触发下载并写入缓存。

## API 与数据结构规划
- `GET /api/books/{book_id}/toc`：返回 `{book_id, chapters:[{id, index, title, word_count, updated_at}]}`；若未下载完成可附加 `download_status`。
- `GET /api/books/{book_id}/chapters/{chapter_id}/content`：返回 `{title, index, prev_id, next_id, content_html, content_text, word_count, updated_at, status}`；`format=html|text` 选择字段；`range=prev|next` 可直接获取相邻章节；`status` 可为 `ready`/`fetching`（正在后台下载）。
- `GET /api/books/{book_id}/reader/progress`：返回 `{chapter_id, offset_px, percent, device_id, updated_at}`（若无则为空对象）。
- `POST /api/books/{book_id}/reader/progress`：入参 `{chapter_id, offset_px, percent, device_id}`；幂等覆盖同一 `(book_id,user,device_id)` 记录。
- `GET /api/books/{book_id}/reader/bookmarks`：列表 `{id, chapter_id, offset_px, percent, note, created_at}`。
- `POST /api/books/{book_id}/reader/bookmarks`：入参 `{chapter_id, offset_px, percent, note}`，返回创建后的列表。
- `DELETE /api/books/{book_id}/reader/bookmarks/{bookmark_id}`：删除。
- `GET /api/books/{book_id}/reader/history`：返回阅读历史列表 `{chapter_id, percent, device_id, updated_at}`（按时间倒序，限定最近 N 条）。
- `DELETE /api/books/{book_id}/reader/history`：清空该书阅读历史；`DELETE /api/books/{book_id}/reader/progress`：清空进度（重置为首章）。
- `POST /api/books/{book_id}/cache/epub`：生成/下载 EPUB 并标记为缓存（前端将响应 Blob 写入 Cache Storage）；`GET /api/books/{book_id}/cache/status`：返回 `{epub_cached: bool, cached_chapters: [chapter_id], cached_at}`。
- 数据落库：
  - `reading_progress` 表：`id` PK、`book_id` FK、`user_id`（可空代表公共）、`chapter_id`（chapter 表 FK）、`offset_px`、`percent`、`device_id`、`updated_at`；唯一索引 `(book_id, user_id, device_id)`。
  - `bookmarks` 表：`id` PK、`book_id` FK、`user_id`（可空）、`chapter_id` FK、`offset_px`、`percent`、`note`、`created_at`。
  - `reading_history` 表：`id` PK、`book_id` FK、`user_id`（可空）、`chapter_id` FK、`percent`、`device_id`、`updated_at`（仅追加，不幂等）；用于展示最近阅读记录。可建索引 `(book_id, user_id, updated_at desc)`。
  - 迁移：Alembic 脚本添加表 + 外键；现有模型目录下新增 ORM 模型与 Pydantic schema。

## 实施步骤与时间预估（工作日）
| 阶段 | 交付物 | 预估 |
| --- | --- | --- |
| 1. 交互草图与需求确认 | 低保真原型、设置项确定、API 协议确定 | 0.5d |
| 2. 后端接口 | 章节内容读取、进度/书签接口、数据模型与迁移 | 1.0d |
| 3. 前端数据层 | `readerStore`、API 封装、设置持久化、书架/用户上下文衔接 | 0.5d |
| 4. 阅读器骨架 | 路由、目录抽屉、工具栏、进度条，串联 TXT 渲染（滚动模式 MVP） | 1.0d |
| 5. 阅读模式与 EPUB | `@egjs/vue3-flicking` 翻页模式、EPUB 渲染接入、模式切换与状态保持 | 1.0d |
| 6. 个性化与主题 | 字体/字号/行距/段间距/背景主题设置，夜间适配与全屏 | 0.5d |
| 7. 增强功能 | 书签、进度同步、章节内搜索、预取/离线缓存、朗读开关 | 1.0d |
| 8. 测试与优化 | 冒烟 + e2e 场景、长章节性能测试、移动端适配、无网/弱网验证 | 0.5d |
| **合计** | -- | **6.0d** |

## 前端实现指引（细化）
- 路由与布局：`/reader/:bookId` 懒加载页面，顶部/底部工具栏保持简洁；移动端底部浮层呈现核心按钮（目录、设置、朗读、模式切换、亮度/背景）。
- Store 交互：
  - 初始化：拉取 TOC -> 根据进度确定 `currentChapterId` -> 拉章节内容 -> 渲染模式（文本/EPUB）。
  - 切章：更新 `currentChapterId`，预取相邻章节，触发 `saveProgress()`（节流）。
  - 设置：`useStorage` 双向绑定到 `readerStore.settings`；变化时更新 CSS 变量或传给 `epubjs` 的 themes。
- 书签：存本地列表并同步接口；删除操作立即本地移除，后端失败再回滚。
  - 缓存状态：`readerStore.cacheState` 维护 `epub_cached`、`cached_chapters`、`last_cached_at`；启动时调用 `/cache/status`，点击“缓存 EPUB”按钮时调用 `/cache/epub` 后将 Blob 写入 `caches.open('reader-cache')` 并更新状态。
  - 在线补全：收到章节内容的 `status=fetching` 时展示骨架屏并轮询/订阅进度（可复用 tasks WebSocket 或轮询章节内容）；章节加载成功后自动替换内容并预取后续章节。
- 渲染
  - TXT：将 content_text 按段落 split，生成 `<p>`，应用动态样式（字体/字号/行距/段间距/首行缩进）。滚动模式使用原生滚动；翻页模式用 Flicking，每个 panel 包含一章内容（或分页片段）。
  - EPUB：`epubjs` 创建 `Book`，使用 `rendition.display(targetCfi)`；用 `rendition.on('relocated')` 获取 CFI -> 更新进度，配合 Flicking 仅用于 TXT。
  - 夜间/主题：通过根节点 class 或 CSS 变量切换背景/文字颜色；确保与 Naive UI 主题不冲突。
- 朗读：基于 `window.speechSynthesis`，传入当前章节文本；提供开始/暂停/继续/停止，支持语速调节。
- 错误/弱网：加载失败时重试按钮；无网络时提示离线并展示已缓存章节。

## 后端实现指引（细化）
- 新路由文件建议放在 `app/web/routes/books_reader.py`，聚合 TOC/内容/进度/书签；在聚合 books router 中注册。
- 内容读取：复用 `StorageService` 读取章节文件；按行包裹 `<p>`，保留空行；若不存在章节则调用 `DownloadService` 拉取该章并可选预取后续 N 章（入参 `prefetch=3`），立即返回 `status=fetching`，后台完成后再次访问可返回内容。
- 进度/书签/历史模型：在 `app/models/` 添加 ORM；`app/schemas/` 中添加 Request/Response Pydantic；在 `services` 中添加 `ReaderService`（或在 `BookService` 扩展阅读相关方法）封装读写与清空。
- 权限与用户：若现有用户体系基于 Cookie/用户名，进度/书签接口需读取当前用户标识；未登录则允许匿名（user_id=None）。
- Alembic：生成迁移，确保索引 `(book_id, user_id, device_id)` 唯一，外键指向 `books` 与 `chapters`。
- 性能：内容接口按需返回单章；避免一次性加载全部章节；可加入简单缓存（如 LRU）存放最近访问章节文本。

## 验收与测试要点
- 功能：在移动/桌面端均可切换滚动/翻页，目录跳转准确，重新打开恢复到上次进度。
- 设置：字体/行距/段间距/背景即时生效且持久化；主题与现有暗色模式不冲突。
- 性能：10w 字章节滚动流畅，翻页模式无明显白屏；预取成功减少章节切换等待。
- 同步：有用户时跨设备进度/书签保持一致；无用户时本地存储独立且可覆盖。
- EPUB：能加载生成的 EPUB，目录与分页正常；TXT/EPUB 双模式切换无异常。

## 逐步工作进度追踪（建议执行顺序，未开始请标记为 [ ]）
- [ ] 后端接口落地：在 `app/web/routes/books_reader.py` 完成 TOC/内容/进度/书签/历史/缓存/在线补全接口，并补充 Pydantic schema 与汇总注册。
- [ ] 数据表迁移：编写 Alembic 迁移创建 `reading_progress`、`bookmarks`、`reading_history`，添加唯一索引 `(book_id,user_id,device_id)` 等。
- [ ] 下载服务适配：在 `DownloadService` 增加“按章节单拉 + 预取后续 N 章”方法，章节内容接口未命中时调用，返回 `status=fetching`。
- [ ] 前端依赖与骨架：`frontend/package.json` 新增 `@egjs/vue3-flicking`，创建 `/reader/:bookId` 页面骨架与 `readerStore`（含 cacheState/online-fetching 状态）。
- [ ] 缓存与 PWA 按钮：实现“缓存 EPUB”按钮逻辑（调用 `/cache/epub`，写入 Cache Storage），UI 显示缓存状态与清除入口。
- [ ] 进度/历史同步：前端在章节切换/定时上报进度，提供“清空进度/清空历史”按钮调用 DELETE 接口；后端按用户区分并允许匿名。
- [ ] 测试与验证：接口层单测（未下载章 -> fetching -> ready）、前端冒烟测试滚动/翻页/离线缓存路径，弱网/无网回退验证。
