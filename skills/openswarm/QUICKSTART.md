# 快速开始指南

## 5 分钟快速安装

### 1. 安装 ChromaDB（必需）

```bash
# Docker 方式（推荐）
docker run -d -p 8000:8000 chromadb/chroma

# 或使用我们的脚本
chmod +x install-chromadb.sh
./install-chromadb.sh
```

### 2. 安装 OpenSwarm 龙虾版

```bash
# 克隆项目
git clone https://github.com/fuguier001/openswarm-lobster-version.git
cd openswarm-lobster-version

# 一键安装
chmod +x install.sh
./install.sh
```

### 3. 重启 OpenClaw

安装完成后，重启 OpenClaw 让 skills 生效。

### 4. 开始使用

直接与 OpenClaw 对话：

```
你：帮我写一个用户认证系统
```

## 详细说明

### 前置要求

| 组件 | 状态 | 说明 |
|------|------|------|
| OpenClaw | ✅ 必需 | 需要已安装 |
| Waza skill | ✅ 必需 | pair-coding 需要（check skill）|
| ChromaDB | ⚠️ 条件必需 | cognitive-memory 需要 |
| Docker | 🐳 可选 | 推荐，用于运行 ChromaDB |
| Python 3.8+ | 🐍 可选 | 用于本地安装 ChromaDB |

### 检查 Waza 安装

```bash
# 检查 Waza skill
ls ~/.npm-global/lib/node_modules/openclaw/skills/wasa/skills/check/

# 如果不存在，Waza 通常会自动下载
# 或手动安装
npm install -g @waza/skills
```

### 安装 ChromaDB 的方法

#### 方法 1：Docker（推荐）
```bash
# 拉取并运行
docker run -d -p 8000:8000 chromadb/chroma

# 验证
curl http://localhost:8000/api/v1/heartbeat
```

#### 方法 2：本地安装
```bash
# 使用 pip
pip install chromadb

# 启动服务器
chroma-server --host 0.0.0.0 --port 8000
```

#### 方法 3：使用脚本
```bash
chmod +x install-chromadb.sh
./install-chromadb.sh
```

脚本会提示你选择 Docker 或本地安装。

### 验证安装

```bash
# 检查 ChromaDB
curl http://localhost:8000/api/v1/heartbeat

# 检查 skills
ls ~/.agents/skills/pair-coding
ls ~/.agents/skills/code-registry
ls ~/.agents/skills/cognitive-memory

# 检查 HEARTBEAT 配置
cat ~/.openclaw/workspace/HEARTBEAT.md
```

### 常见问题

**Q: ChromaDB 必须安装吗？**

A: cognitive-memory skill 需要 ChromaDB。如果不安装：
- ✅ pair-coding 仍然可以使用
- ✅ code-registry 仍然可以使用
- ❌ cognitive-memory 无法使用

**Q: 如何启动/停止 ChromaDB？**

A: Docker 方式：
```bash
# 启动
docker start openswarm-chromadb

# 停止
docker stop openswarm-chromadb
```

**Q: 安装后如何使用？**

A: 重启 OpenClaw，然后直接对话：
```
你：帮我写一个函数
你：扫描我的项目
你：搜索我之前的配置
```

**Q: 卸载怎么办？**

A: 删除 skills 目录和配置：
```bash
rm -rf ~/.agents/skills/pair-coding
rm -rf ~/.agents/skills/code-registry
rm -rf ~/.agents/skills/cognitive-memory
rm ~/.openclaw/workspace/HEARTBEAT.md
```

## 下一步

- 查看 [USAGE.md](USAGE.md) 了解详细使用方法
- 查看 [docs/](docs/) 了解技术细节
- 查看 [skills/](skills/) 了解各个 skill

## 获取帮助

- GitHub Issues: https://github.com/fuguier001/openswarm-lobster-version/issues
- 文档: https://github.com/fuguier001/openswarm-lobster-version

---

**🌊 Happy Coding!**
