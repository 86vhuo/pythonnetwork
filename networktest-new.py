import requests
import speedtest
import ping3
import dns.resolver
import json
import time

# 钉钉机器人 Webhook URL
DINGTALK_WEBHOOK_URL = "https://oapi.dingtalk.com/robot/send?access_token=6f5fa4a0d39e67e1db55ecd5c0ad2b8046face8a1c4f543527693a6aec8bfef7"

def get_external_ip():
    """获取当前网络的出口 IP"""
    try:
        response = requests.get('https://api.ipify.org?format=json')
        return response.json()['ip']
    except Exception as e:
        return f"Failed to get IP: {e}"

def test_speed():
    """测试上传和下载速度"""
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # 转换为 Mbps
    upload_speed = st.upload() / 1_000_000  # 转换为 Mbps
    return download_speed, upload_speed

def test_latency_and_packet_loss(targets):
    """测试延迟和丢包率"""
    results = {}
    for target in targets:
        latency = ping3.ping(target, timeout=2)
        if latency is not None:
            results[target] = {"latency": latency, "packet_loss": 0}
        else:
            results[target] = {"latency": None, "packet_loss": 100}
    return results

def test_dns_resolution_speed(dns_servers):
    """测试 DNS 解析速度"""
    results = {}
    domain = "test.86vhuo.cn"
    for dns in dns_servers:
        resolver = dns.resolver.Resolver()
        resolver.nameservers = [dns]
        start_time = time.time()
        try:
            resolver.resolve(domain)
            results[dns] = (time.time() - start_time) * 1000  # 转换为毫秒
        except Exception as e:
            results[dns] = f"Failed: {e}"
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
    response = requests.post(DINGTALK_WEBHOOK_URL, headers=headers, data=json.dumps(message))
    return response.status_code

def main():
    # 用户输入姓名和地址
    name = input("请输入您的邮箱账号前缀: ")
    address = input("请输入您所在的校区名称: ")

    # 测试网络出口 IP
    external_ip = get_external_ip()
    print(f"出口 IP: {external_ip}")

    # 测试上传和下载速度
    download_speed, upload_speed = test_speed()
    print(f"下载速度: {download_speed:.2f} Mbps")
    print(f"上传速度: {upload_speed:.2f} Mbps")

    # 测试到公有云的延迟和丢包率
    cloud_targets = ["8.8.8.8", "120.48.229.164", "api.cloudflare.com", "api.aliyun.com", "cvm.tencentcloudapi.com"]
    cloud_results = test_latency_and_packet_loss(cloud_targets)
    print("公有云延迟和丢包率:")
    for target, result in cloud_results.items():
        print(f"{target}: 延迟 {result['latency']} ms, 丢包率 {result['packet_loss']}%")

    # 测试 DNS 解析速度
    dns_servers = ["8.8.8.8", "119.29.29.29", "223.5.5.5", "180.76.76.76", "114.114.114.114", "101.101.101.101"]
    dns_results = test_dns_resolution_speed(dns_servers)
    print("DNS 解析速度:")
    for dns, speed in dns_results.items():
        print(f"{dns}: {speed} ms")

    # 汇总测试结果
    results = {
        "external_ip": external_ip,
        "download_speed": f"{download_speed:.2f} Mbps",
        "upload_speed": f"{upload_speed:.2f} Mbps",
        "cloud_results": cloud_results,
        "dns_results": dns_results
    }

    # 发送测试结果到钉钉
    status_code = send_to_dingtalk(name, address, results)
    if status_code == 200:
        print("测试结果已成功发送到钉钉！")
    else:
        print("发送测试结果到钉钉失败！")

if __name__ == "__main__":
    main()