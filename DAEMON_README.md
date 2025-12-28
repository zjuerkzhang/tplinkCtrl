# TP-Link 路由器设备上网控制守护进程

## 功能

守护进程 `daemon.py` 可以根据配置文件在特定时间自动禁用或启用路由器连接的设备，支持：

- **时间表配置** - 使用 Cron 表达式定义任务时间
- **灵活的设备识别** - 支持按 MAC 地址或设备名称识别设备
- **定时自动化** - 后台运行，无需手动干预
- **日志记录** - 所有操作都被记录到日志文件

## 配置文件

配置文件位于 `config/schedule_config.json`，格式如下：

```json
{
  "tasks": [
    {
      "name": "任务名称",
      "device_mac": "MAC地址（可选）",
      "device_name": "设备名称（可选）",
      "action": "block 或 unblock",
      "cron": "Cron 表达式",
      "enabled": true,
      "description": "任务描述"
    }
  ]
}
```

### 参数说明

| 参数 | 说明 | 示例 |
|------|------|------|
| `name` | 任务唯一名称 | "晚间禁用手机" |
| `device_mac` | 设备MAC地址（MAC和name至少一个） | "AA-AA-AA-AA-AA-AA" |
| `device_name` | 设备名称（MAC和name至少一个） | "deviceNameXxx" |
| `action` | 操作类型 | "block" 或 "unblock" |
| `cron` | Cron 表达式 | "0 22 * * *" |
| `enabled` | 是否启用此任务 | true/false |
| `description` | 任务描述（可选） | "每天晚上10点禁用" |

### Cron 表达式格式

```
┌───────────── 分钟 (0 - 59)
│ ┌───────────── 小时 (0 - 23)
│ │ ┌───────────── 日期 (1 - 31)
│ │ │ ┌───────────── 月份 (1 - 12)
│ │ │ │ ┌───────────── 周几 (0 - 6) (0 = 周日, 1 = 周一, ..., 6 = 周六)
│ │ │ │ │
│ │ │ │ │
* * * * *
```

#### 常用 Cron 表达式示例

| 表达式 | 说明 |
|--------|------|
| `0 22 * * *` | 每天晚上10点 |
| `0 8 * * *` | 每天早上8点 |
| `0 9 * * 1-5` | 周一到周五早上9点（工作日） |
| `0 12 * * 0,6` | 周六和周日中午12点（周末） |
| `0 0 1 * *` | 每个月第一天的午夜 |
| `*/15 * * * *` | 每15分钟 |
| `0 */2 * * *` | 每2小时 |

## 使用方法

### 1. 安装依赖

```bash
# 从项目根目录运行
uv sync
```

### 2. 配置任务

编辑 `config/schedule_config.json`，添加你需要的定时任务。

### 3. 直接运行守护进程

```bash
# 从 src 目录运行
cd src
python3 daemon.py

# 或指定自定义配置文件
python3 daemon.py /path/to/custom_config.json
```

### 4. 作为 Systemd 服务运行（推荐）

#### 安装服务

```bash
sudo cp tplinkCtrl-daemon.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tplinkCtrl-daemon.service
```

#### 启动服务

```bash
sudo systemctl start tplinkCtrl-daemon.service
```

#### 查看服务状态

```bash
sudo systemctl status tplinkCtrl-daemon.service
```

#### 查看日志

```bash
# 实时查看日志
journalctl -u tplinkCtrl-daemon.service -f

# 或查看存储的日志文件
tail -f log/daemon.log
```

#### 停止服务

```bash
sudo systemctl stop tplinkCtrl-daemon.service
```

#### 重启服务

```bash
sudo systemctl restart tplinkCtrl-daemon.service
```

## 日志

所有日志都保存在 `log/daemon.log` 中，同时也会输出到控制台。

日志包含：
- 守护进程启动/停止信息
- 配置文件加载状态
- 路由器连接状态
- 定时任务执行结果
- 错误和异常信息

## 配置示例

禁用设备可以按 MAC 地址或设备名称，时间可以用 Cron 表达式灵活定义：

```json
{
  "tasks": [
    {
      "name": "晚间禁用设备",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "action": "block",
      "cron": "0 22 * * *",
      "enabled": true
    }
  ]
}
```

### 示例 1：控制小孩的设备

```json
{
  "tasks": [
    {
      "name": "学习时间禁用设备",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "action": "block",
      "cron": "0 7 * * 1-5",
      "enabled": true,
      "description": "工作日早上7点禁用"
    },
    {
      "name": "放学后启用设备",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "action": "unblock",
      "cron": "0 18 * * 1-5",
      "enabled": true,
      "description": "工作日下午6点启用"
    },
    {
      "name": "夜间禁用设备",
      "device_mac": "AA-AA-AA-AA-AA-AA",
      "action": "block",
      "cron": "0 21 * * *",
      "enabled": true,
      "description": "每天晚上9点禁用"
    }
  ]
}
```

### 示例 2：管理公共设备

```json
{
  "tasks": [
    {
      "name": "工作时间启用Wi-Fi打印机",
      "device_name": "deviceNameXxx",
      "action": "unblock",
      "cron": "0 9 * * 1-5",
      "enabled": true
    },
    {
      "name": "下班后禁用Wi-Fi打印机",
      "device_name": "deviceNameXxx",
      "action": "block",
      "cron": "0 18 * * 1-5",
      "enabled": true
    }
  ]
}
```

## 故障排除

### 守护进程无法启动

1. 检查配置文件语法是否正确
2. 检查路由器连接配置 `config/config.json` 是否正确
3. 查看日志文件 `log/daemon.log` 的错误信息

### 任务未执行

1. 检查 `schedule_config.json` 中任务的 `enabled` 是否为 `true`
2. 检查 Cron 表达式是否正确
3. 检查设备 MAC 地址或名称是否正确
4. 查看日志中是否有错误信息

### 设备控制失败

1. 检查路由器是否在线
2. 检查设备是否真实存在（通过 `python3 main.py` 中的选项 1 查看）
3. 检查路由器登录密码是否正确
