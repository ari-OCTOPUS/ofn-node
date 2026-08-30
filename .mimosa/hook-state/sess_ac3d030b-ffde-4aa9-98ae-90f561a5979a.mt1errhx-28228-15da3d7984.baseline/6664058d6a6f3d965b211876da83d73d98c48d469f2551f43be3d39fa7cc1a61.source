import paramiko
import time
from datetime import datetime

NODES = {
    "OPI-5-Pro-01": "192.168.0.182",
    "OPI-5-Pro-02": "192.168.0.114",
    "OPI-5-Pro-03": "192.168.0.100",
}

def get_node_status(name, ip):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    
    try:
        ssh.connect(ip, username='root', timeout=8)
        
        # همه دستورات رو یکجا اجرا کن - یه SSH connection
        cmd = (
            "echo TEMP=$(cat /sys/class/thermal/thermal_zone0/temp); "
            "echo UPTIME=$(uptime -p); "
            "echo MINER=$(systemctl is-active ccminer.service); "
            "echo CPU=$(top -bn2 -d0.5 | grep 'Cpu(s)' | tail -1 | awk '{print $2+$4}')"
        )
        
        stdin, stdout, stderr = ssh.exec_command(cmd, timeout=15)
        output = stdout.read().decode().strip()
        ssh.close()
        
        results = {}
        for line in output.splitlines():
            if '=' in line:
                key, _, val = line.partition('=')
                results[key.strip()] = val.strip()
        
        return results
        
    except Exception as e:
        return None

def main():
    print("\033[2J\033[H", end="")  # پاک کردن صفحه
    print(f"{'='*85}")
    print(f"  SYDNEY CLUSTER LAB | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*85}\n")
    
    header = f"{'Node Name':<15} | {'IP':<15} | {'Temp':<8} | {'Miner':<12} | {'CPU %':<8} | Uptime"
    print(header)
    print("-" * 85)
    
    for name, ip in NODES.items():
        data = get_node_status(name, ip)
        
        if data:
            # دما
            try:
                temp_c = float(data.get('TEMP', 0)) / 1000
                temp_str = f"{temp_c:.1f}°C"
                if temp_c > 75:
                    temp_str += " 🔥"
            except:
                temp_str = "N/A"
            
            # وضعیت ماینر
            miner_active = data.get('MINER', '').strip() == 'active'
            miner_icon = "✅ ACTIVE" if miner_active else "❌ STOPPED"
            
            # CPU
            try:
                cpu = float(data.get('CPU', 0))
                cpu_str = f"{cpu:.1f}"
            except:
                cpu_str = "N/A"
            
            uptime = data.get('UPTIME', 'N/A')
            
            print(f"{name:<15} | {ip:<15} | {temp_str:<8} | {miner_icon:<12} | {cpu_str:<8}% | {uptime}")
        else:
            print(f"{name:<15} | {ip:<15} | ⚠️  OFFLINE (Check Power/Network)")
    
    print(f"\n{'='*85}")

if __name__ == "__main__":
    try:
        while True:
            main()
            print("\nRefreshing in 60 seconds... (Ctrl+C to stop)")
            time.sleep(60)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")