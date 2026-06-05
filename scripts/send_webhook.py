#!/usr/bin/env python3
"""飞书 Webhook 发送早报卡片

环境变量:
    FEISHU_WEBHOOK_URL  飞书机器人 Webhook 地址

用法:
    python3 send_webhook.py --file /tmp/morning_report.json
    echo '{"date":"..."}' | python3 send_webhook.py --stdin
"""

import json
import os
import sys
import argparse
import requests


def build_card(data: dict) -> dict:
    """组装飞书卡片 JSON 2.0"""
    date_str = data.get("date", "")
    city = data.get("city", "深圳")
    weather = data.get("weather", {})
    news = data.get("news", [])
    suggestions = data.get("suggestions", "")
    daily_quote = data.get("daily_quote", "")
    is_workday = data.get("is_workday", True)

    # 天气信息
    temp = weather.get("temperature", "N/A")
    weather_desc = weather.get("description", "N/A")
    humidity = weather.get("humidity", "N/A")
    wind = weather.get("wind_speed", "N/A")

    # 新闻列表
    news_lines = []
    for i, item in enumerate(news[:8], 1):
        title = item.get("title", "")
        if title:
            news_lines.append(f"**{i}.** {title}")

    news_text = "\n".join(news_lines) if news_lines else "暂无新闻"

    # AI 建议
    suggestions_text = suggestions if suggestions else "保持好心情，加油！"

    # 每日一句
    quote_text = daily_quote if daily_quote else ""

    # 构建卡片
    card = {
        "msg_type": "interactive",
        "card": {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True
            },
            "header": {
                "title": {
                    "tag": "plain_text",
                    "content": f"☀️ 每日早报 - {date_str}"
                },
                "template": "purple"
            },
            "body": {
                "elements": [
                    {
                        "tag": "markdown",
                        "content": f"**📍 {city}** | **🌡️ {temp}°C** | **🌤️ {weather_desc}** | **💧 {humidity}%** | **💨 {wind} km/h**"
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "markdown",
                        "content": f"**📰 今日新闻**\n\n{news_text}"
                    },
                    {
                        "tag": "hr"
                    },
                    {
                        "tag": "markdown",
                        "content": f"**💡 AI 建议**\n\n{suggestions_text}"
                    }
                ]
            }
        }
    }

    # 添加每日一句
    if quote_text:
        card["card"]["body"]["elements"].append({
            "tag": "hr"
        })
        card["card"]["body"]["elements"].append({
            "tag": "markdown",
            "content": f"**📝 每日一句**\n\n{quote_text}"
        })

    return card


def send_webhook(card: dict):
    """通过飞书 Webhook 发送卡片"""
    webhook_url = os.environ.get("FEISHU_WEBHOOK_URL")
    if not webhook_url:
        raise RuntimeError("请设置环境变量 FEISHU_WEBHOOK_URL")

    resp = requests.post(
        webhook_url,
        json=card,
        timeout=10,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") != 0 and result.get("StatusCode") != 0:
        print(f"发送结果: {result}")
    else:
        print("✅ 发送成功")
    return result


def main():
    parser = argparse.ArgumentParser(description="飞书 Webhook 发送早报卡片")
    parser.add_argument("--file", help="JSON 文件路径")
    parser.add_argument("--stdin", action="store_true", help="从 stdin 读取 JSON")
    parser.add_argument("--dry-run", action="store_true", help="只输出卡片 JSON，不发送")
    args = parser.parse_args()

    # 读取数据
    if args.stdin:
        data = json.load(sys.stdin)
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        print("请指定 --file 或 --stdin")
        sys.exit(1)

    # 构建卡片
    card = build_card(data)

    if args.dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
    else:
        send_webhook(card)


if __name__ == "__main__":
    main()
