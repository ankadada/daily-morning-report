import requests
import argparse
import json
from datetime import datetime


# 城市经纬度映射
CITY_COORDS = {
    "深圳": (22.547, 114.0859),
    "北京": (39.9042, 116.4074),
    "上海": (31.2304, 121.4737),
    "广州": (23.1291, 113.2644),
    "杭州": (30.2741, 120.1551),
    "成都": (30.5728, 104.0668),
    "武汉": (30.5928, 114.3055),
    "西安": (34.3416, 108.9398),
    "南京": (32.0603, 118.7969),
    "重庆": (29.4316, 106.9123),
    "长沙": (28.2282, 112.9388),
    "郑州": (34.7466, 113.6253),
    "天津": (39.3434, 117.3616),
    "苏州": (31.2990, 120.5853),
    "东莞": (23.0208, 113.7518),
    "佛山": (23.0218, 113.1218),
    "厦门": (24.4798, 118.0894),
    "青岛": (36.0671, 120.3826),
    "大连": (38.9140, 121.6147),
    "宁波": (29.8683, 121.5440),
    "昆明": (25.0389, 102.7183),
    "福州": (26.0745, 119.2965),
    "济南": (36.6512, 116.9970),
    "合肥": (31.8206, 117.2272),
    "哈尔滨": (45.8038, 126.5340),
    "长春": (43.8171, 125.3235),
    "沈阳": (41.8057, 123.4315),
    "贵阳": (26.6470, 106.6302),
    "南宁": (22.8170, 108.3665),
    "太原": (37.8706, 112.5489),
    "石家庄": (38.0428, 114.5149),
    "乌鲁木齐": (43.8256, 87.6168),
    "拉萨": (29.6500, 91.1000),
    "兰州": (36.0611, 103.8343),
    "呼和浩特": (40.8424, 111.7490),
    "海口": (20.0174, 110.3492),
    "银川": (38.4872, 106.2309),
    "西宁": (36.6171, 101.7782),
    "珠海": (22.2710, 113.5767),
    "无锡": (31.4912, 120.3119),
    "温州": (28.0000, 120.6700),
    "常州": (31.8107, 119.9740),
    "烟台": (37.4639, 121.4479),
    "徐州": (34.2610, 117.1941),
}


def get_weather(lat, lon, city):
    """获取天气数据"""
    weather_resp = requests.get(
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={lat}&longitude={lon}"
        f"&current=temperature_2m,relative_humidity_2m,precipitation,weather_code,wind_speed_10m,wind_direction_10m"
        f"&daily=temperature_2m_max,temperature_2m_min,precipitation_probability_max"
        f"&timezone=Asia/Shanghai&forecast_days=1",
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

    return {
        "city": city,
        "condition": condition,
        "temperature": temperature,
        "humidity": humidity,
        "wind_direction": wind_direction,
        "wind_power": wind_power,
        "precipitation": precipitation,
        "rain_prob": rain_prob,
        "temp_max": int(daily["temperature_2m_max"][0]),
        "temp_min": int(daily["temperature_2m_min"][0])
    }


def collect_data(cities=None):
    """采集新闻和天气数据，返回结构化 JSON"""
    if cities is None:
        cities = ["深圳"]

    # 获取新闻
    news_resp = requests.get("https://60s.viki.moe/v2/60s", timeout=10)
    news_data = news_resp.json()["data"]
    daily_quote = news_data.get("tip", "")
    news_list = news_data.get("news", [])

    # 获取各城市天气
    weathers = []
    for city in cities:
        if city in CITY_COORDS:
            lat, lon = CITY_COORDS[city]
        else:
            # 默认使用深圳坐标
            lat, lon = CITY_COORDS["深圳"]
        try:
            weather = get_weather(lat, lon, city)
            weathers.append(weather)
        except Exception as e:
            weathers.append({"city": city, "error": str(e)})

    weekday = datetime.now().weekday()
    is_workday = weekday < 5

    return {
        "date": datetime.now().strftime("%Y年%m月%d日"),
        "cities": cities,
        "weathers": weathers,
        "is_workday": is_workday,
        "news": news_list,
        "daily_quote": daily_quote
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--city", default="深圳", help="天气查询城市，多个城市用逗号分隔")
    args = parser.parse_args()
    cities = [c.strip() for c in args.city.split(",")]
    data = collect_data(cities)
    print(json.dumps(data, ensure_ascii=False, indent=2))
