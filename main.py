import os
import time
import subprocess
import requests
from DrissionPage import ChromiumPage, ChromiumOptions

# --- 配置区 ---
URL = "https://g4f.gg/jacob"
TARGET_HOURS = 70
MAX_LOOPS = 25

TG_BOT_TOKEN = os.environ.get("TG_BOT_TOKEN")
TG_CHAT_ID = os.environ.get("TG_CHAT_ID")

def send_tg_message(message):
    """发送 TG 消息"""
    if not TG_BOT_TOKEN or not TG_CHAT_ID:
        print("TG 环境变量未配置，跳过发送消息。")
        return
    url = f"https://api.telegram.org/bot{TG_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TG_CHAT_ID,
        "text": message,
        "parse_mode": "HTML"
    }
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"TG 消息发送失败: {e}")

def rotate_warp_ip():
    """切换 WARP IP"""
    print("正在切换 WARP IP...")
    subprocess.run(['warp-cli', '--accept-tos', 'disconnect'], stdout=subprocess.DEVNULL)
    time.sleep(2)
    subprocess.run(['warp-cli', '--accept-tos', 'connect'], stdout=subprocess.DEVNULL)
    # 给一点时间让网络重新连通
    time.sleep(8)
    print("WARP IP 切换完成。")

def get_current_hours(page):
    """获取当前倒计时的小时数"""
    try:
        time_text = page.ele('#countdown').text
        if not time_text:
            return -1
        # 分割时间戳 比如 "50:40:01"
        parts = time_text.split(':')
        if len(parts) >= 1:
            return int(parts[0])
    except Exception as e:
        print(f"获取时间失败: {e}")
    return -1

def main():
    # 初始化无头浏览器配置
    co = ChromiumOptions().auto_port()
    # 针对服务器环境的无头优化，由于使用了 xvfb，这里不需要严格意义的 headless
    co.set_argument('--no-sandbox')
    co.set_argument('--disable-gpu')
    co.set_argument('--disable-dev-shm-usage')
    
    page = ChromiumPage(co)
    
    loop_count = 0
    success_count = 0
    
    while loop_count < MAX_LOOPS:
        loop_count += 1
        print(f"\n--- 开始第 {loop_count}/{MAX_LOOPS} 次循环 ---")
        
        try:
            page.get(URL)
            page.wait.ele_loaded('#countdown', timeout=15)
        except Exception:
            print("页面加载超时，尝试更换 IP...")
            rotate_warp_ip()
            continue
            
        current_hours = get_current_hours(page)
        print(f"当前剩余时间: {page.ele('#countdown').text} (约 {current_hours} 小时)")
        
        # 1. 检测是否已达到目标时间
        if current_hours >= TARGET_HOURS:
            print(f"当前小时数 ({current_hours}) 已达到或超过目标 ({TARGET_HOURS})，准备退出。")
            break
            
        # 2. 检测按钮是否可点击
        btn = page.ele('.vote-btn')
        # 如果按钮不存在，或者按钮存在但被禁用 (disabled)，说明当前 IP 不可用
        if not btn or btn.states.is_disabled:
            print("按钮不可点击 (可能是 IP 已被使用限制)。准备更换 IP...")
            rotate_warp_ip()
            continue
            
        # 3. 点击按钮
        print("按钮状态正常，执行点击...")
        try:
            # 记录点击前的时间文本用于对比
            old_time_text = page.ele('#countdown').text
            btn.click()
            
            # 等待页面刷新或元素发生变化
            time.sleep(5)
            page.get(URL) # 强制刷新确保数据是最新的
            page.wait.ele_loaded('#countdown', timeout=15)
            
            new_time_text = page.ele('#countdown').text
            
            # 4. 检测时间是否增加
            if old_time_text != new_time_text:
                print(f"点击成功！时间由 {old_time_text} 变为 {new_time_text}")
                success_count += 1
                # 成功后，为下一次请求准备一个新 IP
                rotate_warp_ip()
            else:
                print("时间未发生变化，可能请求失败，更换 IP 准备重试。")
                rotate_warp_ip()
                
        except Exception as e:
            print(f"点击过程发生异常: {e}")
            rotate_warp_ip()

    # 循环结束后的总结与汇报
    final_time = "获取失败"
    expiry_info = "获取失败"
    try:
        final_time = page.ele('#countdown').text
        expiry_info = page.ele('.countdown-sub').text
    except:
        pass
        
    page.quit()
    
    # 组装发送 TG 报告
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
