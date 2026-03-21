# OpenClaw Gateway 托盘工具 - 部署指南

## 📋 部署前准备清单

### 开发环境要求
- ✅ Python 3.8 或更高版本
- ✅ Windows 10 或更高版本
- ✅ 管理员权限（用于打包和测试）

### 客户环境要求
- ✅ Windows 10 或更高版本
- ✅ 已安装 OpenClaw（通过官方安装命令）
- ✅ 无需安装 Python（打包后为独立可执行文件）

---

## 🔨 构建步骤

### 步骤 1：安装开发依赖

```powershell
# 进入项目目录
cd d:\work2\openclawtool

# 安装依赖
pip install -r requirements.txt
```

### 步骤 2：测试程序

```powershell
# 运行测试脚本
test_run.bat

# 或直接运行
python openclaw_tray.py
```

**测试检查项：**
- [ ] 托盘图标是否显示
- [ ] 左键点击能否打开面板
- [ ] 右键菜单是否正常
- [ ] 启动/停止/重启功能
- [ ] 状态检测是否准确（8秒轮询）
- [ ] 开机自启动开关
- [ ] 调试日志窗口
- [ ] Windows 通知

### 步骤 3：选择构建方式

#### 方式 A：PyInstaller（推荐 - 快速构建）

```powershell
# 运行构建脚本
build_pyinstaller.bat

# 构建时间：约 30-60 秒
# 文件大小：约 15-25 MB
# 输出位置：dist\OpenClawGateway.exe
```

#### 方式 B：Nuitka（推荐 - 优化体积）

```powershell
# 运行构建脚本
build_nuitka.bat

# 构建时间：约 3-10 分钟（首次构建）
# 文件大小：约 8-15 MB
# 输出位置：dist\OpenClawGateway.exe
```

**性能对比：**
```
┌─────────────┬──────────────┬──────────┬──────────┐
│   构建工具   │   文件大小   │ 启动速度 │ 构建时间 │
├─────────────┼──────────────┼──────────┼──────────┤
│ PyInstaller │  15-25 MB    │   正常   │   快     │
│ Nuitka      │   8-15 MB    │   更快   │   慢     │
└─────────────┴──────────────┴──────────┴──────────┘
```

### 步骤 4：测试可执行文件

```powershell
# 运行生成的 exe
dist\OpenClawGateway.exe

# 测试所有功能（同步骤 2）
```

---

## 📦 打包发布

### 创建发布包

建议的文件夹结构：

```
OpenClawGateway_v1.0/
├── OpenClawGateway.exe     # 主程序
├── 安装使用指南.pdf         # INSTALL_CN.md 转成 PDF
└── README.txt              # 简要说明
```

**README.txt 示例：**
```
OpenClaw Gateway 托盘工具 v1.0
================================

使用方法：
1. 双击 OpenClawGateway.exe 运行
2. 在系统托盘（右下角）找到图标
3. 左键点击打开控制面板

详细说明请查看"安装使用指南.pdf"

技术支持：[你的联系方式]
```

### 压缩和分发

```powershell
# 压缩为 ZIP 文件
Compress-Archive -Path "OpenClawGateway_v1.0" -DestinationPath "OpenClawGateway_v1.0.zip"

# 或使用 7-Zip 等工具压缩
```

---

## 🚀 客户端部署

### 远程部署方案

#### 方案 A：手动部署
1. 将 `OpenClawGateway.exe` 通过 U盘/网盘/邮件发送给客户
2. 指导客户保存到合适位置
3. 指导客户双击运行
4. 远程协助勾选"开机自启动"

#### 方案 B：批量部署脚本

创建 `deploy.bat`：
```batch
@echo off
REM 自动部署脚本

echo 正在部署 OpenClaw Gateway 托盘工具...

REM 创建程序目录
set INSTALL_DIR=C:\Program Files\OpenClawGateway
if not exist "%INSTALL_DIR%" mkdir "%INSTALL_DIR%"

REM 复制文件
copy /Y OpenClawGateway.exe "%INSTALL_DIR%\"

REM 创建桌面快捷方式（可选）
echo Set oWS = WScript.CreateObject("WScript.Shell") > CreateShortcut.vbs
echo sLinkFile = "%USERPROFILE%\Desktop\OpenClaw Gateway.lnk" >> CreateShortcut.vbs
echo Set oLink = oWS.CreateShortcut(sLinkFile) >> CreateShortcut.vbs
echo oLink.TargetPath = "%INSTALL_DIR%\OpenClawGateway.exe" >> CreateShortcut.vbs
echo oLink.Save >> CreateShortcut.vbs
cscript CreateShortcut.vbs
del CreateShortcut.vbs

REM 启动程序
start "" "%INSTALL_DIR%\OpenClawGateway.exe"

echo 部署完成！
echo 请在系统托盘找到图标。
pause
```

#### 方案 C：PowerShell 远程部署

```powershell
# deploy.ps1
$installPath = "C:\Program Files\OpenClawGateway"

# 创建目录
New-Item -ItemType Directory -Force -Path $installPath

# 下载文件（如果托管在服务器上）
# Invoke-WebRequest -Uri "http://yourserver.com/OpenClawGateway.exe" -OutFile "$installPath\OpenClawGateway.exe"

# 或复制本地文件
Copy-Item "OpenClawGateway.exe" -Destination $installPath -Force

# 启动程序
Start-Process "$installPath\OpenClawGateway.exe"

Write-Host "部署完成！" -ForegroundColor Green
```

---

## ✅ 部署后检查

### 客户端检查清单

**第一次运行：**
- [ ] 系统托盘是否出现图标
- [ ] 图标颜色是否正确（绿色/红色）
- [ ] 左键点击能否打开面板
- [ ] 右键菜单是否正常

**功能测试：**
- [ ] 点击"启动"按钮，Gateway 是否成功启动
- [ ] 状态指示器是否变为"Running"
- [ ] 图标是否变为绿色
- [ ] 点击"打开 Web UI"能否访问
- [ ] Windows 通知是否弹出

**自启动测试：**
- [ ] 勾选"Start with Windows"
- [ ] 重启电脑
- [ ] 登录后程序是否自动运行
- [ ] Gateway 是否自动启动（如果之前是运行状态）

---

## 🐛 常见部署问题

### 问题 1：exe 被杀毒软件拦截

**原因：** PyInstaller/Nuitka 打包的程序可能被误报

**解决方案：**
1. 向杀毒软件添加信任/白名单
2. 联系杀毒软件厂商申请误报处理
3. 使用数字签名（需要购买代码签名证书）

### 问题 2：无法写入注册表（自启动失败）

**原因：** 权限不足

**解决方案：**
1. 右键 exe → "以管理员身份运行"
2. 在打包脚本中添加 `--uac-admin` 参数（已包含）

### 问题 3：找不到 openclaw 命令

**原因：** OpenClaw 未安装或不在 PATH 中

**解决方案：**
1. 确认客户已运行官方安装命令
2. 在 PowerShell 中测试：`openclaw --version`
3. 如果不行，重新运行安装命令

### 问题 4：端口 18789 被占用

**原因：** 其他程序占用端口

**解决方案：**
```powershell
# 查看端口占用
netstat -ano | findstr :18789

# 结束占用进程（记下 PID）
taskkill /PID <进程ID> /F
```

---

## 📊 部署统计建议

建议在程序中添加（可选）：
- 使用次数统计
- 错误日志收集
- 自动更新检查

---

## 🔄 更新和维护

### 版本更新流程

1. 修改代码
2. 更新版本号（在代码中添加 `VERSION = "1.1.0"`）
3. 重新构建 exe
4. 测试新版本
5. 发布给客户
6. 客户下载新 exe 替换旧文件

### 日志收集

如果客户遇到问题，让他们：
1. 右键托盘图标 → "View Debug Log"
2. 点击"Refresh"刷新日志
3. 复制或截图发送给你

---

## 📞 技术支持建议

**准备一份常见问题文档（FAQ）**，包含：
- 如何安装
- 如何卸载
- 如何设置自启动
- 如何查看日志
- 常见错误代码和解决方法

**提供多种联系方式：**
- 电话
- 邮件
- 企业微信/钉钉
- 远程协助工具（TeamViewer/向日葵）

---

## 🎯 推荐部署流程

**最佳实践：**

1. **内部测试阶段**（1-2天）
   - 在虚拟机/测试机上完整测试
   - 模拟客户环境

2. **小规模试点**（3-5个客户）
   - 选择技术能力较强的客户
   - 收集反馈和问题

3. **优化改进**（根据反馈）
   - 修复 bug
   - 改进用户体验

4. **正式部署**
   - 批量发送给所有客户
   - 提供技术支持

5. **持续维护**
   - 定期收集使用情况
   - 版本迭代更新

---

## ✨ 可选增强功能

如果客户有更多需求，可以考虑添加：

- [ ] 自动更新功能
- [ ] 使用统计报告
- [ ] 远程管理接口
- [ ] 多语言支持
- [ ] 主题切换（深色/浅色）
- [ ] 更详细的配置选项
- [ ] 崩溃报告自动上传

---

祝部署顺利！🎉
