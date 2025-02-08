import speedtest
import ping3
import dns.resolver
import time

def test_speed():
    print("Testing internet speed...")
    st = speedtest.Speedtest()
    st.get_best_server()
    download_speed = st.download() / 1_000_000  # Convert to Mbps
    upload_speed = st.upload() / 1_000_000  # Convert to Mbps
    print(f"Download Speed: {download_speed:.2f} Mbps")
    print(f"Upload Speed: {upload_speed:.2f} Mbps")
    print()

def test_ping(host="120.27.141.61", count=4):
    print(f"Pinging {host}...")
    total_time = 0
    lost_packets = 0
    for _ in range(count):
        try:
            delay = ping3.ping(host, timeout=1)
            if delay is not None:
                total_time += delay * 1000  # Convert to milliseconds
                print(f"Reply from {host}: time={delay * 1000:.2f} ms")
            else:
                lost_packets += 1
                print("Request timed out.")
        except Exception as e:
            lost_packets += 1
            print(f"Error: {e}")
    if count - lost_packets > 0:
        avg_time = total_time / (count - lost_packets)
        print(f"Average ping: {avg_time:.2f} ms")
    else:
        print("All packets lost.")
    print(f"Packet loss: {lost_packets / count * 100:.2f}%")
    print()

def test_dns_response(dns_servers):
    print("Testing DNS server response times...")
    resolver = dns.resolver.Resolver()
    for name, server in dns_servers.items():
        resolver.nameservers = [server]
        start_time = time.time()
        try:
            resolver.resolve("test.86vhuo.cn", "A")
            response_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            print(f"{name} ({server}): {response_time:.2f} ms")
        except Exception as e:
            print(f"{name} ({server}): Error - {e}")
    print()

if __name__ == "__main__":
    # Test internet speed
    test_speed()

    # Test ping to a common server (e.g., Google DNS)
    test_ping("120.48.229.164")

    # Test DNS server response times
    dns_servers = {
        "Google DNS": "8.8.8.8",
        "DNSPod DNS": "119.29.29.29",
        "alibaba DNS": "223.5.5.5",
        "baidu DNS": "180.76.76.76",
		"114 DNS": "114.114.114.114",
		"TWNIC DNS Quad 101 DNS": "101.101.101.101",
    }
    test_dns_response(dns_servers)