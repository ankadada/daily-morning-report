import requests
import argparse
import json
from datetime import datetime


def collect_data(city="深圳"):
    """采集新闻和天气数据，返回结构化 JSON"""
    # 获取新闻
    news_resp = requests.get("https://60s.viki.moe/v2/60s", timeout=10)
    news_data = news_resp.json()["data"]
    daily_quote = news_data.get("tip", "")
    news_list = news_data.get("news", [])

    # 获取天气
    weather_resp = requests.get(
        "https://api.open-meteo.com/v1/forecast"
        "?latitude=22.547&longitude=114.0859"
        "&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
        "&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        "&timezone=Asia/Shanghai&forecast_days=1",
        timeout=10
    )
    weather_data = weather_resp.json()

    weather_code_map = {
        0: "晴", 1: "晴", 2: "多云", 3: "阴",
        45: "雾", 48: "雾凇",
        51: "小雨", 53: "中雨", 55: "大雨", 56: "冻雨", 57: "强冻雨",
        61: "小雨", 63: "中雨", 65: "大雨", 66: "冻雨", 67: "强冻雨",
        71: "小雪", 73: "中雪", 75: "大雪",
        80: "阵雨", 81: "阵雨", 82: "强阵雨",
        95: "雷阵雨", 96: "雷阵雨伴冰雹", 99: "强雷阵雨伴冰雹"
    }
    wind_direction_map = ["北", "东北", "东", "东南", "南", "西南", "西", "西北"]

    current = weather_data["current"]
    daily = weather_data["daily"]
    condition = weather_code_map.get(current["weather_code"], "未知")
    temperature = int(current["temperature_2m"])
    humidity = int(current.get("relative_humidity_2m", 50))
    wind_degree = current["wind_direction_10m"]
    wind_direction = wind_direction_map[int((wind_degree + 22.5) / 45) % 8]
    wind_power = int(current["wind_speed_10m"] / 3.6)
    precipitation = current["precipitation"]
    rain_prob = daily.get("precipitation_probability_max", [0])[0]

    weekday = datetime.now().weekday()
    is_workday = weekday < 5

    return {
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "city": city,
        "weather": {
            "condition": condition,
            "temperature": temperature,
            "humidity": humidity,
            "wind_direction": wind_direction,
            "wind_power": wind_power,
            "precipitation": precipitation,
            "rain_prob": rain_prob,
            "temp_max": int(daily["temperature_2m_max"][0]),
            "temp_min": int(daily["temperature_2m_min"][0])
        },
        "is_workday": is_workday,
        "news": news_list,
        "daily_quote": daily_quote
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="深圳", help="天气查询城市")
    args = parser.parse_args()
    data = collect_data(args.city)
    print(json.dumps(data, ensure_ascii=False, indent=2))
