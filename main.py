import math
import random
import requests

from datetime import date, datetime
from wechatpy import WeChatClient
from wechatpy.client.api import WeChatMessage, WeChatTemplate

today = datetime.now()

# ================= 配置区：直接写死在代码里 =================
# 按需修改下面这些变量，改完后直接运行 main.py 即可，无需再配置环境变量

# 微信公众测试号 ID 和 SECRET
app_id = "wx1bfe24456f42265e"  # TODO: 换成你自己的 APP_ID
app_secret = "69ee78c956fb65a66a14dd7dc46ce4d0"  # TODO: 换成你自己的 APP_SECRET

# 接收消息的用户 openid，可以配置多个
user_ids = [
    # "onAX62HScnqzOaZ_0pgRonNOYELc",  # TODO: 换成你自己的用户 openid
    "gh_55e2bbccc684",  # TODO: 换成你自己的用户 openid
]

# 对应的模板 ID，可以配置多个，与 user_ids 一一对应
template_ids = [
    "3973oHlYC7Z1T3aylYk1CtYAA-EK3NZDNmj-jGwJIwQ",  # TODO: 换成你自己的模板 ID
]

# 城市列表（与 user_ids 一一对应），例如 ["北京"] 或 ["北京", "上海"]
citys = ["北京"]

# 发工资日（字符串），例如 ["10"] 表示每月 10 号
solarys = ["10"]

# 纪念日开始日期（YYYY-MM-DD），例如 ["2020-01-01"]
start_dates = ["2020-01-01"]

# 生日（MM-DD），例如 ["08-08"]
birthdays = ["08-08"]
# ==========================================================


# 获取天气和温度
def get_weather(city):
    url = (
        "http://autodev.openspeech.cn/csp/api/v2.1/weather"
        "?openId=aiuicus&clientType=android&sign=android&city=" + city
    )
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
    except Exception as e:
        # 接口请求失败时，返回默认文案，避免程序直接报错退出
        print(f"获取天气接口异常：{e}")
        return "接口异常", 0

    try:
        weather = data["data"]["list"][0]
        weather_text = weather.get("weather", "未知")
        temp_raw = weather.get("temp", 0)
        try:
            temp_value = float(temp_raw)
        except (TypeError, ValueError):
            temp_value = 0
        return weather_text, math.floor(temp_value)
    except (KeyError, IndexError, TypeError) as e:
        # 数据格式不符合预期时，给出兜底
        print(f"解析天气数据失败：{e}，原始响应：{data}")
        return "数据错误", 0


# 当前城市、日期
def get_city_date(city):
    return city, today.date().strftime("%Y-%m-%d")


# 距离设置的日期过了多少天
def get_count(start_date):
    """
    计算从纪念日到今天已经过去多少天。
    start_date: 字符串日期，格式 YYYY-MM-DD
    """
    try:
        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
    except (TypeError, ValueError):
        print(f"纪念日日期格式错误：{start_date}，返回 0 天")
        return 0
    delta = today - start_dt
    # 理论上不会为负，这里兜底一下
    return max(0, delta.days)


# 距离发工资还有多少天
def get_solary(solary):
    """
    计算距离下一个发工资日还有多少天。
    solary: 字符串形式的发薪日（1-31），例如 "10"
    """
    try:
        day = int(solary)
    except (TypeError, ValueError):
        print(f"发工资日格式错误：{solary}，默认使用 1 号")
        day = 1

    # 为了简单起见，将 day 限制在 1-28，避免 30/31 在小月报错
    day = max(1, min(day, 28))

    today_date = date.today()
    year = today_date.year
    month = today_date.month

    # 本月的发薪日
    next_pay = datetime(year, month, day)

    # 如果本月发薪日已经过去，则顺延到下个月
    if next_pay < datetime.now():
        if month == 12:
            year += 1
            month = 1
        else:
            month += 1
        next_pay = datetime(year, month, day)

    return (next_pay - today).days


# 距离过生日还有多少天
def get_birthday(birthday):
    """
    计算距离下一个生日还有多少天。
    birthday: 字符串日期，格式 MM-DD，例如 "08-08"
    """
    try:
        next_bd = datetime.strptime(f"{date.today().year}-{birthday}", "%Y-%m-%d")
    except (TypeError, ValueError):
        print(f"生日日期格式错误：{birthday}，返回 0 天")
        return 0
    if next_bd < datetime.now():
        next_bd = next_bd.replace(year=next_bd.year + 1)
    return (next_bd - today).days


# 每日一句
def get_words():
    """
    从第三方接口获取一句话文案。
    接口异常或数据结构不符合预期时，返回默认文案，避免递归死循环。
    """
    url = "https://api.shadiao.pro/chp"
    try:
        res = requests.get(url, timeout=5)
        res.raise_for_status()
        data = res.json()
        text = data.get("data", {}).get("text")
        if not text:
            raise KeyError("缺少 data.text 字段")
        return text
    except Exception as e:
        print(f"获取每日一句失败：{e}")
        return "愿你今天也有好心情～"


# 字体随机颜色
def get_random_color():
    return "#%06x" % random.randint(0, 0xFFFFFF)


try:
    client = WeChatClient(app_id, app_secret)
    wm = WeChatMessage(client)
except Exception as e:
    print(f"初始化 WeChatClient 失败，请检查 APP_ID/APP_SECRET 是否正确：{e}")
    raise SystemExit(1)

# 防止列表长度不一致导致下标越界，只取最短的一组配置
lengths = [
    len(user_ids),
    len(template_ids),
    len(citys),
    len(solarys),
    len(start_dates),
    len(birthdays),
]
count = min(lengths) if lengths else 0

if count == 0:
    print("未配置任何用户/模板信息，程序结束。")
else:
    if len(set(lengths)) != 1:
        print(f"警告：配置列表长度不一致，仅使用前 {count} 条配置。")

    for i in range(count):
        wea, tem = get_weather(citys[i])
        cit, dat = get_city_date(citys[i])
        love_days = get_count(start_dates[i])
        birthday_left = get_birthday(birthdays[i])
        solary_left = get_solary(solarys[i])

        data = {
            "date": {"value": f"今日日期：{dat}", "color": get_random_color()},
            "city": {"value": f"当前城市：{cit}", "color": get_random_color()},
            "weather": {"value": f"今日天气：{wea}", "color": get_random_color()},
            "temperature": {
                "value": f"当前温度：{tem}",
                "color": get_random_color(),
            },
            "love_days": {
                "value": f"今天是你们在一起的第{love_days}天",
                "color": get_random_color(),
            },
            "birthday_left": {
                "value": f"距离她的生日还有{birthday_left}天",
                "color": get_random_color(),
            },
            "solary": {
                "value": f"距离发工资还有{solary_left}天",
                "color": get_random_color(),
            },
            "words": {"value": get_words(), "color": get_random_color()},
        }
        if birthday_left == 0:
            data["birthday_left"]["value"] = "今天是她的生日哦，快去一起甜蜜吧"
        if solary_left == 0:
            data["solary"]["value"] = "今天发工资啦，快去犒劳一下自己吧"

        print(data)
        print(user_ids[i])
        print(template_ids[i])  
        print("--------------------------------")
        try:
            res = wm.send_template(user_ids[i], template_ids[i], data)
            print(f"发送给 {user_ids[i]} 成功：{res}")
        except Exception as e:
            print(f"发送给 {user_ids[i]} 失败：{e}")
