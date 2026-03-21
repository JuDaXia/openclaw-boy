# OpenClaw Gateway 托盘工具

一个简单易用的 Windows 系统托盘工具，用于管理 OpenClaw Gateway 服务。

## ✨ 功能特性

- 🎯 **系统托盘图标**：实时显示 Gateway 运行状态（绿色=运行中，红色=已停止，黄色=操作中）
- 🖱️ **图形化操作界面**：启动、停止、重启 Gateway，无需手动输入命令
- 🌐 **一键打开 Web UI**：快速访问 OpenClaw 控制台
- 🔔 **Windows 通知**：操作完成后自动弹出通知
- 🚀 **开机自启动**：可选择随 Windows 启动自动运行
- 📋 **调试日志**：查看详细的运行日志，方便排查问题
- 🎨 **现代化界面**：深色主题，美观易用

## 📦 安装和使用

### 方式一：直接使用可执行文件（推荐给客户）

1. 从发布页面下载 `OpenClawGateway.exe`
2. 双击运行即可
3. 程序会在系统托盘显示图标
4. 右键点击托盘图标或左键打开控制面板

### 方式二：从源码运行（开发者）

```powershell
# 1. 克隆或下载代码
cd d:\work2\openclawtool

# 2. 安装依赖
pip install -r requirements.txt

# 3. 运行程序
python openclaw_tray.py
```

## 🔨 打包为可执行文件

### 方法一：使用 PyInstaller（更快构建）

```powershell
# 运行构建脚本
build_pyinstaller.bat

# 生成的文件：dist\OpenClawGateway.exe
```

### 方法二：使用 Nuitka（更小体积，推荐）

```powershell
# 运行构建脚本
build_nuitka.bat

# 生成的文件：dist\OpenClawGateway.exe
# 优点：体积更小（约减少 30-50%），启动更快
```

## 📖 使用说明

### 系统托盘菜单

右键点击托盘图标可以看到：

- **打开面板**：显示图形化控制面板
- **启动 Gateway**：启动 OpenClaw Gateway 服务
- **停止 Gateway**：停止服务
- **重启 Gateway**：重启服务
- **打开 Web UI**：在浏览器中打开 http://127.0.0.1:18789
- **查看调试日志**：查看程序运行日志
- **开机自启动**：勾选后程序会随 Windows 启动
- **退出**：关闭托盘工具（不影响 Gateway 运行状态）

### 控制面板

左键点击托盘图标打开控制面板，包含：

- **状态指示器**：显示当前 Gateway 运行状态
- **操作按钮**：
  - ▶ Start：启动服务
  - ■ Stop：停止服务
  - ↺ Restart：重启服务
  - 🌐 Open Web UI：打开网页控制台
  - 📋 View Debug Log：查看日志
- **开机自启动**：复选框控制是否随系统启动
- **消息提示**：显示最近操作的结果

## ⚙️ 工作原理

- **状态检测**：每 8 秒检测一次端口 18789 是否监听
- **命令执行**：通过 `openclaw gateway [start|stop|restart]` 控制服务
- **自启动**：通过 Windows 注册表实现（`HKEY_CURRENT_USER\Software\Microsoft\Windows\CurrentVersion\Run`）
- **通知系统**：使用 Windows 原生通知（需要 winotify 库）

## 🛠️ 技术栈

- **Python 3.8+**
- **Tkinter**：图形界面（Python 标准库）
- **pystray**：系统托盘功能
- **Pillow**：图标生成
- **winotify**：Windows 通知（可选）

## 📝 开发说明

### 项目结构

```
openclawtool/
├── openclaw_tray.py         # 主程序
├── requirements.txt         # Python 依赖
├── build_pyinstaller.bat    # PyInstaller 构建脚本
├── build_nuitka.bat         # Nuitka 构建脚本
├── README_CN.md             # 中文说明文档
└── dist/                    # 构建输出目录
    └── OpenClawGateway.exe  # 可执行文件
```

### 代码改进点

相比原版，新增了以下功能：

1. ✅ **开机自启动**：通过注册表管理，托盘菜单和面板都可以控制
2. ✅ **Windows 通知**：操作成功或失败时弹出通知
3. ✅ **错误处理增强**：更详细的错误提示和日志
4. ✅ **UI 改进**：
   - 操作时按钮自动禁用，防止重复点击
   - 更友好的状态和错误消息（带 ✓ 和 ✗ 标记）
   - 添加了开机自启动复选框
5. ✅ **完整的构建脚本**：支持 PyInstaller 和 Nuitka 两种方式

## 🐛 故障排除

### 程序无法启动
- 确保已经安装了 OpenClaw（`openclaw` 命令可用）
- 以管理员权限运行

### Gateway 启动失败
- 检查端口 18789 是否被占用
- 查看调试日志了解详细错误信息

### 自启动不生效
- 确保程序有写入注册表的权限
- 以管理员权限运行程序

### 通知不显示
- 检查 Windows 通知设置是否启用
- 确保安装了 winotify：`pip install winotify`

## 📄 许可证

本工具为 OpenClaw 的第三方辅助工具，遵循 MIT 许可证。

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📮 联系方式

如有问题或建议，请通过 GitHub Issues 联系。
