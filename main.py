import os
import time
import subprocess
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# --- 配置区 ---
URL = "https://g4f.gg/jacob"
TARGET_HOURS = 70
MAX_LOOPS = 5

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

def send_tg_message(message):
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("TG 环境变量未配置，跳过发送消息。")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {"chat_id": TG_CHAT_ID, "text": message, "parse_mode": "HTML"}
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"TG 消息发送失败: {e}")

def get_current_ip():
    """获取当前公网 IP"""
    try:
        ip = requests.get('https://api.ipify.org', timeout=5).text
        return ip
    except:
        return "获取失败"

def rotate_warp_ip(old_ip):
    """切换 WARP IP，并确保获取到与上一次不同的新 IP"""
    max_retries = 3
    for i in range(max_retries):
        print(f"正在尝试切换 WARP IP (尝试 {i+1}/{max_retries})...")
        subprocess.run(['warp-cli', '--accept-tos', 'disconnect'], stdout=subprocess.DEVNULL)
        time.sleep(2)
        subprocess.run(['warp-cli', '--accept-tos', 'connect'], stdout=subprocess.DEVNULL)
        
        # 给一定时间让网络恢复
        time.sleep(8)
        new_ip = get_current_ip()
        
        if new_ip == "获取失败":
            print("⚠️ IP 获取失败，重试...")
            continue
            
        if new_ip == old_ip:
            print(f"⚠️ 新 IP ({new_ip}) 与旧 IP 相同，跳过此 IP 重新切换...")
            continue
            
        print(f"✅ WARP IP 切换完成。当前新 IP 为: {new_ip}")
        return new_ip
        
    print("❌ 多次尝试切换 IP 失败 (可能 IP 地址池分配重复)，将使用当前获取到的 IP 继续。")
    return get_current_ip()

def get_current_hours(time_text):
    if not time_text:
        return -1
    try:
        parts = time_text.split(':')
        if len(parts) >= 1:
            return int(parts[0])
    except:
        pass
    return -1

def main():
    co = ChromiumOptions().auto_port()
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    
    page = ChromiumPage(co)
    page.set.timeouts(page_load=15)
    
    loop_count = 0
    success_count = 0
    
    current_ip = get_current_ip()
    print(f"初始 IP: {current_ip}")
    
    while loop_count < MAX_LOOPS:
        loop_count += 1
        print(f"\n--- 开始第 {loop_count}/{MAX_LOOPS} 次循环 ---")
        
        try:
            page.get(URL)
        except Exception as e:
            print(f"[网络状态] 页面底层加载超时或异常，但可能已渲染完成: {e}")
            
        countdown_ele = page.ele('#countdown', timeout=10)
        
        if not countdown_ele:
            print("❌ 核心元素未找到，判定为页面加载彻底失败。正在截图...")
            page.get_screenshot(path=f'timeout_error_{loop_count}.png')
            current_ip = rotate_warp_ip(current_ip)
            continue
            
        current_time_text = countdown_ele.text
        current_hours = get_current_hours(current_time_text)
        print(f"当前剩余时间: {current_time_text} (约 {current_hours} 小时)")
        
        if current_hours >= TARGET_HOURS:
            print(f"✅ 已达到目标 ({TARGET_HOURS}h)，准备退出。")
            break
            
        btn = page.ele('.vote-btn')
        
        # 修复了之前的语法错误，改为判断 is_enabled
        if not btn or not btn.states.is_enabled:
            print("⚠️ 按钮不可点击 (可能 IP 被限制或处于冷却)。准备更换 IP...")
            current_ip = rotate_warp_ip(current_ip)
            continue
            
        print("🟢 按钮状态正常，准备点击...")
        try:
            page.get_screenshot(path=f'before_click_{loop_count}.png')
            
            btn.click(by_js=True)
            print("已发送点击指令，等待 8 秒让后端处理...")
            time.sleep(8)
            
            try:
                page.get(URL)
            except Exception:
                pass
                
            new_countdown_ele = page.ele('#countdown', timeout=10)
            if new_countdown_ele:
                new_time_text = new_countdown_ele.text
                page.get_screenshot(path=f'after_click_{loop_count}.png')
                
                if current_time_text != new_time_text:
                    print(f"🎉 点击成功！时间由 {current_time_text} 变为 {new_time_text}")
                    success_count += 1
                    # 成功后，带着当前的 IP 去获取一个新的 IP
                    current_ip = rotate_warp_ip(current_ip)
                else:
                    print("⚠️ 时间未发生变化，点击可能被服务端拒绝，更换 IP 准备重试。")
                    current_ip = rotate_warp_ip(current_ip)
            else:
                print("点击后无法重新获取页面数据，更换 IP 准备重试。")
                current_ip = rotate_warp_ip(current_ip)
                
        except Exception as e:
            print(f"❌ 点击过程发生异常: {e}")
            page.get_screenshot(path=f'exception_error_{loop_count}.png')
            current_ip = rotate_warp_ip(current_ip)

    final_time = "获取失败"
    expiry_info = "获取失败"
    try:
        final_time = page.ele('#countdown').text
        expiry_info = page.ele('.countdown-sub').text
    except:
        pass
        
    page.quit()
    
    report_msg = (
        f"🎮 <b>Jacob 服务器续期任务报告</b>\n"
        f"--------------------------\n"
        f"🔄 循环次数: {loop_count} / {MAX_LOOPS}\n"
        f"✅ 成功点击次数: {success_count}\n"
        f"⏳ 最终时长: <code>{final_time}</code>\n"
        f"📅 到期信息: {expiry_info}\n"
    )
    print("任务结束，正在发送报告...")
    send_tg_message(report_msg)
    print("流程全部完成。")

if __name__ == '__main__':
    main()
