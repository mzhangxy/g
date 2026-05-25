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

def rotate_warp_ip():
    print("正在切换 WARP IP...")
    subprocess.run(['warp-cli', '--accept-tos', 'disconnect'], stdout=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.run(['warp-cli', '--accept-tos', 'connect'], stdout=subprocess.DEVNULL)
    time.sleep(8)
    new_ip = get_current_ip()
    print(f"WARP IP 切换完成。当前新 IP 为: {new_ip}")

def get_current_hours(page):
    try:
        time_text = page.ele('#countdown').text
        if not time_text:
            return -1
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
    
    loop_count = 0
    success_count = 0
    
    # 初始运行前打印一下当前 IP
    print(f"初始 IP: {get_current_ip()}")
    
    while loop_count < MAX_LOOPS:
        loop_count += 1
        print(f"\n--- 开始第 {loop_count}/{MAX_LOOPS} 次循环 ---")
        
        try:
            page.get(URL)
            page.wait.ele_loaded('#countdown', timeout=15)
        except Exception:
            print("页面加载超时！正在截图保存为 timeout_error.png...")
            # 记录超时瞬间的页面状态
            page.get_screenshot(path=f'timeout_error_{loop_count}.png')
            print("尝试更换 IP...")
            rotate_warp_ip()
            continue
            
        current_hours = get_current_hours(page)
        print(f"当前剩余时间: {page.ele('#countdown').text} (约 {current_hours} 小时)")
        
        if current_hours >= TARGET_HOURS:
            print(f"已达到目标 ({TARGET_HOURS}h)，准备退出。")
            break
            
        btn = page.ele('.vote-btn')
        if not btn or btn.states.is_disabled:
            print("按钮不可点击。准备更换 IP...")
            rotate_warp_ip()
            continue
            
        print("按钮状态正常，准备点击...")
        try:
            old_time_text = page.ele('#countdown').text
            
            # 点击前截图
            page.get_screenshot(path=f'before_click_{loop_count}.png')
            print(f"已保存点击前截图: before_click_{loop_count}.png")
            
            btn.click()
            time.sleep(5)
            page.get(URL) 
            page.wait.ele_loaded('#countdown', timeout=15)
            
            # 点击后加载完成截图
            page.get_screenshot(path=f'after_click_{loop_count}.png')
            print(f"已保存点击后截图: after_click_{loop_count}.png")
            
            new_time_text = page.ele('#countdown').text
            
            if old_time_text != new_time_text:
                print(f"点击成功！时间由 {old_time_text} 变为 {new_time_text}")
                success_count += 1
                rotate_warp_ip()
            else:
                print("时间未发生变化，更换 IP 准备重试。")
                rotate_warp_ip()
                
        except Exception as e:
            print(f"点击过程发生异常: {e}")
            page.get_screenshot(path=f'exception_error_{loop_count}.png')
            rotate_warp_ip()

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
