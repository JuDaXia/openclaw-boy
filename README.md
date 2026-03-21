# OpenClaw-Boy

OpenClaw Gateway 图形化管理工具。无需输入命令行，双击即可管理 OpenClaw Gateway 服务。

## 功能

- **系统托盘图标** — 实时显示 Gateway 状态（🟢运行中 🔴已停止 🟡处理中）
- **控制面板** — 启动 / 停止 / 重启 Gateway，一键打开网页控制台
- **开机自启动** — 可选随 Windows 启动自动运行
- **Windows 通知** — 操作完成后弹出系统通知
- **调试日志** — 查看详细运行日志，方便排查问题
- **智能启动** — 自动处理服务安装、权限不足、端口占用等问题

## 安装使用

### 前置条件

- Windows 10 或更高版本
- 已安装 OpenClaw：
  ```powershell
  powershell -c "irm https://openclaw.ai/install.ps1 | iex"
  ```

### 下载运行

1. 从 [Releases](https://github.com/JuDaXia/openclaw-boy/releases) 页面下载 `OpenClawBoy.exe`
2. 双击运行（首次可能弹出安全提示，点击「更多信息」→「仍要运行」）
3. 在系统托盘（屏幕右下角）找到圆形图标
4. **左键** 点击图标打开控制面板，**右键** 点击显示菜单

### 控制面板

| 按钮 | 功能 |
|------|------|
| ▶ 启动 | 启动 Gateway 服务 |
| ■ 停止 | 停止 Gateway 服务 |
| ↺ 重启 | 重启 Gateway 服务 |
| 🌐 打开网页控制台 | 浏览器打开 http://127.0.0.1:18789 |
| 📋 查看调试日志 | 查看运行日志 |

### 托盘右键菜单

- 打开控制面板
- 启动 / 停止 / 重启 Gateway
- 打开网页控制台
- 查看调试日志
- 开机自动启动（勾选启用）
- 退出

## 从源码运行

```bash
# 安装依赖
pip install -r requirements.txt

# 运行
python openclaw_tray.py
```

## 打包

```bash
# 安装打包工具
pip install pyinstaller

# 打包为单个 exe
pyinstaller --onefile --windowed --name "OpenClawBoy" --uac-admin --clean openclaw_tray.py
```

生成文件：`dist/OpenClawBoy.exe`

## 常见问题

**Q: 双击后没有窗口出现？**
正常。程序启动后在系统托盘显示图标，左键点击即可打开面板。

**Q: 启动 Gateway 失败？**
右键图标 → 查看调试日志，确认 OpenClaw 已安装（终端运行 `openclaw` 测试）。

**Q: 如何卸载？**
取消「开机自动启动」→ 点击「退出」→ 删除 exe 文件。

## 技术栈

- Python 3.8+
- Tkinter（GUI）
- pystray（系统托盘）
- Pillow（图标生成）
- winotify（Windows 通知）

## License

MIT
