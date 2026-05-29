---
name: daily-morning-report
description: 通用每日早报推送技能，支持飞书卡片推送，内置国内稳定数据源（60s新闻 + Open-Meteo天气），免鉴权无需API密钥
category: productivity
trigger: 当用户需要配置每日定时早报、定时资讯推送、天气/新闻播报时使用
tags: ["feishu", "daily report", "news", "weather", "automation"]
related_skills: ["hermes-lark-gateway", "cronjob"]
required_commands: []
required_environment_variables: ["FEISHU_APP_ID", "FEISHU_APP_SECRET", "FEISHU_CHAT_ID"]
---

### 功能说明
- 内置对接国内稳定开源数据源：https://60s.viki.moe （免鉴权、全球CDN加速、数据每日更新），JSON格式返回新闻数组+每日一言
- 天气数据源使用稳定的open-meteo免费API，默认深圳天气，支持自定义城市
- **脚本只负责采集数据**（新闻、天气、每日一言），输出结构化JSON，不生成报告
- **cron agent 负责组装报告**：读取JSON数据，根据当天天气AI生成3条实用建议，合并到JSON后调用卡片发送脚本
- **飞书卡片发送**：`scripts/send_feishu_card.py` 调飞书 API 发送 Interactive Card（Card JSON 2.0）

### 架构设计
脚本和 agent 分工：
- **数据脚本** (`scripts/generate_report.py`)：只负责采集数据，输出 JSON（天气、新闻、每日一言）
- **卡片脚本** (`scripts/send_feishu_card.py`)：接收 JSON 数据（含 suggestions），组装飞书卡片并发送
- **Cron agent**：执行数据脚本 → AI 生成 3 条实用建议 → 合并到 JSON → 调用卡片脚本发送

deliver 必须设为 `local`（卡片由脚本直接调飞书 API 发送，不需要 Hermes 再发一条文本）。

### 环境变量

| 变量 | 说明 |
|------|------|
| `FEISHU_APP_ID` | 飞书应用 App ID |
| `FEISHU_APP_SECRET` | 飞书应用 App Secret |
| `FEISHU_CHAT_ID` | 目标群聊 ID（可选，也可用 --chat-id 参数） |

### 飞书卡片发送（send_feishu_card.py）
```bash
# 从文件发送
python scripts/send_feishu_card.py --file /tmp/morning_report.json

# 从 stdin 发送
python scripts/generate_report.py | python scripts/send_feishu_card.py --stdin

# dry-run 只输出卡片 JSON 不发送
python scripts/send_feishu_card.py --file /tmp/morning_report.json --dry-run
```

输入 JSON 格式：
```json
{
  "date": "2026年05月05日",
  "city": "深圳",
  "weather": {"condition": "阴", "temperature": 21, "humidity": 90, ...},
  "news": ["新闻1", "新闻2", ...],
  "suggestions": "建议1\n建议2\n建议3",
  "daily_quote": "每日一句",
  "is_workday": true
}
```

### Cron Job Prompt 模板
```
你是每日早报生成助手。按以下步骤执行：

1. 获取数据：
   python scripts/generate_report.py --city 深圳

2. 解析 JSON 数据，基于天气和新闻生成 3 条简洁实用的中文建议（每条 15-25 字，带 emoji）

3. 用 execute_code 合并数据并发送卡片：
   data["suggestions"] = "建议1\n建议2\n建议3"
   写入 /tmp/morning_report.json，然后执行：
   python scripts/send_feishu_card.py --file /tmp/morning_report.json

4. 确认卡片发送成功即可（deliver=local 不会额外发文本）
```

### 数据源
- **60s 新闻 API**：`https://60s.viki.moe/v2/60s` — JSON 格式，返回新闻列表、每日一言、农历等
- **Open-Meteo 天气 API**：`https://api.open-meteo.com/v1/forecast` — 免费免鉴权，返回当前天气 + 预报

### 卡片布局
紫色 header（日期+城市+天气）→ 三栏天气区（居中对齐）→ 新闻列表 → AI建议 → 每日一句
