"""
目的: 利用可能なネットワークインターフェースを検出するユーティリティ関数を提供します。
get_network_interfaces 関数:
・システム上のすべてのネットワークインターフェースをリストとして返します。
・対応OS: Linux（ip link show）および Windows（netsh interface show interface）。
・日本語環境でのインターフェース検出にも対応。
"""

import platform
import subprocess

def get_network_interfaces():
    interfaces = []
    try:
        system_platform = platform.system()
        if system_platform == "Linux":
            result = subprocess.run("ip link show", shell=True, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if ": " in line and not line.startswith(" "):
                    interface = line.split(": ")[1].split("@")[0]
                    interfaces.append(interface)
        elif system_platform == "Windows":
            result = subprocess.run("netsh interface show interface", shell=True, capture_output=True, text=True)
            for line in result.stdout.splitlines():
                if "Enabled" in line or "有効" in line:  # 日本語環境に対応
                    interfaces.append(line.split()[-1])
        else:
            print(f"Unsupported platform: {system_platform}")
    except Exception as e:
        print(f"Error detecting network interfaces: {e}")
    return interfaces
