import json
import os
import urllib.parse
import urllib.request
import mcp.types as types

DEFAULT_API_KEY = "1615a436fe93b8887dc6f856f6161d72"
BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

def get_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="openweather_current",
            description="获取当前天气，支持城市名或经纬度，基于 OpenWeather API。",
            inputSchema={
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "城市名，例如 Beijing 或 Shanghai"},
                    "lat": {"type": "number", "description": "纬度"},
                    "lon": {"type": "number", "description": "经度"},
                    "units": {"type": "string", "enum": ["metric", "imperial", "standard"], "description": "单位：metric/imperial/standard"},
                    "lang": {"type": "string", "description": "语言，例如 zh_cn"},
                    "api_key": {"type": "string", "description": "可选：OpenWeather API Key，不传则使用默认或环境变量"}
                }
            }
        )
    ]

async def handle_call(name: str, arguments: dict | None) -> list[types.TextContent]:
    if name != "openweather_current":
        return []
    if not arguments:
        arguments = {}
    api_key = arguments.get("api_key") or os.getenv("OPENWEATHER_API_KEY") or DEFAULT_API_KEY
    units = arguments.get("units") or "metric"
    lang = arguments.get("lang") or "zh_cn"
    city = arguments.get("city")
    lat = arguments.get("lat")
    lon = arguments.get("lon")
    params = {"appid": api_key, "units": units, "lang": lang}
    if city:
        params["q"] = city
    elif lat is not None and lon is not None:
        params["lat"] = str(lat)
        params["lon"] = str(lon)
    else:
        return [types.TextContent(type="text", text="缺少参数：请提供 city 或同时提供 lat 和 lon")]
    url = f"{BASE_URL}?{urllib.parse.urlencode(params)}"
    try:
        with urllib.request.urlopen(url, timeout=15) as resp:
            data = resp.read().decode("utf-8")
        payload = json.loads(data)
        if isinstance(payload, dict) and payload.get("cod") not in (200, "200", None):
            message = payload.get("message", "未知错误")
            return [types.TextContent(type="text", text=f"请求失败: {message}")]
        name_text = payload.get("name", "")
        weather_list = payload.get("weather") or []
        weather_main = weather_list[0].get("main") if weather_list else ""
        weather_desc = weather_list[0].get("description") if weather_list else ""
        main = payload.get("main") or {}
        temp = main.get("temp")
        feels_like = main.get("feels_like")
        humidity = main.get("humidity")
        wind = payload.get("wind") or {}
        wind_speed = wind.get("speed")
        lines = [
            f"地点: {name_text}" if name_text else "地点: 未知",
            f"天气: {weather_main} {weather_desc}".strip(),
            f"温度: {temp}°" if temp is not None else "温度: 未知",
            f"体感: {feels_like}°" if feels_like is not None else "体感: 未知",
            f"湿度: {humidity}%" if humidity is not None else "湿度: 未知",
            f"风速: {wind_speed} m/s" if wind_speed is not None else "风速: 未知"
        ]
        return [types.TextContent(type="text", text="\n".join(lines))]
    except Exception as e:
        return [types.TextContent(type="text", text=f"请求异常: {str(e)}")]
