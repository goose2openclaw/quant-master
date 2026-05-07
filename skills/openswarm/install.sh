#!/bin/bash

# OpenSwarm 龙虾版 - 一键安装脚本
# 将 OpenSwarm 的核心模式安装到 OpenClaw

set -e

echo "🌊 OpenSwarm 龙虾版 - 安装中..."
echo ""

# 检查 OpenClaw 安装目录
OPENCLAW_SKILLS_DIR="${HOME}/.agents/skills"

if [ ! -d "$OPENCLAW_SKILLS_DIR" ]; then
    echo "❌ 错误：未找到 OpenClaw 安装目录"
    echo "   预期目录：$OPENCLAW_SKILLS_DIR"
    echo "   请确认 OpenClaw 已正确安装"
    exit 1
fi

echo "✓ 找到 OpenClaw 安装目录: $OPENCLAW_SKILLS_DIR"
echo ""

# 检查 Waza
echo "🔍 检查 Waza skill..."

WAZA_SKILL="${HOME}/.npm-global/lib/node_modules/openclaw/skills/waza/SKILL.md"
if [ -f "$WAZA_SKILL" ]; then
    echo "   ✓ Waza skill 已安装"
    WAZA_INSTALLED=true
else
    echo "   ⚠️  未找到 Waza skill"
    echo "   pair-coding skill 需要 Waza 进行代码审查"
    echo "   Waza 是 OpenClaw 的标准 skill，需要单独安装"
    echo ""
    echo "   安装命令："
    echo "   方法 1: npm install -g waza-skills"
    echo "   方法 2: git clone https://github.com/tw93/Waza.git && cd Waza && npm install && npm link"
    echo ""
    read -p "是否现在安装 Waza？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🔧 安装 Waza..."
        if command -v npm &> /dev/null; then
            npm install -g waza-skills
            if [ -f "$WAZA_SKILL" ]; then
                echo "   ✓ Waza 安装成功！"
                WAZA_INSTALLED=true
            else
                echo "   ❌ Waza 安装失败"
                echo "   请手动安装：npm install -g waza-skills"
            fi
        else
            echo "   ⚠️  未找到 npm"
            echo "   请先安装 Node.js 和 npm"
        fi
    else
        echo "   ⚠️  跳过 Waza 安装"
        echo "   pair-coding skill 将无法使用"
        WAZA_INSTALLED=false
    fi
fi
echo ""

# 检查 ChromaDB
echo "🔍 检查 ChromaDB..."

CHROMADB_RUNNING=false

# 检查 Docker 中的 ChromaDB
if command -v docker &> /dev/null; then
    if docker ps | grep -q chroma; then
        echo "   ✓ ChromaDB 正在运行（Docker）"
        CHROMADB_RUNNING=true
    fi
fi

# 检查本地 ChromaDB
if ! $CHROMADB_RUNNING; then
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
            echo "   ✓ ChromaDB 正在运行（本地）"
            CHROMADB_RUNNING=true
        fi
    fi
fi

if ! $CHROMADB_RUNNING; then
    echo "   ⚠️  ChromaDB 未运行"
    echo ""
    echo "📌 ChromaDB 是 cognitive-memory skill 的必需组件"
    echo "   如果不安装，cognitive-memory skill 将无法使用"
    echo "   但 pair-coding 和 code-registry 仍然可以正常使用"
    echo ""
    read -p "是否现在安装 ChromaDB？(y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo ""
        echo "🔧 安装 ChromaDB..."

        # 检查 Docker
        if command -v docker &> /dev/null; then
            echo "   使用 Docker 安装..."
            docker run -d -p 8000:8000 --name openswarm-chromadb chromadb/chroma

            if docker ps | grep -q openswarm-chromadb; then
                echo "   ✓ ChromaDB 安装成功！"
                CHROMADB_RUNNING=true
            else
                echo "   ❌ ChromaDB 安装失败"
                echo "   请手动安装：docker run -d -p 8000:8000 chromadb/chroma"
            fi
        else
            echo "   ⚠️  未找到 Docker"
            echo "   请选择其他方式安装："
            echo ""
            echo "   方法 1: 安装 Docker（推荐）"
            echo "      https://docs.docker.com/get-docker/"
            echo ""
            echo "   方法 2: 使用 pip 安装"
            echo "      pip install chromadb"
            echo "      chroma-server --host 0.0.0.0 --port 8000"
            echo ""
            echo "   跳过 ChromaDB 安装..."
        fi
    else
        echo "   ⚠️  跳过 ChromaDB 安装"
        echo "   cognitive-memory skill 将无法使用"
    fi
else
    echo ""
fi

# 验证 ChromaDB 连接
if $CHROMADB_RUNNING; then
    echo "🔍 验证 ChromaDB 连接..."
    if command -v curl &> /dev/null; then
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
            echo "   ✓ ChromaDB 连接成功"
        else
            echo "   ⚠️  ChromaDB 连接失败"
            echo "   请检查 ChromaDB 是否在 8000 端口运行"
        fi
    fi
    echo ""
fi

# 安装 skills
echo "📦 安装 skills..."
echo ""

# pair-coding
if [ -d "skills/pair-coding" ]; then
    echo "   ✓ 安装 pair-coding skill..."
    cp -r skills/pair-coding "$OPENCLAW_SKILLS_DIR/"
else
    echo "   ❌ 未找到 pair-coding skill"
    exit 1
fi

# code-registry
if [ -d "skills/code-registry" ]; then
    echo "   ✓ 安装 code-registry skill..."
    cp -r skills/code-registry "$OPENCLAW_SKILLS_DIR/"
else
    echo "   ❌ 未找到 code-registry skill"
    exit 1
fi

# cognitive-memory
if [ -d "skills/cognitive-memory" ]; then
    echo "   ✓ 安装 cognitive-memory skill..."
    cp -r skills/cognitive-memory "$OPENCLAW_SKILLS_DIR/"
else
    echo "   ❌ 未找到 cognitive-memory skill"
    exit 1
fi

# 复制 HEARTBEAT 配置
echo ""
echo "📝 配置 HEARTBEAT..."
if [ -f "HEARTBEAT.md" ]; then
    mkdir -p "${HOME}/.openclaw/workspace"
    cp HEARTBEAT.md "${HOME}/.openclaw/workspace/HEARTBEAT.md"
    echo "   ✓ HEARTBEAT 配置已复制"
else
    echo "   ⚠️  未找到 HEARTBEAT.md"
fi

echo ""
echo "✅ 安装完成！"
echo ""
echo "📚 已安装的 skills："
if $WAZA_INSTALLED; then
    echo "   - pair-coding: Worker/Reviewer 对模式（✓ Waza 已配置）"
else
    echo "   - pair-coding: Worker/Reviewer 对模式（⚠️ 需要 Waza）"
fi
echo "   - code-registry: 代码注册表 + BS 检测器（✓ 无需额外依赖）"
if $CHROMADB_RUNNING; then
    echo "   - cognitive-memory: 认知记忆系统（✓ ChromaDB 已配置）"
else
    echo "   - cognitive-memory: 认知记忆系统（⚠️ 需要 ChromaDB）"
fi
echo ""
echo "🚀 下一步："
echo "   1. 重启 OpenClaw"
echo "   2. 查看 USAGE.md 了解如何使用"
echo "   3. 配置 HEARTBEAT.md 启用自动化（可选）"
echo ""
if ! $WAZA_INSTALLED; then
    echo "⚠️  注意：pair-coding skill 需要 Waza check skill"
    echo "   安装命令：npm install -g @waza/skills"
    echo ""
fi
if ! $CHROMADB_RUNNING; then
    echo "⚠️  注意：cognitive-memory skill 需要 ChromaDB"
    echo "   安装命令：docker run -d -p 8000:8000 chromadb/chroma"
    echo ""
fi
echo "📖 文档："
echo "   - USAGE.md: 使用说明"
echo "   - docs/: 详细文档"
echo "   - skills/<name>/README.md: 各 skill 文档"
echo ""
echo "🌊 Happy Coding!"
