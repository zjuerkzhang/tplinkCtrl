#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP-Link路由器设备上网控制脚本
用于控制指定设备（如android-eee46d2d0988b09e）的上网权限
"""

import requests
import json
import sys
import os
from typing import Optional, Dict, Any

def security_encode(password, salt="RDpbLfCPsJZ7fiv", dictionary="yLwVl0zKqws7LgKPRQ84Mdt708T1qQ3Ha7xv3H7NyU84p21BriUWBU43odz3iP4rBL3cD02KZciXTysVXiV8ngg6vL48rPJyAUw0HurW20xqxv9aYb4M9wK1Ae0wlro510qXeU07kV57fQMc8L6aLgMLwygtc0F10a0Dg70TOoouyFhdysuRMO51yY5ZlOZZLEal1h0t9YQW0Ko7oBwmCAHoic4HYbUyVeU3sfQ1xtXcPcf1aT303wAQhv66qzW"):
    d = ""
    g = len(password)
    f = len(salt)
    h = len(dictionary)
    e = max(g, f)

    for m in range(e):
        # 默认值为 187 (对应 JS 中的 k = 187, l = 187)
        k = 187
        l = 187

        if m >= g:
            l = ord(salt[m])
        elif m >= f:
            k = ord(password[m])
        else:
            k = ord(password[m])
            l = ord(salt[m])

        # 核心异或取模逻辑
        index = (k ^ l) % h
        d += dictionary[index]

    return d

class TPLinkController:
    def __init__(self, router_ip: str = "192.168.1.1", password: str = "password"):
        """
        初始化TP-Link路由器控制器

        Args:
            router_ip: 路由器IP地址
            password: 路由器登录密码
        """
        self.router_ip = router_ip
        self.password = security_encode(password)
        self.base_url = f"http://{router_ip}"
        self.stok = None
        self.session = requests.Session()
        self.devices_cache = None  # 缓存设备信息

    def login(self) -> bool:
        """
        登录路由器获取认证令牌(stok)

        Returns:
            bool: 登录成功返回True，失败返回False
        """
        try:
            login_url = f"{self.base_url}"
            login_data = {
                "method": "do",
                "login": {
                    "password": self.password
                }
            }

            response = self.session.post(login_url, json=login_data, timeout=5)
            result = response.json()

            if result.get("error_code") == 0 and "stok" in result:
                self.stok = result["stok"]
                print(f"✓ 登录成功，获得令牌: {self.stok[:20]}...")
                # 登录成功后，初始化一次设备信息
                self.get_devices()
                return True
            else:
                print(f"✗ 登录失败: {result.get('error_code')}")
                return False
        except Exception as e:
            print(f"✗ 登录出错: {e}")
            return False

    def get_devices(self) -> Optional[Dict[str, Any]]:
        """
        获取路由器连接的所有设备信息，并刷新缓存

        Returns:
            dict: 设备信息字典，获取失败返回None
        """
        if not self.stok:
            print("✗ 未登录，请先调用login()方法")
            return None

        try:
            url = f"{self.base_url}/stok={self.stok}/ds"
            request_data = {
                "hosts_info": {
                    "table": "host_info",
                    "name": "cap_host_num"
                },
                "network": {
                    "name": "iface_mac"
                },
                "hyfi": {
                    "table": ["connected_ext"]
                },
                "method": "get"
            }

            response = self.session.post(url, json=request_data, timeout=5)
            result = response.json()

            if result.get("error_code") == 0:
                print("✓ 成功获取设备信息")
                # 更新缓存
                self.devices_cache = result
                return result
            else:
                print(f"✗ 获取设备信息失败: {result.get('error_code')}")
                return None
        except Exception as e:
            print(f"✗ 获取设备信息出错: {e}")
            return None

    def find_device_by_name(self, device_name: str) -> Optional[Dict[str, Any]]:
        """
        根据设备名称查找设备信息

        Args:
            device_name: 设备名称（如 "android-eee46d2d0988b09e"）

        Returns:
            dict: 设备信息，未找到返回None
        """
        devices_info = self.get_devices()
        if not devices_info:
            return None

        try:
            hosts = devices_info.get("hosts_info", {}).get("host_info", [])
            for host_entry in hosts:
                for host_key, host_data in host_entry.items():
                    if device_name in host_data.get("hostname", ""):
                        return host_data

            print(f"✗ 未找到设备: {device_name}")
            return None
        except Exception as e:
            print(f"✗ 查找设备出错: {e}")
            return None

    def set_device_block(self, mac: str = "", device_name: str = "", is_blocked: int = 0) -> bool:
        """
        设置设备的上网权限

        Args:
            mac: 设备MAC地址（可选，但如果device_name为空则必须提供）
            device_name: 设备名称（可选，但如果mac为空则必须提供）
            is_blocked: 1表示禁用上网，0表示允许上网

        Returns:
            bool: 操作成功返回True，失败返回False
        """
        # 验证参数
        if not mac and not device_name:
            print("✗ MAC地址和设备名称不能同时为空，请至少提供其中一个")
            return False

        if not self.stok:
            print("✗ 未登录，请先调用login()方法")
            return False

        # 从缓存中查找完整的设备信息
        if not self.devices_cache:
            print("✗ 设备缓存为空，请先调用list_devices()或login()")
            return False

        try:
            hosts = self.devices_cache.get("hosts_info", {}).get("host_info", [])
            target_device = None

            # 根据MAC或设备名查找设备
            for host_entry in hosts:
                for host_key, host_data in host_entry.items():
                    host_mac = host_data.get("mac", "").lower()
                    host_name = host_data.get("hostname", "")

                    # 如果提供了MAC，按MAC查找
                    if mac and host_mac == mac.lower():
                        target_device = host_data
                        break
                    # 如果提供了设备名，按设备名查找
                    elif device_name and device_name in host_name:
                        target_device = host_data
                        break
                if target_device:
                    break

            if not target_device:
                print(f"✗ 未找到匹配的设备 (MAC: {mac}, 设备名: {device_name})")
                return False

            # 获取完整的设备信息
            final_mac = target_device.get("mac", "")
            final_name = target_device.get("hostname", "")

            # 发送POST请求
            url = f"{self.base_url}/stok={self.stok}/ds"
            request_data = {
                "hosts_info": {
                    "set_block_flag": {
                        "mac": final_mac,
                        "is_blocked": str(is_blocked),
                        "name": final_name,
                        "down_limit": "0",
                        "up_limit": "0",
                        "forbid_domain": "",
                        "limit_time": ""
                    }
                },
                "method": "do"
            }

            response = self.session.post(url, json=request_data, timeout=5)
            result = response.json()

            if result.get("error_code") == 0:
                action = "禁用" if is_blocked else "启用"
                display_name = final_name if final_name else final_mac
                print(f"✓ 成功{action}设备 {display_name}")
                return True
            else:
                print(f"✗ 设置失败: {result.get('error_code')}")
                return False
        except Exception as e:
            print(f"✗ 设置设备权限出错: {e}")
            return False

    def block_device(self, mac: str = "", device_name: str = "") -> bool:
        """禁用设备上网"""
        return self.set_device_block(mac, device_name, 1)

    def unblock_device(self, mac: str = "", device_name: str = "") -> bool:
        """启用设备上网"""
        return self.set_device_block(mac, device_name, 0)

    def list_devices(self) -> None:
        """列出所有连接的设备"""
        devices_info = self.get_devices()
        if not devices_info:
            return

        try:
            hosts = devices_info.get("hosts_info", {}).get("host_info", [])
            print("\n已连接的设备列表:")
            print("-" * 80)
            print(f"{'序号':<6} {'MAC地址':<20} {'IP地址':<15} {'设备名称':<30} {'状态':<10}")
            print("-" * 80)

            for idx, host_entry in enumerate(hosts, 1):
                for host_key, host_data in host_entry.items():
                    mac = host_data.get("mac", "N/A")
                    ip = host_data.get("ip", "N/A")
                    hostname = host_data.get("hostname", "未命名")
                    blocked = host_data.get("blocked", 0)
                    status = "禁用" if blocked == "1" else "正常"

                    print(f"{idx:<6} {mac:<20} {ip:<15} {hostname:<30} {status:<10}")
            print("-" * 80)
        except Exception as e:
            print(f"✗ 列出设备出错: {e}")


def main():
    """主函数"""
    print("=" * 80)
    print("TP-Link路由器设备上网控制工具")
    print("=" * 80)

    # 读取配置文件
    config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
        router_ip = config.get("router_ip", "192.168.1.1")
        password = config.get("password", "")
    except FileNotFoundError:
        print(f"✗ 配置文件未找到: {config_path}")
        return
    except json.JSONDecodeError:
        print(f"✗ 配置文件格式错误: {config_path}")
        return

    # 创建控制器实例
    controller = TPLinkController(router_ip=router_ip, password=password)

    # 登录
    if not controller.login():
        print("无法连接路由器，请检查IP和密码")
        return

    # 显示菜单
    while True:
        print("\n请选择操作:")
        print("1. 列出所有设备")
        print("2. 禁用设备上网")
        print("3. 启用设备上网")
        print("4. 退出")

        choice = input("请输入选项 (1-4): ").strip()

        if choice == "1":
            controller.list_devices()

        elif choice == "2":
            mac = input("请输入设备MAC地址 (可选，如: AA-AA-AA-AA-AA-AA): ").strip()
            device_name = input("请输入设备名称 (可选，如: deviceNameXxx): ").strip()
            if mac or device_name:
                controller.block_device(mac, device_name)
            else:
                print("✗ MAC地址和设备名称不能同时为空")

        elif choice == "3":
            mac = input("请输入设备MAC地址 (可选，如: AA-AA-AA-AA-AA-AA): ").strip()
            device_name = input("请输入设备名称 (可选，如: deviceNameXxx): ").strip()
            if mac or device_name:
                controller.unblock_device(mac, device_name)
            else:
                print("✗ MAC地址和设备名称不能同时为空")

        elif choice == "4":
            print("退出程序")
            break

        else:
            print("✗ 无效选项，请重新输入")


if __name__ == "__main__":
    main()
