#!/bin/bash

# ChromaDB 一键安装脚本
# 支持 Docker 和本地安装

set -e

echo "🔧 ChromaDB 安装脚本"
echo ""

# 检查是否已经运行
echo "🔍 检查 ChromaDB 状态..."

if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
    echo "   ✓ ChromaDB 已经在运行"
    echo "   端口：8000"
    echo ""
    echo "无需重新安装"
    exit 0
fi

echo "   ChromaDB 未运行"
echo ""

# 选择安装方式
echo "请选择安装方式："
echo "   1. Docker（推荐）"
echo "   2. 本地安装（需要 Python 3.8+）"
echo "   3. 退出"
echo ""
read -p "请输入选项 (1/2/3): " choice

case $choice in
    1)
        echo ""
        echo "🐳 使用 Docker 安装..."

        # 检查 Docker
        if ! command -v docker &> /dev/null; then
            echo "   ❌ 未找到 Docker"
            echo "   请先安装 Docker：https://docs.docker.com/get-docker/"
            exit 1
        fi

        # 检查是否已存在容器
        if docker ps -a | grep -q openswarm-chromadb; then
            echo "   发现已存在的 ChromaDB 容器"
            read -p "是否删除并重新创建？(y/n) " -n 1 -r
            echo
            if [[ $REPLY =~ ^[Yy]$ ]]; then
                docker stop openswarm-chromadb 2>/dev/null || true
                docker rm openswarm-chromadb 2>/dev/null || true
                echo "   ✓ 已删除旧容器"
            else
                docker start openswarm-chromadb
                echo "   ✓ 已启动现有容器"
                exit 0
            fi
        fi

        # 运行新容器
        echo "   启动 ChromaDB 容器..."
        docker run -d \
            --name openswarm-chromadb \
            -p 8000:8000 \
            -v openswarm-chromadb-data:/chroma/chroma \
            chromadb/chroma

        # 等待启动
        echo "   等待 ChromaDB 启动..."
        sleep 3

        # 验证
        if curl -s http://localhost:8000/api/v1/heartbeat > /dev/null 2>&1; then
            echo "   ✓ ChromaDB 安装成功！"
            echo "   容器名：openswarm-chromadb"
            echo "   端口：8000"
            echo ""
            echo "常用命令："
            echo "   启动：docker start openswarm-chromadb"
            echo "   停止：docker stop openswarm-chromadb"
            echo "   删除：docker rm -f openswarm-chromadb"
        else
            echo "   ❌ ChromaDB 启动失败"
            echo "   请检查日志：docker logs openswarm-chromadb"
            exit 1
        fi
        ;;

    2)
        echo ""
        echo "🐍 本地安装..."

        # 检查 Python
        if ! command -v python3 &> /dev/null; then
            echo "   ❌ 未找到 Python 3"
            echo "   请先安装 Python 3.8 或更高版本"
            exit 1
        fi

        PYTHON_VERSION=$(python3 --version | awk '{print $2}')
        echo "   找到 Python 版本：$PYTHON_VERSION"

        # 检查 pip
        if ! command -v pip3 &> /dev/null; then
            echo "   ❌ 未找到 pip3"
            echo "   请先安装 pip"
            exit 1
        fi

        # 安装 ChromaDB
        echo "   安装 ChromaDB..."
        pip3 install chromadb

        # 启动 ChromaDB
        echo "   启动 ChromaDB 服务器..."
        echo "   ChromaDB 将在后台运行"
        echo "   按 Ctrl+C 停止"

        chroma-server --host 0.0.0.0 --port 8000
        ;;

    3)
        echo "退出"
        exit 0
        ;;

    *)
        echo "无效选项"
        exit 1
        ;;
esac

echo ""
echo "✅ 安装完成！"
echo ""
echo "🔍 验证安装："
echo "   curl http://localhost:8000/api/v1/heartbeat"
echo ""
echo "🌊 Happy Coding!"
