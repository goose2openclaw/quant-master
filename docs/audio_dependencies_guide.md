# 音频处理依赖安装指南

## 概述
本文档提供在OpenClaw系统中安装音频处理所需依赖的完整指南。

## 系统要求

### 最低要求
- **操作系统**: Ubuntu 20.04+ / Debian 11+ / macOS 11+ / Windows 10+
- **内存**: 4GB RAM（推荐8GB+）
- **存储**: 10GB可用空间
- **Python**: 3.8-3.11

### 推荐配置
- **CPU**: 4核以上
- **GPU**: NVIDIA GPU（CUDA支持）用于加速
- **内存**: 16GB RAM
- **存储**: 50GB SSD

## 依赖分类

### 核心依赖（必需）
1. **FFmpeg** - 音频/视频处理
2. **Python 3.8+** - 编程环境
3. **pip** - Python包管理

### 转录依赖（必需）
1. **OpenAI Whisper** - 语音识别
2. **faster-whisper** - 加速版本（可选）

### 开发依赖（可选）
1. **PyTorch** - 深度学习框架
2. **CUDA Toolkit** - GPU加速（NVIDIA）
3. **开发工具** - 编译工具链

## 安装方法

### 方法1: 一键安装脚本（推荐）

```bash
#!/bin/bash
# install_audio_deps.sh

echo "🎵 开始安装音频处理依赖"
echo "="*50

# 检查系统
echo "🔍 检查系统信息..."
OS=$(uname -s)
ARCH=$(uname -m)

echo "系统: $OS $ARCH"

# 更新包管理器
echo "🔄 更新包管理器..."
if [ "$OS" = "Linux" ]; then
    sudo apt update
elif [ "$OS" = "Darwin" ]; then
    brew update
fi

# 安装FFmpeg
echo "📦 安装FFmpeg..."
if [ "$OS" = "Linux" ]; then
    sudo apt install -y ffmpeg
elif [ "$OS" = "Darwin" ]; then
    brew install ffmpeg
else
    echo "⚠ 请手动安装FFmpeg: https://ffmpeg.org/download.html"
fi

# 检查Python
echo "🐍 检查Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3未安装"
    if [ "$OS" = "Linux" ]; then
        sudo apt install -y python3 python3-pip
    elif [ "$OS" = "Darwin" ]; then
        brew install python@3.11
    fi
else
    echo "✅ Python3已安装: $(python3 --version)"
fi

# 安装pip（如果需要）
if ! command -v pip3 &> /dev/null; then
    echo "📦 安装pip..."
    if [ "$OS" = "Linux" ]; then
        sudo apt install -y python3-pip
    elif [ "$OS" = "Darwin" ]; then
        curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
        python3 get-pip.py
        rm get-pip.py
    fi
fi

# 安装Whisper
echo "🎙️ 安装OpenAI Whisper..."
pip3 install openai-whisper

# 安装可选依赖
echo "⚡ 安装可选加速依赖..."
pip3 install faster-whisper

# 验证安装
echo "✅ 验证安装..."
if command -v ffmpeg &> /dev/null; then
    echo "✅ FFmpeg: $(ffmpeg -version | head -1)"
else
    echo "❌ FFmpeg未安装"
fi

if python3 -c "import whisper; print('✅ Whisper导入成功')" &> /dev/null; then
    echo "✅ Whisper安装成功"
else
    echo "❌ Whisper安装失败"
fi

echo ""
echo "🎉 安装完成!"
echo "="*50
echo "📋 已安装:"
echo "  - FFmpeg (音频处理)"
echo "  - Python 3 + pip"
echo "  - OpenAI Whisper"
echo "  - faster-whisper (可选)"
echo ""
echo "🚀 下一步:"
echo "  运行测试: python3 -c \"import whisper; print('Whisper版本:', whisper.__version__)\""
```

保存为 `install_audio_deps.sh` 并运行：
```bash
chmod +x install_audio_deps.sh
./install_audio_deps.sh
```

### 方法2: 分步手动安装

#### 步骤1: 安装FFmpeg

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. 下载FFmpeg: https://ffmpeg.org/download.html
2. 解压到 `C:\ffmpeg`
3. 添加 `C:\ffmpeg\bin` 到系统PATH

**验证安装:**
```bash
ffmpeg -version
```

#### 步骤2: 安装Python和pip

**Ubuntu/Debian:**
```bash
sudo apt install -y python3 python3-pip python3-venv
```

**macOS:**
```bash
brew install python@3.11
```

**Windows:**
1. 下载Python: https://www.python.org/downloads/
2. 安装时勾选 "Add Python to PATH"

**验证安装:**
```bash
python3 --version
pip3 --version
```

#### 步骤3: 安装Whisper

**使用pip安装:**
```bash
pip3 install openai-whisper
```

**使用conda安装:**
```bash
conda install -c conda-forge openai-whisper
```

**从源码安装:**
```bash
git clone https://github.com/openai/whisper.git
cd whisper
pip3 install -e .
```

**验证安装:**
```bash
python3 -c "import whisper; print('Whisper版本:', whisper.__version__)"
```

#### 步骤4: 安装加速版本（可选）

**faster-whisper (CPU/GPU加速):**
```bash
pip3 install faster-whisper
```

**需要CUDA的版本:**
```bash
# 先安装PyTorch with CUDA
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 安装faster-whisper
pip3 install faster-whisper
```

### 方法3: 使用Docker

**Dockerfile:**
```dockerfile
FROM python:3.11-slim

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# 安装Python依赖
RUN pip install --no-cache-dir \
    openai-whisper \
    faster-whisper \
    torch torchvision torchaudio

# 设置工作目录
WORKDIR /app

# 复制脚本
COPY . .

# 运行命令
CMD ["python", "audio_processor.py"]
```

**构建和运行:**
```bash
docker build -t audio-processor .
docker run -v $(pwd)/audio:/app/audio audio-processor
```

### 方法4: 使用虚拟环境

**创建虚拟环境:**
```bash
python3 -m venv audio_env
source audio_env/bin/activate  # Linux/macOS
# 或
audio_env\Scripts\activate     # Windows
```

**在虚拟环境中安装:**
```bash
pip install openai-whisper faster-whisper
```

**退出虚拟环境:**
```bash
deactivate
```

## 平台特定指南

### Ubuntu/Debian (完整安装)
```bash
#!/bin/bash
# ubuntu_install.sh

# 更新系统
sudo apt update
sudo apt upgrade -y

# 安装基础工具
sudo apt install -y wget curl git build-essential

# 安装FFmpeg
sudo apt install -y ffmpeg

# 安装Python
sudo apt install -y python3 python3-pip python3-venv python3-dev

# 安装PyTorch依赖
sudo apt install -y libopenblas-dev libblas-dev m4 cmake cython3

# 创建虚拟环境
python3 -m venv ~/audio_env
source ~/audio_env/bin/activate

# 安装Python包
pip install --upgrade pip
pip install openai-whisper faster-whisper

# 测试
python -c "import whisper; print('安装成功!')"
```

### macOS (Homebrew)
```bash
#!/bin/bash
# macos_install.sh

# 安装Homebrew（如果未安装）
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# 安装依赖
brew install ffmpeg python@3.11

# 配置Python
echo 'export PATH="/usr/local/opt/python@3.11/bin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# 安装Python包
pip3 install openai-whisper faster-whisper

# 测试
python3 -c "import whisper; print('安装成功!')"
```

### Windows (PowerShell)
```powershell
# windows_install.ps1

# 安装Chocolatey（包管理器）
Set-ExecutionPolicy Bypass -Scope Process -Force
[System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072
iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# 安装依赖
choco install ffmpeg python -y

# 更新PATH
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

# 安装Python包
pip install openai-whisper faster-whisper

# 测试
python -c "import whisper; print('安装成功!')"
```

## GPU加速配置

### NVIDIA GPU (CUDA)

**检查GPU:**
```bash
nvidia-smi
```

**安装CUDA Toolkit:**
```bash
# Ubuntu
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.1-1_all.deb
sudo dpkg -i cuda-keyring_1.1-1_all.deb
sudo apt update
sudo apt install -y cuda-toolkit-12-4

# 验证
nvcc --version
```

**安装PyTorch with CUDA:**
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121
```

**安装faster-whisper with CUDA:**
```bash
pip3 install faster-whisper
```

### AMD GPU (ROCm)

**安装ROCm:**
```bash
# Ubuntu
sudo apt update
sudo apt install -y rocm-hip-sdk rocm-opencl-sdk
```

**安装PyTorch with ROCm:**
```bash
pip3 install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/rocm5.7
```

## 故障排除

### 常见问题

#### 1. "ffmpeg: command not found"
**解决方案:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# 检查是否在PATH中
which ffmpeg
```

#### 2. "No module named 'whisper'"
**解决方案:**
```bash
# 重新安装
pip3 uninstall whisper
pip3 install openai-whisper

# 检查Python路径
python3 -c "import sys; print(sys.path)"
```

#### 3. 内存不足错误
**解决方案:**
- 使用更小的模型: `--model base` 或 `--model small`
- 增加swap空间
- 分段处理长音频

#### 4. 处理速度慢
**解决方案:**
```bash
# 使用更快的模型
whisper audio.mp3 --model turbo

# 使用faster-whisper
from faster_whisper import WhisperModel
model = WhisperModel("base", device="cuda", compute_type="float16")

# 使用GPU
whisper audio.mp3 --device cuda
```

#### 5. 音频格式不支持
**解决方案:**
```bash
# 转换为支持的格式
ffmpeg -i input.m4a -acodec libvorbis output.ogg
ffmpeg -i input.opus -acodec pcm_s16le output.wav
```

### 调试命令

**检查系统信息:**
```bash
# 系统信息
uname -a
lsb_release -a  # Linux

# Python信息
python3 --version
pip3 list | grep -i whisper

# 音频工具
ffmpeg -version
which ffmpeg
```

**测试Whisper安装:**
```bash
# 简单测试
python3 -c "
import whisper
print('Whisper版本:', whisper.__version__)

# 测试模型加载
try:
    model = whisper.load_model('base')
    print('✅ 模型加载成功')
except Exception as e:
    print('❌ 模型加载失败:', e)
"
```

**测试音频处理:**
```bash
# 创建测试音频
echo "这是一个测试录音" | text2wave -o test.wav

# 测试转录
whisper test.wav --model base --language zh
```

## 性能优化

### 模型选择指南

| 模型 | 大小 | 速度 | 质量 | 内存 | 推荐用途 |
|------|------|------|------|------|----------|
| **tiny** | 39M | ⚡⚡⚡⚡ | ⭐ | ~1GB | 实时转录，移动设备 |
| **base** | 74M | ⚡⚡⚡ | ⭐⭐ | ~1GB | 一般用途，平衡 |
| **small** | 244M | ⚡⚡ | ⭐⭐⭐ | ~2GB | 高质量转录 |
| **medium** | 769M | ⚡ | ⭐⭐⭐⭐ | ~5GB | 专业用途 |
| **large** | 1550M | - | ⭐⭐⭐⭐⭐ | ~10GB | 研究，最高质量 |
| **turbo** | 809M | ⚡⚡⚡ | ⭐⭐⭐⭐ | ~6GB | 最佳速度/质量比 |

### 配置优化

**CPU优化:**
```bash
# 使用多线程
whisper audio.mp3 --threads $(nproc)

# 使用更高效的模型
whisper audio.mp3 --model turbo

# 禁用GPU
whisper audio.mp3 --device cpu
```

**内存优化:**
```bash
# 分段处理长音频
whisper long_audio.mp3 --split_on_silence

# 使用低内存模型
whisper audio.mp3 --model tiny

# 清理缓存
import torch
torch.cuda.empty_cache()
```

## 维护与更新

### 更新依赖
```bash
# 更新所有包
pip3 install --upgrade openai-whisper faster-whisper

# 更新系统包
sudo apt update && sudo apt upgrade -y  # Ubuntu/Debian
brew update && brew upgrade            # macOS
```

### 清理缓存
```bash
# 清理pip缓存
pip3 cache purge

# 清理下载的模型
rm -rf ~/.cache/whisper

# 清理临时文件
find /tmp -name "*.wav" -o -name "*.mp3" -mtime +1 -delete
```

### 监控资源使用
```bash
# 监控CPU/内存
htop

# 监控GPU
nvidia-smi -l 1

# 监控磁盘
df -h
du -sh ~/.cache/whisper
```

## 安全考虑

### 权限管理
```bash
# 限制文件权限
chmod 600 audio_files/*

# 使用专用用户
sudo useradd -r -s /bin/false audio_processor

# 设置目录权限
sudo chown -R audio_processor:audio_processor /var/lib/audio
```

### 网络隔离
```bash
# 使用防火墙
sudo ufw allow from 192.168.1.0/24 to any port 8000

# 使用VPN处理敏感音频
```

### 数据加密
```bash
# 加密存储
sudo apt install ecryptfs-utils
sudo mount -t ecryptfs /audio_data /audio_data_encrypted
```

## 附录

### 有用的命令参考

**音频处理:**
```bash
# 获取音频信息
ffprobe -v error -show_format -show_streams audio.mp3

# 转换格式
ffmpeg -i input.mp3 -acodec libvorbis -aq 4 output.ogg

# 提取片段
ffmpeg -i audio.mp3 -ss 00:01:00 -to 00:02:00 -c copy segment.mp3

# 调整音量
ffmpeg -i input.mp3 -af "volume=1.5" output.mp3
```

**Whisper命令:**
```bash
# 基本转录
whisper audio.mp3 --model large-v3 --language zh

# 带时间戳
whisper audio.mp3 --output_format srt

# 批量处理
for file in *.mp3; do whisper "$file" --model base; done

# 使用GPU
whisper audio.mp3