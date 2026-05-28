# ================================================================
#  🐶 天气情话推送系统 - Python 脚本
#  你只需要改「配置区」和「manual_messages.json」，其他不要动
# ================================================================

import requests
import json
import os
from datetime import datetime, date

# ================================================================
#  ★ 配 置 区（你改这里 ↓）
# ================================================================

# ---------- 1. API 密钥 ----------
CAIYUN_TOKEN = os.environ.get("CAIYUN_TOKEN", "这里填你的彩云Token")
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "这里填你的DeepSeek Key")

# ---------- 2. 她的位置 ----------
LAT = 28.235193
LON = 112.93142
CITY_NAME = "长沙·岳麓区"

# ---------- 3. 你们的称呼 ----------
YOUR_NAME = "你的宝宝"
HER_NAME_HAPPY = "宝宝"
HER_NAME_NORMAL = "tll"

# ---------- 4. 纪念日 ----------
START_DATE = "2025-10-21"

# ---------- 5. 下次见面日期 ----------
NEXT_MEETING = "2026-06-18"

# ---------- 6. 极端天气阈值 ----------
HIGH_TEMP = 35
LOW_TEMP = 5
WIND_LEVEL = 40

# ================================================================
#  ★ 配 置 区 结 束（你改到这里 ↑）
#  以下不要改
# ================================================================


def get_weather():
    """调用彩云天气API获取实时天气"""
    url = f"https://api.caiyunapp.com/v2.5/{CAIYUN_TOKEN}/{LON},{LAT}/realtime.json"
    try:
        resp = requests.get(url, timeout=10)
        data = resp.json()
    except Exception as e:
        print(f"天气API请求失败: {e}")
        return None
    if data.get("status") != "ok":
        print(f"天气API返回异常: {data}")
        return None
    r = data["result"]["realtime"]
    weather_map = {
        "CLEAR_DAY": "晴☀️", "CLEAR_NIGHT": "晴🌙",
        "PARTLY_CLOUDY_DAY": "多云⛅", "PARTLY_CLOUDY_NIGHT": "多云🌙",
        "CLOUDY": "阴☁️", "RAIN": "雨🌧️", "SNOW": "雪❄️",
        "WIND": "风🌬️", "HAZE": "霾😷"
    }
    skycon = r.get("skycon", "未知")
    weather_cn = weather_map.get(skycon, "未知")
    temp = r.get("temperature", "?")
    humidity = int(r.get("humidity", 0) * 100)
    wind = r.get("wind", {}).get("speed", 0)
    precip = r.get("precipitation", {}).get("local", {})
    precip_intensity = precip.get("intensity", 0)
    precip_status = precip.get("status", "no_rain")
    return {
        "city": CITY_NAME,
        "temperature": temp,
        "weather": weather_cn,
        "humidity": humidity,
        "wind": wind,
        "skycon": skycon,
        "precip_intensity": precip_intensity,
        "precip_status": precip_status
    }


def check_extreme(weather):
    """检查极端天气"""
    extremes = []
    t = weather["temperature"]
    w = weather["wind"]
    s = weather["skycon"]
    if t > HIGH_TEMP:
        extremes.append("高温")
    if t < LOW_TEMP:
        extremes.append("低温")
    if w > WIND_LEVEL:
        extremes.append("大风")
    if s == "RAIN":
        extremes.append("暴雨")
    return extremes


def load_manual_messages():
    """读取手动消息"""
    try:
        with open("manual_messages.json", "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except FileNotFoundError:
        return {}
    except json.JSONDecodeError:
        print("⚠️ manual_messages.json 格式错误，请检查")
        return {}


def build_prompt(weather, extremes, days_together, days_to_meeting):
    """简单自然的 prompt——像真人刚睡醒随手打的"""

    # --- 降水描述 ---
    precip_desc = "无降水"
    if weather.get("precip_status") == "rain" and weather.get("precip_intensity", 0) > 0:
        precip_desc = f"正在下雨（强度{weather['precip_intensity']}mm/h），记得提醒带伞"
    elif weather.get("precip_status") == "snow":
        precip_desc = "正在下雪，记得提醒保暖"

    # --- 天气数据 ---
    weather_info = f"""城市：{weather['city']}
温度：{weather['temperature']}°C
天气：{weather['weather']}
湿度：{weather['humidity']}%
风速：{weather['wind']} km/h
降水：{precip_desc}"""

    # --- 简单 prompt ---
    prompt = f"""你是tll的男朋友，在一起{days_together}天了，异地恋。

你刚睡醒，看了一眼今天她在的城市（{weather['city']}）的天气，准备给她发条早安消息。

## 今天的天气（她那边）
{weather_info}

## 怎么说话
- 叫她"宝宝"或"小宝宝"，这两个词可以自由用
- 经常在结尾说"抱抱"、"亲亲"、"想你"
- 不说"宝贝"、"叔叔"，不油腻，不写小作文
- 像真人刚睡醒随手在手机上打的，简短自然，2-3句话
- 把天气自然地顺带提一下，不要生硬播报
- 这是在提醒她今天的天气，不要反问她"你那边天气怎么样"
- 只有下雨/降雪才提醒带伞，没下雨就别提
- 温度超过34°C才提醒注意防暑，低于34°C不用提
- 风速超过40 km/h才提醒注意防风
- 关于见面倒计时：{f'还有{days_to_meeting}天见面，但只在自然的时候提一句' if days_to_meeting > 0 else '已经见面了'}
- 偶尔提一句"想你了"就行，不用每次长篇大论

直接输出消息内容，不要加引号，不要加前缀。"""

    return prompt


def call_deepseek(prompt):
    """调用 DeepSeek API"""
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个温柔体贴的男朋友，正在给异地恋的女朋友发早安天气问候。你要活泼可爱，不油腻。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.8,
        "max_tokens": 300
    }
    try:
        resp = requests.post(
            "https://api.deepseek.com/chat/completions",
            headers=headers,
            json=data,
            timeout=30
        )
        result = resp.json()
    except Exception as e:
        print(f"DeepSeek API 请求失败: {e}")
        return None
    if "choices" not in result:
        print(f"DeepSeek 返回异常: {result}")
        return None
    return result["choices"][0]["message"]["content"].strip()


def calc_days(start_str):
    """计算天数"""
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    today = date.today()
    return (today - start).days


def main():
    """主函数"""
    print("=" * 50)
    print("  🌤️  天气情话推送系统 v1.0")
    print("=" * 50)
    
    today_str = date.today().strftime("%Y-%m-%d")
    
    days_together = calc_days(START_DATE)
    print(f"\n📅 和tll的第 {days_together} 天")
    
    days_to_meeting = calc_days(NEXT_MEETING)
    if days_to_meeting >= 0:
        print(f"📆 距离下次见面还有 {days_to_meeting} 天")
    else:
        print("📆 已经见面了！记得更新下次见面日期")
        days_to_meeting = 0
    
    # 检查手动消息
    print("\n📖 检查手动消息...")
    manual = load_manual_messages()
    if today_str in manual:
        message = manual[today_str]
        print(f"✅ 今天（{today_str}）有手动消息，跳过 AI 生成")
    else:
        print(f"ℹ️  今天（{today_str}）没有手动消息，使用 AI 生成")
        message = None
    
    # 获取天气
    print("\n🌤️  正在获取天气...")
    weather = get_weather()
    if not weather:
        print("❌ 天气获取失败")
        if message:
            print("\n" + "=" * 50)
            print("  💌 手动消息（天气获取失败，仅推送文字）")
            print("=" * 50)
            print(f"\n{message}\n")
        return
    
    print(f"✅ {weather['city']}  {weather['weather']}  {weather['temperature']}°C  湿度{weather['humidity']}%  风速{weather['wind']} km/h")
    
    extremes = check_extreme(weather)
    if extremes:
        print(f"⚠️  极端天气提醒：{'、'.join(extremes)}")
    else:
        print("✅ 天气正常")
    
    # 有手动消息就直接输出，没有就调 DeepSeek
    if message:
        print("\n" + "=" * 50)
        print("  💌 手动消息（已跳过 DeepSeek）")
        print("=" * 50)
        print(f"\n{message}\n")
    else:
        print("\n🤖 正在构建人格 prompt...")
        prompt = build_prompt(weather, extremes, days_together, days_to_meeting)
        
        print("🤖 正在调用 DeepSeek...")
        message = call_deepseek(prompt)
        
        if not message:
            print("❌ DeepSeek 生成失败")
            return
        
        print("\n" + "=" * 50)
        print("  💌 AI 生成的问候")
        print("=" * 50)
        print(f"\n{message}\n")
    
    print("=" * 50)
    print(f"  🕐 生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

        # ===== 保存到仓库文件 =====
    if message:
        import json as json_module
        output = {
            "date": today_str,
            "city": weather["city"] if weather else CITY_NAME,
            "temperature": str(weather["temperature"]) + "°C" if weather else "?",
            "weather": weather["weather"] if weather else "未知",
            "loveMessage": message,
            "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        with open("latest_weather.json", "w", encoding="utf-8") as f:
            json_module.dump(output, f, ensure_ascii=False, indent=2)
        print("📁 已保存到 latest_weather.json")


    # ===== 推送到云数据库 =====
    if message:
        webhook_url = "https://cloud1-d7gq4qdms5d7dee1a-1430529539.ap-shanghai.app.tcloudbase.com/github_webhook"
        try:
            payload = {
                "type": "weather",
                "data": {
                    "date": today_str,
                    "city": weather["city"] if weather else CITY_NAME,
                    "temperature": str(round(weather["temperature"])) + "°C" if weather else "?",
                    "weather": weather["weather"] if weather else "未知",
                    "loveMessage": message,
                    "updateTime": datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            }
            resp = requests.post(webhook_url, json=payload, timeout=10)
            print(f"📤 推送到云数据库：{'成功' if resp.ok else '失败'} (HTTP {resp.status_code})")
        except Exception as e:
            print(f"📤 推送到云数据库失败：{e}")

if __name__ == "__main__":
    main()
