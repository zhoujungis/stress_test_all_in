# 压测

嵌入式设备模块化压力测试工具，面向 Glazero 系列设备，提供开关机、RESET、绑定解绑、OTA 升级、休眠唤醒、开流等场景的自动化压测能力。

**版本：** V0.1  
**技术栈：** PyQt6 + Appium + pyserial

---

## 功能特性

- **模块化测试**：按需启用/禁用测试模块，各模块独立配置、并行执行
- **多通道集成**：串口日志采集、继电器电源控制、Appium 移动端自动化、云平台 OTA 下发
- **实时日志与统计**：按模块过滤日志，自动记录串口输出，统计成功/失败次数与耗时
- **配置持久化**：项目信息、模块参数、Appium/云端/继电器设置均可保存与加载

## 测试模块

| 模块 | ID | 说明 |
|------|-----|------|
| 开关机 | `power_cycle` | 通过继电器控制设备电源通断，验证开关机稳定性 |
| RESET | `reset` | 通过 Appium 点击设备复位按钮，验证复位后 App 恢复正常 |
| 绑定解绑 | `bind_unbind` | BLE 扫描绑定 + WiFi 配网 + 解绑，验证绑定流程稳定性 |
| 升级 | `upgrade` | 通过云平台下发 OTA 升级指令，串口验证设备升级状态 |
| 休眠唤醒 | `sleep_wake` | 反复让设备进入休眠并唤醒，验证低功耗模式稳定性 |
| 开流 | `stream_view` | 通过 Appium 打开设备实时画面，验证视频流加载稳定性 |

## 环境要求

- Python 3.10+
- Windows（推荐，串口与继电器控制）
- [Appium Server](https://appium.io/)（绑定解绑、RESET、开流等模块需要）
- Android 测试手机，已安装 Glazero App
- USB 串口线（连接设备 CPU / WiFi 模块）
- 继电器模块（开关机模块需要，可选）

## 安装

```bash
# 克隆仓库
git clone <repo-url>
cd stress_test_all_in

# 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate        # Windows
# source .venv/bin/activate   # Linux / macOS

# 安装依赖
pip install -r requirements.txt
```

### 依赖说明

| 包 | 用途 |
|----|------|
| PyQt6 | 图形界面 |
| pyserial | 串口通信 |
| Appium-Python-Client | Android App 自动化 |
| requests | 云平台 API 调用 |

## 快速开始

### 1. 启动 Appium Server

```bash
appium
```

默认监听 `http://localhost:4723`。

### 2. 启动压测工具

```bash
python main.py
```

### 3. 配置测试环境

在菜单栏 **设置** 中完成以下配置：

| 菜单项 | 配置文件 | 说明 |
|--------|----------|------|
| 项目配置 | `config/project.json` | 项目名称、测试人员、测试时长、联系方式 |
| Appium 设置 | `config/appium.json` | Appium 地址、平台、App 包名与 Activity |
| 云端设置 | `config/cloud.json` | 云平台账号、密码、区域 |
| 继电器设置 | `config/relay.json` | 继电器串口、通道数、开关命令 |

### 4. 配置测试模块

1. **模块 → 模块管理**：勾选本次要运行的模块
2. **模块 → 模块配置**：为每个模块设置串口、循环次数、超时等参数
3. 各模块配置自动保存至 `config/modules/<module_id>.json`

### 5. 运行压测

- 按 **F5** 或选择 **运行 → 开始压测**
- 按 **Esc** 或选择 **运行 → 停止** 中止测试
- 通过 **查看** 菜单按模块过滤日志输出

## 快捷键

| 快捷键 | 功能 |
|--------|------|
| F5 | 开始压测 |
| Esc | 停止压测 |
| Ctrl+S | 保存配置 |
| Ctrl+O | 加载配置 |

## 项目结构

```
stress_test_all_in/
├── main.py                 # 程序入口
├── requirements.txt        # Python 依赖
├── config/                 # 配置文件目录
│   ├── project.json        # 项目信息
│   ├── appium.json         # Appium 连接配置
│   ├── cloud.json          # 云平台配置
│   ├── relay.json          # 继电器配置
│   └── modules/            # 各模块参数
├── core/                   # 核心逻辑
│   ├── test_runner.py      # 测试调度与线程池
│   ├── test_context.py     # 共享上下文（Appium/云端/继电器）
│   ├── config_manager.py   # 配置读写
│   ├── appium_client.py    # Appium 客户端
│   ├── cloud_client.py     # 云平台客户端
│   ├── relay_manager.py    # 继电器控制
│   ├── serial_manager.py   # 串口管理
│   └── metrics.py            # 统计数据聚合
├── modules/                # 测试模块实现
│   ├── base.py             # 模块基类
│   ├── power_cycle.py
│   ├── reset.py
│   ├── bind_unbind.py
│   ├── upgrade.py
│   ├── sleep_wake.py
│   └── stream_view.py
├── workers/                # 后台工作线程
│   ├── module_worker.py    # 单模块执行
│   └── stats_worker.py       # 统计刷新
└── ui/                     # PyQt6 界面
    ├── main_window.py      # 主窗口
    ├── log_panel.py        # 日志面板
    └── ...                 # 各配置对话框
```

## 扩展新模块

1. 在 `modules/` 下新建模块类，继承 `BaseTestModule`
2. 实现 `create_config_widget`、`get_config`、`set_default_config`、`run` 四个方法
3. 在 `modules/__init__.py` 的 `_registry` 中注册模块 ID
4. 在 `config/modules/` 下添加对应的默认 JSON 配置

## 日志

测试日志按 **项目名-测试人员** 命名，保存在 `logs/` 目录下，按模块分子目录存放。界面右侧可查看各模块的成功/失败统计与耗时分析。

## 注意事项

- 运行压测前请确认串口、继电器、Appium 均已正确连接
- 绑定解绑、开流等模块依赖 Appium 与测试手机，请确保 App 已登录且设备在线
- 升级模块需配置有效的云平台账号与设备 SN
- 配置文件中的账号密码等敏感信息请勿提交至版本控制

## 联系方式

- 邮箱：zhoujun@glazero.com

## 版权

© 2025 深圳市致翎科技有限公司（Glazero (Shenzhen) Co., Ltd.）

本工具仅限内部测试使用，未经授权不得复制、分发或用于商业目的。
