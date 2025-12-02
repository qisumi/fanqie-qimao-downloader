# FanqieQimaoDownloader - 路线图


## 最新进展（v1.5.1）

- [x] 书架页与书籍卡片移动端布局优化，操作区自适应换行
- [x] 设置页用户列表移动端操作区铺满对齐，日期单独换行
- [x] 首页“今日配额”卡显示剩余额度 + 进度条，移动端对齐
- [x] 一键脚本：前端构建 + 数据库迁移 `scripts/build_frontend_and_migrate.py`

## 待修复/待实现任务

### 高优先级

- [ ] 开发在线阅读器功能

### 中优先级

- [ ] 夜间模式优化
- [ ] 性能优化（大量章节时的内存使用）

### 低优先级

- [ ] 国际化支持 (i18n)
- [ ] 完善错误处理和日志
- [ ] API 文档完善（OpenAPI 注释）

---

## 计划中的功能

### v1.5.1 - 已完成
**界面与移动端**
- [x] 书架页卡片与操作布局的移动端细化
- [x] 设置页用户列表按钮区域移动端优化
- [x] 首页今日配额卡展示剩余额度与进度

### v1.6.0 - 计划中

**阅读器功能**

- [ ] 在线阅读器界面
- [ ] 基于 vue-book-reader 集成
- [ ] 阅读进度同步
- [ ] 书签功能
- [ ] 阅读设置（字体、主题、行距）
- [ ] 章节跳转

### v1.7.0 - 计划中

**书架管理增强**

- [ ] 书籍分类/标签
- [ ] 书籍搜索（本地）
- [ ] 批量操作（删除、导出）
- [ ] 阅读统计
- [ ] 书籍排序（更新时间、添加时间、名称）

### v1.8.0 - 计划中

**自动化功能**

- [ ] 自动更新检测（定时任务）
- [ ] 新章节通知
- [ ] 自动下载新章节
- [ ] Webhook 通知支持

### v2.0.0 - 远期规划

**多平台支持**

- [ ] 更多小说平台支持
- [ ] 插件化平台架构
- [ ] 自定义 API 接入

---

## 贡献指南

欢迎提交 Issue 和 Pull Request！

### 开发环境

```bash
# 克隆仓库
git clone https://github.com/qisumi/fanqie-qimao-downloader.git
cd fanqie-qimao-downloader

# 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/macOS

# 安装依赖
pip install -r requirements.txt

# 运行测试
pytest tests/ -v

# 启动开发服务器
python start.py
```

### 代码规范

- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写单元测试
- 更新文档

### 提交规范

```
feat: 新功能
fix: 修复bug
docs: 文档更新
refactor: 代码重构
test: 测试相关
chore: 构建/工具相关
```
