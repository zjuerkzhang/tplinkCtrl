#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TP-Link路由器设备上网控制守护进程
根据配置文件在特定时间禁用或启用设备联网
"""

import json
import os
import sys
import signal
import logging
from typing import Dict, Any, List
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from main import TPLinkController

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(os.path.dirname(__file__), "..", "log", "daemon.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class TPLinkDaemon:
    def __init__(self, config_path: str = None):
        """
        初始化守护进程

        Args:
            config_path: 配置文件路径，默认为 ../config/schedule_config.json
        """
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "..", "config", "schedule_config.json")

        self.config_path = config_path
        self.scheduler = BackgroundScheduler()
        self.controller = None
        self.config = {}

        # 注册信号处理器
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """处理系统信号"""
        logger.info(f"收到信号 {signum}，正在关闭守护进程...")
        self.stop()
        sys.exit(0)

    def load_config(self) -> bool:
        """
        加载配置文件

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = json.load(f)
            logger.info(f"成功加载配置文件: {self.config_path}")
            return True
        except FileNotFoundError:
            logger.error(f"配置文件未找到: {self.config_path}")
            return False
        except json.JSONDecodeError:
            logger.error(f"配置文件格式错误: {self.config_path}")
            return False

    def init_controller(self) -> bool:
        """
        初始化TPLinkController

        Returns:
            bool: 成功返回True，失败返回False
        """
        try:
            main_config_path = os.path.join(os.path.dirname(__file__), "..", "config", "config.json")
            with open(main_config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)

            router_ip = config.get("router_ip", "192.168.1.1")
            password = config.get("password", "")

            self.controller = TPLinkController(router_ip=router_ip, password=password)

            # 登录
            if not self.controller.login():
                logger.error("无法连接路由器，请检查IP和密码")
                return False

            logger.info("成功连接到路由器")
            return True
        except Exception as e:
            logger.error(f"初始化控制器出错: {e}")
            return False

    def _execute_task(self, device_mac: str, device_name: str, action: str) -> None:
        """
        执行设备控制任务

        Args:
            device_mac: 设备MAC地址
            device_name: 设备名称
            action: 操作 ('block' 或 'unblock')
        """
        try:
            if action == "block":
                success = self.controller.block_device(device_mac, device_name)
                action_name = "禁用"
            elif action == "unblock":
                success = self.controller.unblock_device(device_mac, device_name)
                action_name = "启用"
            else:
                logger.error(f"未知的操作: {action}")
                return

            if success:
                display_name = device_name if device_name else device_mac
                logger.info(f"成功执行定时任务: {action_name}设备 {display_name}")
            else:
                logger.error(f"执行定时任务失败: {action} {device_mac} {device_name}")
        except Exception as e:
            logger.error(f"执行任务出错: {e}")

    def setup_schedules(self) -> bool:
        """
        设置定时任务

        Returns:
            bool: 成功返回True，失败返回False
        """
        if not self.config:
            logger.error("配置文件为空")
            return False

        tasks = self.config.get("tasks", [])
        if not tasks:
            logger.warning("配置文件中没有定义任何任务")
            return True

        for task in tasks:
            try:
                task_name = task.get("name", "未命名任务")
                device_mac = task.get("device_mac", "")
                device_name = task.get("device_name", "")
                action = task.get("action", "")
                cron_expression = task.get("cron", "")
                enabled = task.get("enabled", True)

                if not enabled:
                    logger.info(f"任务已禁用: {task_name}")
                    continue

                if not action or action not in ["block", "unblock"]:
                    logger.error(f"任务 {task_name} 的action无效: {action}")
                    continue

                if not device_mac and not device_name:
                    logger.error(f"任务 {task_name} 的MAC和设备名都为空")
                    continue

                if not cron_expression:
                    logger.error(f"任务 {task_name} 没有定义cron表达式")
                    continue

                # 添加定时任务
                trigger = CronTrigger.from_crontab(cron_expression)
                self.scheduler.add_job(
                    self._execute_task,
                    trigger=trigger,
                    args=[device_mac, device_name, action],
                    id=task_name,
                    name=task_name,
                    replace_existing=True
                )
                logger.info(f"添加定时任务: {task_name} (cron: {cron_expression})")

            except Exception as e:
                logger.error(f"添加定时任务失败: {e}")
                continue

        return True

    def start(self) -> None:
        """启动守护进程"""
        logger.info("=" * 80)
        logger.info("TP-Link路由器设备上网控制守护进程启动")
        logger.info("=" * 80)

        # 加载配置
        if not self.load_config():
            logger.error("加载配置文件失败")
            return

        # 初始化控制器
        if not self.init_controller():
            logger.error("初始化控制器失败")
            return

        # 设置定时任务
        if not self.setup_schedules():
            logger.error("设置定时任务失败")
            return

        # 启动调度器
        try:
            self.scheduler.start()
            logger.info("守护进程已启动，正在运行定时任务...")

            # 保持进程运行
            import time
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("接收到中断信号，正在关闭...")
            self.stop()
        except Exception as e:
            logger.error(f"守护进程运行出错: {e}")
            self.stop()

    def stop(self) -> None:
        """停止守护进程"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("守护进程已停止")


def main():
    """主函数"""
    # 创建log目录
    log_dir = os.path.join(os.path.dirname(__file__), "..", "log")
    os.makedirs(log_dir, exist_ok=True)

    # 获取配置文件路径（可从命令行参数指定）
    config_path = sys.argv[1] if len(sys.argv) > 1 else None

    # 创建并启动守护进程
    daemon = TPLinkDaemon(config_path)
    daemon.start()


if __name__ == "__main__":
    main()
