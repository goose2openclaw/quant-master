# 🌊 OpenSwarm 龙虾版

> 将 OpenSwarm 的核心模式改造为 OpenClaw Skills，一条命令安装，立即使用

[![OpenClaw](https://img.shields.io/badge/OpenClaw-compatible-green.svg)](https://docs.openclaw.ai)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 💻 操作系统选择

请根据你的操作系统选择安装方式：

- **macOS**：参考下面的完整安装指南
- **Linux (Ubuntu/Debian)**：参考下面的完整安装指南
- **Windows**：📖 **[查看 Windows 专用安装指南](WINDOWS.md)** ⚠️

**⚠️ Windows 用户注意**：
Windows 的安装过程与 macOS/Linux 有所不同，包括：
- 安装 Docker Desktop for Windows（不是普通的 Docker）
- PowerShell 命令和权限配置
- 路径和空格处理
- Git Bash 的使用

**Windows 用户请直接查看 [WINDOWS.md](WINDOWS.md) 获取完整的 9 步安装流程和常见问题解答。**

---

## 📖 什么是 OpenSwarm？

OpenSwarm 是一个 **AI 开发团队编排系统**，通过 Worker/Reviewer 对模式、代码注册表、认知记忆等核心功能，提升代码质量、开发效率和知识管理能力。

**核心功能**：
- 🤝 **pair-coding**：Worker/Reviewer 对模式，自动进行安全检查和性能验证
- 🔍 **code-registry**：代码注册表，检测坏代码模式，计算复杂度
- 🧠 **cognitive-memory**：认知记忆系统，智能检索历史信息，跨会话知识复用
- 🤖 **automation**：自动化集成，定时任务，自动检查和报告

**依赖关系**：
- ⚠️ pair-coding：需要 Waza skill（工程习惯技能库）
- ✅ code-registry：无需额外依赖
- ⚠️ cognitive-memory：需要 ChromaDB

**重要说明**：
- Waza skill 是 OpenClaw 的标准 skill，**不包含在本项目中**
- 需要单独安装 Waza skill
- Waza 项目地址：https://github.com/tw93/Waza

---

## 💻 Windows 用户

**Windows 用户的安装过程与 macOS/Linux 有所不同**，包括：
- 安装 Docker Desktop for Windows
- PowerShell 命令和权限配置
- 路径和空格处理
- Git Bash 的使用

**详细的 Windows 安装指南**：📖 [WINDOWS.md](WINDOWS.md)

包含完整的 9 步安装流程：
1. 安装 OpenClaw（npm 或 Chocolatey）
2. 安装 Git for Windows
3. 安装 Docker Desktop for Windows
4. 安装 ChromaDB（Docker 或 Python）
5. 安装 Waza Skill
6. 克隆项目并安装
7. 验证安装
8. 重启 OpenClaw
9. 开始使用

以及 Windows 特定的常见问题解答。

---

---

## 🦀 为什么是"龙虾版"？

电脑里养了太多虾（OpenClaw 的 AI 助手称为"虾"），如果只是某个模式好一些，完全没必要再安装新的虾。因此决定将 OpenSwarm 的核心功能改造为 OpenClaw 的插件（Skills），在不增加新虾的情况下，获得 OpenSwarm 的所有能力。

**优势**：
- ✅ 无需安装新的 AI 助手
- ✅ 复用现有的 ChromaDB 向量数据库
- ✅ 无缝集成到 OpenClaw
- ✅ 一条命令安装
- ✅ 性能不打折

---

## 🚀 完整安装指南（新电脑）

**⚠️ 重要提示**：

- **macOS/Linux 用户**：按照下面的步骤进行安装
- **Windows 用户**：请直接查看 **[WINDOWS.md](WINDOWS.md)** 获取详细的 Windows 专用安装指南

下面的安装指南主要针对 macOS 和 Linux 用户。

---

### 第 1 步：检查/安装 OpenClaw

**如果你已经安装了 OpenClaw，跳过此步骤。**

#### 检查 OpenClaw 是否已安装

```bash
# 检查 OpenClaw 命令
openclaw --version

# 检查 OpenClaw 安装目录
ls ~/.openclaw
```

如果命令执行成功，说明 OpenClaw 已安装。

#### 安装 OpenClaw

```bash
# 使用 npm 安装
npm install -g openclaw

# 验证安装
openclaw --version
```

**OpenClaw 文档**：https://docs.openclaw.ai

---

### 第 2 步：安装依赖

**⚠️ Windows 用户**：
Windows 用户的依赖安装过程（Git、Docker、Python）与 macOS/Linux 有所不同，请查看 **[WINDOWS.md](WINDOWS.md)** 获取详细的安装步骤。

---

#### 2.1 安装 Git（如果未安装）

**检查 Git：**
```bash
git --version
```

**安装 Git：**

- **macOS**：
  ```bash
  # 通常已预装
  # 如果没有，使用 Homebrew
  brew install git
  ```

- **Linux (Ubuntu/Debian)**：
  ```bash
  sudo apt update
  sudo apt install git
  ```

- **Windows**：
  下载并安装：https://git-scm.com/download/win

#### 2.2 安装 Docker（推荐）

**检查 Docker：**
```bash
docker --version
docker ps
```

**安装 Docker：**

- **macOS**：
  下载 Docker Desktop：https://www.docker.com/products/docker-desktop/

- **Linux (Ubuntu/Debian)**：
  ```bash
  curl -fsSL https://get.docker.com -o get-docker.sh
  sudo sh get-docker.sh
  sudo usermod -aG docker $USER
  ```

- **Windows**：
  下载 Docker Desktop：https://www.docker.com/products/docker-desktop/
  **详细安装指南**：见 [WINDOWS.md](WINDOWS.md)

**启动 Docker：**
```bash
# macOS/Windows：启动 Docker Desktop 应用

# Linux：
sudo systemctl start docker
sudo systemctl enable docker
```

**验证 Docker：**
```bash
docker run hello-world
```

#### 2.3 可选：安装 Python（如果不想用 Docker）

**检查 Python：**
```bash
python3 --version
```

**安装 Python：**

- **macOS**：
  ```bash
  brew install python3
  ```

- **Linux (Ubuntu/Debian)**：
  ```bash
  sudo apt update
  sudo apt install python3 python3-pip
  ```

- **Windows**：
  下载并安装：https://www.python.org/downloads/

---

### 第 2.5 步：安装 Waza Skill（必需）

**什么是 Waza？**

Waza (技) 是一个工程习惯技能库，包含 8 个核心技能：
- **think** - 设计验证
- **design** - UI 设计
- **check** - 代码审查 ⚠️ pair-coding 需要
- **hunt** - 系统调试
- **write** - 自然写作
- **learn** - 深度研究
- **read** - 内容获取
- **health** - 配置审计

**Waza 项目地址**：https://github.com/tw93/Waza

**注意**：Waza skill **不包含在本项目中**，需要单独安装。

#### 检查 Waza 是否已安装

```bash
# 检查 Waza skill
ls ~/.npm-global/lib/node_modules/openclaw/skills/waza/SKILL.md

# 或查看 OpenClaw skills 列表
openclaw skills list | grep waza
```

如果命令执行成功，说明 Waza 已安装。

#### 安装 Waza

**方法 1：使用 npm（推荐）**

```bash
# 安装 Waza skill
npm install -g waza-skills

# 验证安装
ls ~/.npm-global/lib/node_modules/openclaw/skills/waza/SKILL.md
```

**方法 2：从源码安装**

```bash
# 克隆 Waza 仓库
git clone https://github.com/tw93/Waza.git

# 安装 Waza
cd Waza
npm install
npm link

# 验证安装
ls ~/.npm-global/lib/node_modules/openclaw/skills/waza/SKILL.md
```

#### 验证 Waza

```bash
# 检查 Waza skill 文件
cat ~/.npm-global/lib/node_modules/openclaw/skills/waza/SKILL.md

# 应该看到 Waza 的描述和 8 个核心技能
```

**如果 Waza 未安装，pair-coding skill 会无法进行代码审查。**

---

### 第 3 步：安装 ChromaDB

#### 方法 1：使用 Docker（推荐）

```bash
# 拉取并运行 ChromaDB
docker run -d -p 8000:8000 --name openswarm-chromadb chromadb/chroma

# 验证运行
curl http://localhost:8000/api/v1/heartbeat

# 预期输出：{"nanosecond_bucket_bounds":null,"status":"ok"}
```

#### 方法 2：使用 Python

```bash
# 安装 ChromaDB
pip3 install chromadb

# 启动 ChromaDB 服务器
chroma-server --host 0.0.0.0 --port 8000

# 在另一个终端验证
curl http://localhost:8000/api/v1/heartbeat
```

#### 方法 3：使用我们的安装脚本

```bash
# 克隆项目后运行
chmod +x install-chromadb.sh
./install-chromadb.sh
```

---

### 第 4 步：克隆项目并安装

```bash
# 1. 克隆项目
git clone https://github.com/fuguier001/openswarm-lobster-version.git
cd openswarm-lobster-version

# 2. 运行安装脚本
chmod +x install.sh
./install.sh
```

**安装脚本会自动：**
- ✅ 检查 OpenClaw 安装目录
- ✅ 检查 Waza skill
- ✅ 检查 ChromaDB 状态
- ✅ 安装 3 个 skills
- ✅ 配置 HEARTBEAT
- ✅ 显示每个 skill 的依赖状态

---

### 第 5 步：验证安装

```bash
# 1. 检查 skills 是否安装成功
ls ~/.agents/skills/pair-coding
ls ~/.agents/skills/code-registry
ls ~/.agents/skills/cognitive-memory

# 2. 检查 HEARTBEAT 配置
cat ~/.openclaw/workspace/HEARTBEAT.md

# 3. 检查 ChromaDB（如果使用）
curl http://localhost:8000/api/v1/heartbeat

# 4. 检查 Waza（如果使用）
ls ~/.npm-global/lib/node_modules/openclaw/skills/waza/SKILL.md
```

---

### 第 6 步：重启 OpenClaw

重启 OpenClaw 让新安装的 skills 生效。

---

### 第 7 步：开始使用

直接与 OpenClaw 对话：

```
你：帮我写一个用户认证系统
你：扫描我的项目，检查代码质量
你：搜索我之前提到的 Docker 配置
```

---

## 🎯 核心功能

### 1. pair-coding - Worker/Reviewer 对模式

**用途**：生成代码时自动进行安全检查和性能验证

**依赖**：Waza skill（check skill）

**使用**：
```
你：帮我写一个用户认证系统
```

**效果**：
- ✅ Worker 生成代码
- ✅ Reviewer 审查代码
- ✅ 安全检查 100% 有效
- ✅ 性能验证 100% 有效
- ✅ 平均 1.5 次迭代完成

---

### 2. code-registry - 代码注册表

**用途**：扫描代码库，检测坏代码模式，计算复杂度

**依赖**：无

**使用**：
```
你：扫描我的项目，检查代码质量
```

**效果**：
- ✅ BS 检测准确率 100%
- ✅ 复杂度评分 0-100
- ✅ 支持多语言（JS, Python, Java）
- ✅ 自动排除 node_modules

**BS 问题分级**：
- 🔴 **CRITICAL**：硬编码密钥、安全问题
- 🟠 **HIGH**：空 catch 块、console.log
- 🟡 **MEDIUM**：参数过多、函数过长
- 🟢 **LOW**：未使用的变量

---

### 3. cognitive-memory - 认知记忆

**用途**：智能检索历史信息，跨会话知识复用

**依赖**：ChromaDB

**使用**：
```
你：搜索我之前提到的 Docker 配置
```

**效果**：
- ✅ 加权检索算法
- ✅ 结合相似度、重要性、近期性、频率
- ✅ 支持多种记忆类型
- ✅ 检索时间 < 1 秒

---

## 📚 文档

- **[USAGE.md](USAGE.md)** - 详细使用指南
- **[QUICKSTART.md](QUICKSTART.md)** - 5 分钟快速开始
- **[docs/](docs/)** - 技术文档和项目总结
- **[skills/](skills/)** - 各 skill 的详细文档

---

## ⚠️ 常见问题

### Q: ChromaDB 必须安装吗？

A: cognitive-memory skill 需要 ChromaDB。如果不安装：
- ✅ pair-coding 仍然可以使用
- ✅ code-registry 仍然可以使用
- ❌ cognitive-memory 无法使用

### Q: Waza 必须安装吗？

A: pair-coding skill 需要 Waza 的 check skill。Waza 通常已经包含在 OpenClaw 中。如果没有，OpenClaw 会自动下载。

### Q: 可以只安装部分 skills 吗？

A: 可以。安装后，删除不需要的 skills 即可：
```bash
rm -rf ~/.agents/skills/cognitive-memory  # 删除 cognitive-memory
```

### Q: 如何卸载？

A: 删除安装的文件：
```bash
# 删除 skills
rm -rf ~/.agents/skills/pair-coding
rm -rf ~/.agents/skills/code-registry
rm -rf ~/.agents/skills/cognitive-memory

# 删除配置
rm ~/.openclaw/workspace/HEARTBEAT.md
```

### Q: 安装后如何使用？

A: 重启 OpenClaw，然后直接对话：
```
你：帮我写一个函数
你：扫描我的项目
你：搜索我之前的配置
```

### Q: Waza 必须安装吗？

A: pair-coding skill 需要 Waza skill 进行代码审查。Waza 是 OpenClaw 的标准 skill，**不包含在本项目中**，需要单独安装。

**安装命令**：
```bash
npm install -g waza-skills
```

**项目地址**：https://github.com/tw93/Waza

### Q: ChromaDB 必须安装吗？

A: cognitive-memory skill 需要 ChromaDB。如果不安装：
- ✅ pair-coding 仍然可以使用
- ✅ code-registry 仍然可以使用
- ❌ cognitive-memory 无法使用

### Q: 可以只安装部分 skills 吗？

A: 可以。安装后，删除不需要的 skills 即可：
```bash
rm -rf ~/.agents/skills/cognitive-memory  # 删除 cognitive-memory
```

### Q: 如何卸载？

A: 检查：
1. OpenClaw 是否正确安装
2. ChromaDB 是否运行
3. Docker 是否运行
4. 查看安装脚本的错误信息

---

## 🛠️ 技术栈

- **OpenClaw** - AI 助手框架
- **Waza** - 工程习惯技能库
- **ChromaDB** - 向量数据库
- **Docker** - 容器化平台

---

## 📊 性能数据

| 指标 | 数值 |
|------|------|
| 测试通过率 | 100% (18/18) |
| BS 检测准确率 | 100% (5/5) |
| 平均迭代次数 | 1.5 |
| 检索时间 | < 1 秒（<1000 条记忆）|

---

## 🤝 贡献

欢迎贡献代码、报告问题、提出建议！

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📝 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

---

## 🙏 致谢

- [OpenSwarm](https://github.com/your-username/openswarm) - 原始项目
- [OpenClaw](https://github.com/openclaw/openclaw) - AI 助手框架
- [Waza](https://github.com/tw93/Waza) - 工程习惯技能库
- [ChromaDB](https://www.trychroma.com/) - 向量数据库

---

## 📬 联系方式

- **GitHub**: [fuguier001](https://github.com/fuguier001)
- **Issues**: [GitHub Issues](https://github.com/fuguier001/openswarm-lobster-version/issues)

---

**🌊 Happy Coding with OpenSwarm 龙虾版！**

---

*如果觉得有用，请给个 Star ⭐️*
