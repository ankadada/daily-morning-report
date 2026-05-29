# Daily Morning Report — AI Agent 每日早报推送

每日定时推送天气 + 新闻 + AI 建议的早报卡片，支持飞书。

## 特点

- **免 API Key**：新闻用 [60s](https://60s.viki.moe)（免费CDN），天气用 [Open-Meteo](https://open-meteo.com)（免费免鉴权）
- **飞书卡片**：紫色主题，天气三栏 + 新闻列表 + AI 建议 + 每日一句
- **架构清晰**：数据脚本只采集 → Cron agent 生成建议 → 卡片脚本发送

## 快速开始

### 1. 安装依赖

```bash
pip install requests
```

### 2. 测试数据采集

```bash
python scripts/generate_report.py --city 深圳
```

### 3. 配置飞书凭证

```bash
export FEISHU_APP_ID="your_app_id"
export FEISHU_APP_SECRET="your_app_secret"
export FEISHU_CHAT_ID="your_chat_id"
```

### 4. 测试卡片发送

```bash
# dry-run（只输出卡片 JSON）
python scripts/generate_report.py --city 深圳 | python scripts/send_feishu_card.py --stdin --dry-run

# 实际发送
python scripts/generate_report.py --city 深圳 | python scripts/send_feishu_card.py --stdin
```

## 架构

```
generate_report.py          send_feishu_card.py
  (数据采集)                    (卡片发送)
       │                           │
       ▼                           ▼
  60s API + Open-Meteo    →   飞书 Card JSON 2.0
       │                           │
       └───── Cron Agent ──────────┘
           (AI 生成建议)
```

- **generate_report.py**：采集新闻 + 天气，输出 JSON
- **send_feishu_card.py**：读取 JSON（含 suggestions），组装飞书卡片发送
- **Cron Agent**：执行数据脚本 → AI 生成 3 条建议 → 合并 JSON → 调卡片脚本

## Hermes Agent 用户

将整个目录复制到 `~/.hermes/skills/`，然后按 SKILL.md 配置 cron job。

## 自定义城市

```bash
python scripts/generate_report.py --city 北京
```

支持任何 Open-Meteo 覆盖的城市（自动经纬度查询）。

## License

MIT
