# Rain API V3 - 番茄小说 API 调用说明

## 基础信息
- **API 地址**: `http://v3.rain.ink/fanqie/`
- **API Key**: `YOUR_API_KEY_HERE` (请使用你自己的API Key)
- **数据源**: 番茄小说

---

## 核心 API 接口

### 1. 搜索书籍
**URL**: `{{baseUrl}}&type=1&keywords={{keyword}}&page={{page}}`

**参数**:
- `type=1` (固定)
- `keywords`: 搜索关键词
- `page`: 页码 (从0开始)

**特殊搜索模式**:
- **AI朗读**: 在关键词前加 `@`，如 `@禁神之下`
- **真人朗读**: 在关键词前加 `!`，如 `!禁神之下`

### 2. 获取书籍详情
**URL**: `{{baseUrl}}&type=2&bookid={{bookId}}`

**参数**:
- `type=2` (固定)
- `bookid`: 书籍ID

### 3. 获取目录章节
**URL**: `{{baseUrl}}&type=3&bookid={{bookId}}`

**参数**:
- `type=3` (固定)
- `bookid`: 书籍ID

### 4. 获取章节内容
**URL**: `{{baseUrl}}&type=4&itemid={{itemId}}`

**参数**:
- `type=4` (固定)
- `itemid`: 章节ID

**AI朗读附加参数**:
- `tone_id`: 音色ID (如 `tone_id=74`)

---

## 功能特性

### 阅读模式
1. **普通阅读模式** (`type=8`)
2. **AI朗读模式** (`type=32`)
   - 支持多种音色选择
   - 自动音色切换功能

### 音色选项
- 成熟大叔升级版 (tone_id=74)
- 成熟大叔 (tone_id=4)
- 甜美少女 (tone_id=0)
- 开朗青年 (tone_id=5)
- 清亮青叔 (tone_id=2)
- 温柔淑女 (tone_id=6)

### 分类浏览
支持男频/女频分类浏览，包含：
- 玄幻、都市、言情、悬疑等多种分类
- 推荐/评分/热门排序
- 连载/完结状态筛选

---

## 数据返回格式

### 书籍信息字段
```json
{
  "book_id": "书籍ID",
  "book_name": "书名",
  "author": "作者",
  "thumb_url": "封面URL",
  "abstract": "简介",
  "word_number": "字数",
  "last_chapter_title": "最新章节",
  "category": "分类",
  "gender": "性别分类",
  "creation_status": "连载状态",
  "score": "评分"
}
```

### 章节信息字段
```json
{
  "item_id": "章节ID",
  "title": "章节标题",
  "volume_name": "卷名",
  "chapter_word_number": "章节字数",
  "first_pass_time": "发布时间戳"
}
```

---

## 使用限制

- **免费用户**: 每天最多阅读200章
- **用途限制**: 仅用于学习交流，禁止倒卖或违法用途
- **音色设置**: 首次使用需设置默认AI朗读音色

---

## 特殊说明

1. **封面图片处理**: 自动转换封面图片URL为高质量版本
2. **登录功能**: 支持番茄账号登录，获取个人书架信息
3. **书架同步**: 登录后可同步云端书架数据
4. **内容缓存**: 支持离线阅读功能

如需完整的技术文档或遇到问题，请参考书源内的详细注释说明。