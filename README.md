# FanqieQimaoDownloader

基于 Rain API V3 的番茄小说和七猫小说下载工具。

## 快速开始

### 1. 配置环境

复制 `.env.example` 文件为 `.env`，并填入你的 API Key：

```bash
cp .env.example .env
```

编辑 `.env` 文件，将 `YOUR_API_KEY_HERE` 替换为你的实际 Rain API Key。

### 2. 获取 API Key

请访问 [Rain API](http://v3.rain.ink) 获取你的 API Key。

**注意**: 请勿将包含真实 API Key 的 `.env` 文件提交到版本控制系统。

## 项目结构

```
FanqieQimaoDownloader/
├── reference/          # API参考文档
│   ├── FANQIE_EXAMPLE.txt
│   ├── FANQIE_RULES.md
│   └── QIMAO_RULES.json
├── .env.example       # 环境变量示例
├── .gitignore         # Git忽略规则
└── 工作计划.md        # 项目计划文档
```

## 参考文档

- `reference/FANQIE_RULES.md` - 番茄小说 API 规则说明
- `reference/FANQIE_EXAMPLE.txt` - API 响应示例
- `reference/QIMAO_RULES.json` - 七猫小说阅读3配置

## 许可证

本项目仅供学习交流使用。
