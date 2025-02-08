import requests
import speedtest
import ping3
import dns.resolver  # 保证使用正确的模块
import json
import time
import threading  # 用于多线程
import tkinter as tk
from tkinter import messagebox

# 钉钉机器人 Webhook URL
DINGTALK_WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=6f5fa4a0d39e67e1db55ecd5c0ad2b8046face8a1c4f543527693a6aec8bfef7"

def get_external_ip():
    """获取当前网络的出口 IP"""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        response.raise_for_status()  # 检查请求是否成功
        return response.json()['ip']
    except requests.RequestException as e:
        return f"Failed to get IP: {e}"

def test_speed():
    """测试上传和下载速度"""
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download_speed = st.download() / 1_000_000  # 转换为 Mbps
        upload_speed = st.upload() / 1_000_000  # 转换为 Mbps
        return download_speed, upload_speed
    except Exception as e:
        return f"Failed to test speed: {e}", f"Failed to test speed: {e}"

def test_latency_and_packet_loss(targets):
    """测试延迟和丢包率"""
    results = {}
    for target in targets:
        try:
            latency = ping3.ping(target, timeout=2)
            if latency is not None:
                results[target] = {"latency": latency, "packet_loss": 0}
            else:
                results[target] = {"latency": None, "packet_loss": 100}
        except Exception as e:
            results[target] = {"latency": None, "packet_loss": "Error", "error": str(e)}
    return results

def test_dns_resolution_speed(dns_servers):
    """测试 DNS 解析速度"""
    results = {}
    domain = "test.86vhuo.cn"
    for dns_server in dns_servers:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns_server]
        start_time = time.time()
        try:
            resolver.resolve(domain)
            results[dns_server] = (time.time() - start_time) * 1000  # 转换为毫秒
        except dns.resolver.DNSException as e:
            results[dns_server] = f"Failed: {e}"
        except Exception as e:
            results[dns_server] = f"Unknown error: {e}"
    return results

def send_to_dingtalk(name, address, results):
    """将测试结果发送到钉钉"""
    message = {
        "msgtype": "text",
        "text": {
            "content": f"网络测试报告\n姓名: {name}\n地址: {address}\n测试结果:\n{json.dumps(results, indent=2)}"
        }
    }
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(DINGTALK_WEBHOOK_URL, headers=headers, data=json.dumps(message))
        response.raise_for_status()  # 检查请求是否成功
        return response.status_code
    except requests.RequestException as e:
        return f"Failed to send message: {e}"

def gather_results(name, address, callback):
    """收集所有网络测试结果并通过回调更新GUI"""
    results = {}

    # 测试网络出口 IP
    external_ip = get_external_ip()
    results['external_ip'] = external_ip

    # 测试上传和下载速度
    download_speed, upload_speed = test_speed()
    results['download_speed'] = f"{download_speed:.2f} Mbps"
    results['upload_speed'] = f"{upload_speed:.2f} Mbps"

    # 测试到公有云的延迟和丢包率
    cloud_targets = ["8.8.8.8", "120.48.229.164", "api.cloudflare.com", "api.aliyun.com", "cvm.tencentcloudapi.com"]
    cloud_results = test_latency_and_packet_loss(cloud_targets)
    results['cloud_results'] = cloud_results

    # 测试 DNS 解析速度
    dns_servers = ["8.8.8.8", "119.29.29.29", "223.5.5.5", "180.76.76.76", "114.114.114.114", "101.101.101.101"]
    dns_results = test_dns_resolution_speed(dns_servers)
    results['dns_results'] = dns_results

    # 发送到钉钉
    status_code = send_to_dingtalk(name, address, results)

    # 使用 Tkinter 的 after() 方法在主线程中更新 GUI
    root.after(0, callback, results, status_code)

def show_results_in_gui(results, status_code):
    """将结果显示在GUI中"""
    result_str = f"出口 IP: {results['external_ip']}\n"
    result_str += f"下载速度: {results['download_speed']}\n"
    result_str += f"上传速度: {results['upload_speed']}\n"
    result_str += "\n公有云延迟和丢包率:\n"
    for target, result in results['cloud_results'].items():
        result_str += f"{target}: 延迟 {result.get('latency', 'N/A')} ms, 丢包率 {result.get('packet_loss', 'N/A')}%\n"
    result_str += "\nDNS 解析速度:\n"
    for dns, speed in results['dns_results'].items():
        result_str += f"{dns}: {speed} ms\n"
    
    result_display.config(state=tk.NORMAL)
    result_display.delete(1.0, tk.END)
    result_display.insert(tk.END, result_str)
    result_display.config(state=tk.DISABLED)

    # 显示钉钉发送结果
    if status_code == 200:
        messagebox.showinfo("成功", "测试结果已成功发送到钉钉！")
    else:
        messagebox.showerror("失败", f"发送测试结果到钉钉失败！状态码: {status_code}")

def on_test_button_click():
    """处理按钮点击事件"""
    name = name_entry.get()
    address = address_entry.get()

    if not name or not address:
        messagebox.showwarning("输入错误", "请填写姓名和地址")
        return

    # 启动一个新线程执行耗时操作
    test_thread = threading.Thread(target=gather_results, args=(name, address, show_results_in_gui))
    test_thread.start()

# 创建GUI
root = tk.Tk()
root.title("网络测试工具")

# 姓名输入框
tk.Label(root, text="请输入您的邮箱账号前缀:").grid(row=0, column=0, padx=10, pady=5)
name_entry = tk.Entry(root, width=40)
name_entry.grid(row=0, column=1, padx=10, pady=5)

# 地址输入框
tk.Label(root, text="请输入您所在的校区名称:").grid(row=1, column=0, padx=10, pady=5)
address_entry = tk.Entry(root, width=40)
address_entry.grid(row=1, column=1, padx=10, pady=5)

# 测试按钮
test_button = tk.Button(root, text="开始测试", command=on_test_button_click)
test_button.grid(row=2, columnspan=2, pady=20)

# 显示测试结果的文本框
result_display = tk.Text(root, width=80, height=20, wrap=tk.WORD, state=tk.DISABLED)
result_display.grid(row=3, columnspan=2, padx=10, pady=5)

# 运行GUI
root.mainloop()
