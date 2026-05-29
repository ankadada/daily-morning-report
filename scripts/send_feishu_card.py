#!/usr/bin/env python3
"""飞书早报卡片发送脚本

环境变量:
    FEISHU_APP_ID      飞书应用 App ID
    FEISHU_APP_SECRET  飞书应用 App Secret
    FEISHU_CHAT_ID     目标群聊 ID（可选，也可用 --chat-id 参数）

用法:
    python3 send_feishu_card.py --file /tmp/morning_report.json
    echo '{"date":"..."}' | python3 send_feishu_card.py --stdin
    python3 send_feishu_card.py --file report.json --dry-run
"""

import json
import os
import sys
import argparse
import requests


def get_tenant_token():
    """获取飞书 tenant_access_token"""
    app_id = os.environ.get("FEISHU_APP_ID")
    app_secret = os.environ.get("FEISHU_APP_SECRET")
    if not app_id or not app_secret:
        raise RuntimeError("请设置环境变量 FEISHU_APP_ID 和 FEISHU_APP_SECRET")

    resp = requests.post(
        "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
        json={"app_id": app_id, "app_secret": app_secret},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"获取 token 失败: {data}")
    return data["tenant_access_token"]


def build_card(data: dict) -> dict:
    """组装飞书卡片 JSON 2.0"""
    date_str = data.get("date", "")
    city = data.get("city", "深圳")
    weather = data.get("weather", {})
    news = data.get("news", [])
    suggestions = data.get("suggestions", "")
    daily_quote = data.get("daily_quote", "")
    is_workday = data.get("is_workday", True)

    # 天气字段
    condition = weather.get("condition", "未知")
    temp = weather.get("temperature", "--")
    humidity = weather.get("humidity", "--")
    wind_dir = weather.get("wind_direction", "")
    wind_power = weather.get("wind_power", "--")
    rain_prob = weather.get("rain_prob", 0)
    temp_max = weather.get("temp_max", "--")
    temp_min = weather.get("temp_min", "--")

    # 天气 emoji
    weather_emoji_map = {
        "晴": "☀️", "多云": "⛅", "阴": "☁️",
        "小雨": "🌧️", "中雨": "🌧️", "大雨": "🌧️",
        "阵雨": "🌦️", "雷阵雨": "⛈️",
        "小雪": "🌨️", "中雪": "🌨️", "大雪": "❄️",
        "雾": "🌫️", "雾凇": "🌫️",
    }
    w_emoji = weather_emoji_map.get(condition, "🌤️")

    # 工作日/休息日
    day_type = "工作日" if is_workday else "休息日"
    day_emoji = "💼" if is_workday else "🎉"

    # 新闻列表
    news_lines = []
    for i, item in enumerate(news[:12], 1):
        news_lines.append(f"**{i}.** {item}")
    news_text = "\n".join(news_lines) if news_lines else "暂无新闻"

    # 组装卡片
    elements = []

    # 天气区域 - 三栏布局
    elements.append({
        "tag": "column_set",
        "flex_mode": "stretch",
        "background_style": "grey",
        "columns": [
            {
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "vertical_align": "top",
                "elements": [
                    {
                        "tag": "markdown",
                        "content": f"**{w_emoji} {condition}**\n**{temp}℃**\n最高 {temp_max}℃ / 最低 {temp_min}℃",
                        "text_align": "center"
                    }
                ]
            },
            {
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "vertical_align": "top",
                "elements": [
                    {
                        "tag": "markdown",
                        "content": f"💧 湿度 **{humidity}%**\n🌬️ {wind_dir}风 **{wind_power}级**",
                        "text_align": "center"
                    }
                ]
            },
            {
                "tag": "column",
                "width": "weighted",
                "weight": 1,
                "vertical_align": "top",
                "elements": [
                    {
                        "tag": "markdown",
                        "content": f"☔ 降水概率\n**{rain_prob}%**\n{day_emoji} {day_type}",
                        "text_align": "center"
                    }
                ]
            }
        ]
    })

    elements.append({"tag": "hr"})
    elements.append({"tag": "markdown", "content": "📰 **今日要闻**"})
    elements.append({"tag": "markdown", "content": news_text})
    elements.append({"tag": "hr"})

    if suggestions:
        elements.append({
            "tag": "markdown",
            "content": f"💡 **今日建议**\n{suggestions}"
        })
        elements.append({"tag": "hr"})

    if daily_quote:
        elements.append({
            "tag": "markdown",
            "content": f"✨ *{daily_quote}*"
        })

    card = {
        "schema": "2.0",
        "config": {"wide_screen_mode": True},
        "header": {
            "title": {"tag": "plain_text", "content": f"🌅 今日早报 | {date_str} {city}"},
            "subtitle": {"tag": "plain_text", "content": f"{w_emoji} {condition} {temp}℃"},
            "template": "purple"
        },
        "body": {"elements": elements}
    }

    return card


def send_card(token: str, card: dict, chat_id: str):
    """发送卡片消息到飞书群"""
    resp = requests.post(
        "https://open.feishu.cn/open-apis/im/v1/messages",
        params={"receive_id_type": "chat_id"},
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json; charset=utf-8",
        },
        json={
            "receive_id": chat_id,
            "msg_type": "interactive",
            "content": json.dumps(card, ensure_ascii=False),
        },
        timeout=15,
    )
    resp.raise_for_status()
    result = resp.json()
    if result.get("code") != 0:
        raise RuntimeError(f"发送卡片失败: {result}")
    return result


def main():
    parser = argparse.ArgumentParser(description="发送飞书早报卡片")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--data", help="JSON 字符串")
    group.add_argument("--file", help="JSON 文件路径")
    group.add_argument("--stdin", action="store_true", help="从 stdin 读取 JSON")
    parser.add_argument("--chat-id", default=None, help="目标群 ID（默认用 FEISHU_CHAT_ID 环境变量）")
    parser.add_argument("--dry-run", action="store_true", help="只输出卡片 JSON，不发送")
    args = parser.parse_args()

    chat_id = args.chat_id or os.environ.get("FEISHU_CHAT_ID")
    if not chat_id and not args.dry_run:
        raise RuntimeError("请设置 FEISHU_CHAT_ID 环境变量或使用 --chat-id 参数")

    # 读取数据
    if args.data:
        data = json.loads(args.data)
    elif args.file:
        with open(args.file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = json.load(sys.stdin)

    # 组装卡片
    card = build_card(data)

    if args.dry_run:
        print(json.dumps(card, ensure_ascii=False, indent=2))
        return

    # 发送
    token = get_tenant_token()
    result = send_card(token, card, chat_id)
    msg_id = result.get("data", {}).get("message_id", "unknown")
    print(f"✅ 卡片发送成功 message_id={msg_id}")


if __name__ == "__main__":
    main()
