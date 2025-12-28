# TP-Link Router Device Control Tool

一个功能强大的 TP-Link 路由器设备上网控制工具，支持定时自动管理设备的网络访问权限。

[中文说明](#中文说明) | [English](#english)

## 中文说明

### 功能特性

- 🎮 **交互式控制** - 手动禁用/启用设备上网
- 📅 **定时自动化** - 使用 Cron 表达式定义精确的时间表
- 🔍 **灵活识别** - 支持按 MAC 地址或设备名称识别设备
- 👨‍👩‍👧‍👦 **家长控制** - 为小孩管理设备的网络访问时间
- 📝 **完整日志** - 所有操作都被记录，方便审计和调试
- 🚀 **守护进程** - 后台运行，自动执行定时任务

### 快速开始

#### 前置条件

- Python 3.11+
- pip/uv（包管理工具）
- TP-Link 路由器（需要支持相应的 API）

#### 1. 克隆项目

```bash
git clone https://github.com/yourusername/tplinkctrl.git
cd tplinkctrl
```

#### 2. 安装依赖

```bash
# 使用 uv（推荐）
uv sync

# 或使用 pip
pip install -e .
```

#### 3. 配置路由器凭证

编辑 `config/config.json`，输入你的路由器 IP 和登录密码：

```json
{
  "router_ip": "192.168.0.1",
  "password": "your_router_password"
}
```

#### 4. 运行工具

**交互式使用：**

```bash
cd src
python3 main.py
```

然后选择操作：
- 1: 列出所有连接的设备
- 2: 禁用设备上网
- 3: 启用设备上网
- 4: 退出

**启动守护进程：**

首先配置定时任务 `config/schedule_config.json`，然后：

```bash
cd src
python3 daemon.py
```

### 配置说明

#### 路由器配置 - `config/config.json`

```json
{
  "router_ip": "192.168.0.1",
  "password": "router_password"
}
```

#### 定时任务配置 - `config/schedule_config.json`

```json
{
  "tasks": [
    {
      "name": "任务名称",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "device_name": "deviceNameXxx",
      "action": "block",
      "cron": "0 22 * * *",
      "enabled": true,
      "description": "每天晚上10点禁用设备"
    }
  ]
}
```

**任务参数：**

| 参数 | 说明 | 必需 |
|------|------|------|
| `name` | 任务唯一名称 | ✅ |
| `device_mac` | 设备 MAC 地址 | ⚠️* |
| `device_name` | 设备名称 | ⚠️* |
| `action` | `block` 或 `unblock` | ✅ |
| `cron` | Cron 表达式 | ✅ |
| `enabled` | 是否启用任务 | ✅ |
| `description` | 任务描述 | ❌ |

*: MAC 和设备名至少需要一个

### Cron 表达式

| 表达式 | 含义 |
|--------|------|
| `0 22 * * *` | 每天晚上 10 点 |
| `0 8 * * *` | 每天早上 8 点 |
| `0 9 * * 1-5` | 周一到周五早上 9 点 |
| `0 12 * * 0,6` | 周末中午 12 点 |
| `*/15 * * * *` | 每 15 分钟 |

更多 Cron 表达式说明，见 [DAEMON_README.md](DAEMON_README.md)。

### 项目结构

```
tplinkctrl/
├── src/
│   ├── main.py           # 主程序（交互式）
│   └── daemon.py         # 守护进程
├── config/
│   ├── config.json       # 路由器配置
│   └── schedule_config.json  # 定时任务配置
├── log/
│   └── daemon.log        # 守护进程日志
├── pyproject.toml        # 项目配置
├── README.md             # 本文件
└── DAEMON_README.md      # 守护进程详细说明
```

### 常见用途

#### 1. 控制小孩的设备

```json
{
  "tasks": [
    {
      "name": "学习时间禁用设备",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "action": "block",
      "cron": "0 7 * * 1-5",
      "enabled": true
    },
    {
      "name": "放学后启用设备",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "action": "unblock",
      "cron": "0 18 * * 1-5",
      "enabled": true
    }
  ]
}
```

#### 2. 工作时间管理

```json
{
  "tasks": [
    {
      "name": "工作时间禁用娱乐设备",
      "device_name": "deviceNameXxx",
      "action": "block",
      "cron": "0 9 * * 1-5",
      "enabled": true
    },
    {
      "name": "下班启用娱乐设备",
      "device_name": "deviceNameXxx",
      "action": "unblock",
      "cron": "0 18 * * 1-5",
      "enabled": true
    }
  ]
}
```

### 故障排除

**无法连接到路由器？**
- 检查 `config/config.json` 中的 IP 地址是否正确
- 检查密码是否正确
- 确保路由器在线且可访问

**定时任务未执行？**
- 检查 `schedule_config.json` 中任务的 `enabled` 是否为 `true`
- 检查 Cron 表达式语法
- 查看 `log/daemon.log` 中的错误信息

**设备不存在？**
- 运行 `main.py` 选项 1 查看所有连接的设备
- 确认设备 MAC 地址或名称是否正确

### 作为系统服务运行

将守护进程配置为系统服务，开机自启：

```bash
sudo cp tplinkCtrl-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tplinkCtrl-daemon.service
sudo systemctl start tplinkCtrl-daemon.service
```

查看状态：
```bash
sudo systemctl status tplinkCtrl-daemon.service
tail -f log/daemon.log
```

### 许可证

MIT License

### 贡献

欢迎提交 Issue 和 Pull Request！

---

## English

### Features

- 🎮 **Interactive Control** - Manually enable/disable device internet access
- 📅 **Scheduled Automation** - Define precise schedules using Cron expressions
- 🔍 **Flexible Device Identification** - Identify devices by MAC address or hostname
- 👨‍👩‍👧‍👦 **Parental Control** - Manage children's device network access times
- 📝 **Complete Logging** - All operations are logged for auditing and debugging
- 🚀 **Daemon Mode** - Run in background and execute scheduled tasks automatically

### Quick Start

#### Prerequisites

- Python 3.11+
- pip/uv (package manager)
- TP-Link Router (with supported API)

#### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/tplinkctrl.git
cd tplinkctrl
```

#### 2. Install Dependencies

```bash
# Using uv (recommended)
uv sync

# Or using pip
pip install -e .
```

#### 3. Configure Router Credentials

Edit `config/config.json` with your router IP and login password:

```json
{
  "router_ip": "192.168.0.1",
  "password": "your_router_password"
}
```

#### 4. Run the Tool

**Interactive Mode:**

```bash
cd src
python3 main.py
```

**Daemon Mode:**

First configure `config/schedule_config.json`, then:

```bash
cd src
python3 daemon.py
```

### Documentation

- [DAEMON_README.md](DAEMON_README.md) - Detailed daemon mode documentation

### License

MIT License
