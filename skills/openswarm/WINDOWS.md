# Windows 安装指南

本文档为 Windows 用户提供详细的安装步骤。

---

## 前提条件

- **操作系统**：Windows 10 或 Windows 11
- **管理员权限**：需要管理员权限安装某些软件
- **网络连接**：需要下载软件和依赖

---

## 第 1 步：安装 OpenClaw

### 方法 1：使用 npm（推荐）

#### 1.1 安装 Node.js 和 npm

1. 访问 https://nodejs.org/
2. 下载 LTS 版本（推荐）
3. 运行安装程序，一路"下一步"
4. 安装完成后，打开 PowerShell 或命令提示符

#### 1.2 验证安装

```powershell
# 验证 Node.js
node --version

# 验证 npm
npm --version
```

#### 1.3 安装 OpenClaw

```powershell
# 使用 npm 安装 OpenClaw
npm install -g openclaw

# 验证安装
openclaw --version
```

### 方法 2：使用 Chocolatey

#### 1.1 安装 Chocolatey

以**管理员身份**运行 PowerShell：

```powershell
# 设置执行策略
Set-ExecutionPolicy Bypass -Scope Process -Force

# 安装 Chocolatey
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))
```

#### 1.2 安装 OpenClaw

```powershell
# 使用 Chocolatey 安装
choco install openclaw -y

# 验证安装
openclaw --version
```

---

## 第 2 步：安装 Git

### 检查 Git 是否已安装

```powershell
git --version
```

### 安装 Git

1. 访问 https://git-scm.com/download/win
2. 下载 Windows 版本
3. 运行安装程序：
   - 选择安装路径（默认：`C:\Program Files\Git`）
   - 选择组件（全部勾选）
   - 选择默认编辑器（推荐 VS Code）
   - PATH 环境设置：选择 "Git from the command line and also from 3rd-party software"
   - 其他选项保持默认
4. 安装完成后，重新打开 PowerShell 或命令提示符

### 验证 Git

```powershell
git --version
# 应该显示 git version x.x.x.windows.x
```

### 配置 Git（可选但推荐）

```powershell
# 配置用户名
git config --global user.name "Your Name"

# 配置邮箱
git config --global user.email "your.email@example.com"
```

---

## 第 3 步：安装 Docker Desktop

### 为什么需要 Docker？

ChromaDB 推荐使用 Docker 运行，这是最简单的方式。

### 检查 Docker 是否已安装

```powershell
docker --version
```

### 安装 Docker Desktop for Windows

1. 访问 https://www.docker.com/products/docker-desktop/
2. 点击 "Download for Windows"
3. 下载 Docker Desktop Installer.exe
4. 运行安装程序，一路"下一步"
5. 安装完成后，重启电脑
6. 启动 Docker Desktop
7. Docker Desktop 会自动启动并显示在系统托盘

### 验证 Docker

```powershell
# 检查 Docker 版本
docker --version

# 检查 Docker 是否运行
docker ps

# 测试 Docker
docker run hello-world
```

### 配置 Docker（可选）

1. 打开 Docker Desktop
2. 点击右上角齿轮图标（Settings）
3. 调整资源限制（根据你的电脑配置）：
   - CPUs：至少 2 个
   - Memory：至少 4 GB
4. 点击 "Apply & Restart"

---

## 第 4 步：安装 ChromaDB

### 方法 1：使用 Docker（推荐）

#### 启动 ChromaDB

```powershell
# 拉取并运行 ChromaDB
docker run -d -p 8000:8000 --name openswarm-chromadb chromadb/chroma

# 验证运行
docker ps

# 应该看到 openswarm-chromadb 容器正在运行
```

#### 验证 ChromaDB

```powershell
# 使用 PowerShell 测试
Invoke-RestMethod -Uri http://localhost:8000/api/v1/heartbeat

# 或使用 curl（如果安装了 Git for Windows，curl 也可以用）
curl http://localhost:8000/api/v1/heartbeat

# 预期输出：{"nanosecond_bucket_bounds":null,"status":"ok"}
```

### 方法 2：使用 Python（不推荐，但可用）

#### 安装 Python

1. 访问 https://www.python.org/downloads/
2. 下载 Windows 版本
3. 运行安装程序：
   - **重要**：勾选 "Add Python to PATH"
   - 点击 "Install Now"
4. 安装完成后，重新打开 PowerShell

#### 验证 Python

```powershell
python --version
# 应该显示 Python 3.x.x

pip --version
# 应该显示 pip x.x.x
```

#### 安装并运行 ChromaDB

```powershell
# 安装 ChromaDB
pip install chromadb

# 启动 ChromaDB 服务器
chroma-server --host 0.0.0.0 --port 8000

# 在另一个 PowerShell 窗口中验证
curl http://localhost:8000/api/v1/heartbeat
```

---

## 第 5 步：安装 Waza Skill

### 检查 Waza 是否已安装

```powershell
# 检查 Waza skill 目录
Test-Path "$env:USERPROFILE\.npm-global\node_modules\openclaw\skills\waza\SKILL.md"
```

### 安装 Waza

```powershell
# 使用 npm 安装
npm install -g waza-skills

# 验证安装
Test-Path "$env:USERPROFILE\.npm-global\node_modules\openclaw\skills\waza\SKILL.md"
```

---

## 第 6 步：克隆项目并安装

### 克隆项目

```powershell
# 克隆项目到桌面（或其他你喜欢的位置）
git clone https://github.com/fuguier001/openswarm-lobster-version.git $env:USERPROFILE\Desktop\openswarm-lobster-version

# 进入项目目录
cd $env:USERPROFILE\Desktop\openswarm-lobster-version
```

### 运行安装脚本

**注意**：Windows 用户不能直接运行 `.sh` 脚本。需要使用 Git Bash 或手动安装。

#### 方法 1：使用 Git Bash（推荐）

1. 打开项目文件夹
2. 右键点击空白处，选择 "Git Bash Here"
3. 运行安装脚本：

```bash
chmod +x install.sh
./install.sh
```

#### 方法 2：手动安装（如果没有 Git Bash）

```powershell
# 检查 OpenClaw 安装目录
Test-Path "$env:USERPROFILE\.agents\skills"

# 创建 skills 目录（如果不存在）
New-Item -ItemType Directory -Path "$env:USERPROFILE\.agents\skills" -Force

# 复制 skills
Copy-Item -Recurse -Force "skills\pair-coding" "$env:USERPROFILE\.agents\skills\"
Copy-Item -Recurse -Force "skills\code-registry" "$env:USERPROFILE\.agents\skills\"
Copy-Item -Recurse -Force "skills\cognitive-memory" "$env:USERPROFILE\.agents\skills\"

# 创建 workspace 目录（如果不存在）
New-Item -ItemType Directory -Path "$env:USERPROFILE\.openclaw\workspace" -Force

# 复制 HEARTBEAT 配置
Copy-Item -Force "HEARTBEAT.md" "$env:USERPROFILE\.openclaw\workspace\HEARTBEAT.md"
```

---

## 第 7 步：验证安装

### 验证 Skills

```powershell
# 检查 pair-coding
Test-Path "$env:USERPROFILE\.agents\skills\pair-coding\SKILL.md"

# 检查 code-registry
Test-Path "$env:USERPROFILE\.agents\skills\code-registry\SKILL.md"

# 检查 cognitive-memory
Test-Path "$env:USERPROFILE\.agents\skills\cognitive-memory\SKILL.md"
```

### 验证 HEARTBEAT 配置

```powershell
# 检查 HEARTBEAT 配置
Test-Path "$env:USERPROFILE\.openclaw\workspace\HEARTBEAT.md"

# 查看内容
Get-Content "$env:USERPROFILE\.openclaw\workspace\HEARTBEAT.md"
```

### 验证 ChromaDB

```powershell
# 验证 ChromaDB 是否运行
docker ps | Select-String "openswarm-chromadb"

# 验证 ChromaDB 连接
Invoke-RestMethod -Uri http://localhost:8000/api/v1/heartbeat
```

### 验证 Waza

```powershell
# 检查 Waza skill
Test-Path "$env:USERPROFILE\.npm-global\node_modules\openclaw\skills\waza\SKILL.md"

# 查看 Waza 内容
Get-Content "$env:USERPROFILE\.npm-global\node_modules\openclaw\skills\waza\SKILL.md"
```

---

## 第 8 步：重启 OpenClaw

重启 OpenClaw 让新安装的 skills 生效。

---

## 第 9 步：开始使用

直接与 OpenClaw 对话：

```
你：帮我写一个用户认证系统
你：扫描我的项目，检查代码质量
你：搜索我之前提到的 Docker 配置
```

---

## Windows 常见问题

### Q: PowerShell 提示"无法加载文件，因为在此系统上禁止运行脚本"？

A: 这是 PowerShell 的执行策略限制。解决方法：

```powershell
# 以管理员身份运行 PowerShell
Set-ExecutionPolicy RemoteSigned -Scope CurrentUser
```

### Q: Docker Desktop 无法启动？

A: 检查：
1. 是否启用了 WSL 2
2. 是否启用了虚拟化
3. Windows 版本是否支持

详细解决方法：https://docs.docker.com/desktop/troubleshoot/

### Q: Git Bash 在哪里？

A: 如果你安装了 Git for Windows，Git Bash 通常在以下位置：
- 开始菜单 → Git → Git Bash
- 或右键点击文件夹 → "Git Bash Here"

### Q: 端口 8000 被占用？

A: 如果端口 8000 被其他程序占用：

```powershell
# 查看端口占用
netstat -ano | findstr :8000

# 停止占用端口的进程（需要 PID）
taskkill /PID <PID> /F

# 或使用其他端口运行 ChromaDB
docker run -d -p 8001:8000 --name openswarm-chromadb chromadb/chroma
```

### Q: npm 安装速度慢？

A: 使用国内镜像：

```powershell
# 使用淘宝镜像
npm config set registry https://registry.npmmirror.com

# 恢复官方源
npm config set registry https://registry.npmjs.org
```

### Q: 如何卸载？

A: 删除安装的文件：

```powershell
# 删除 skills
Remove-Item -Recurse -Force "$env:USERPROFILE\.agents\skills\pair-coding"
Remove-Item -Recurse -Force "$env:USERPROFILE\.agents\skills\code-registry"
Remove-Item -Recurse -Force "$env:USERPROFILE\.agents\skills\cognitive-memory"

# 删除配置
Remove-Item -Force "$env:USERPROFILE\.openclaw\workspace\HEARTBEAT.md"

# 停止并删除 ChromaDB
docker stop openswarm-chromadb
docker rm openswarm-chromadb
```

---

## Windows 特定提示

### 1. 路径分隔符

Windows 使用反斜杠 `\`，但大多数命令可以接受正斜杠 `/`。

### 2. 管理员权限

某些操作需要管理员权限，建议以管理员身份运行 PowerShell。

### 3. 防火墙

首次运行 Docker 或 ChromaDB 时，Windows 防火墙可能会提示，请允许访问。

### 4. 路径中的空格

如果路径包含空格，使用引号包裹：

```powershell
# 正确
cd "C:\Program Files\Git"

# 错误
cd C:\Program Files\Git
```

---

## 下一步

- 查看 [README.md](README.md) 了解项目详情
- 查看 [USAGE.md](USAGE.md) 了解使用方法
- 查看 [QUICKSTART.md](QUICKSTART.md) 了解快速开始

---

## 获取帮助

- GitHub Issues: https://github.com/fuguier001/openswarm-lobster-version/issues
- Docker 文档: https://docs.docker.com/desktop/windows/
- Git 文档: https://git-scm.com/book/zh/v2/开始

---

**🌊 Happy Coding with OpenSwarm 龙虾版！**
