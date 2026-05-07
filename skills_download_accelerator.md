# OpenClaw Skills下载加速方案

## 当前问题分析
1. **clawhub速率限制** - 主要瓶颈
2. **网络连接不稳定** - 影响下载速度
3. **依赖安装缓慢** - 需要优化

## 解决方案分类

### A. 绕过clawhub速率限制的方法

#### 方法1: 使用多个来源
```bash
# 1. 直接从GitHub下载技能
git clone https://github.com/openclaw/skills.git ~/opc-skills-cache

# 2. 从npm安装（如果技能发布到npm）
npm install @openclaw/skill-weather --global

# 3. 使用镜像源
export CLAWHUB_REGISTRY="https://mirror.openclaw.ai"
clawhub install skill-name
```

#### 方法2: 批量下载和本地安装
```bash
# 创建批量下载脚本
cat > download_skills_batch.sh << 'EOF'
#!/bin/bash
# 批量下载常用技能到本地缓存

SKILLS_LIST=(
    "github"
    "whatsapp" 
    "cron"
    "shell"
    "brave-search"
    "agent-browser"
    "pdf"
    "docx"
    "xlsx"
    "pptx"
)

CACHE_DIR="$HOME/.openclaw/skills-cache"
mkdir -p "$CACHE_DIR"

for skill in "${SKILLS_LIST[@]}"; do
    echo "下载: $skill"
    
    # 尝试从多个源下载
    SOURCES=(
        "https://raw.githubusercontent.com/openclaw/skills/main/$skill/SKILL.md"
        "https://cdn.openclaw.ai/skills/$skill/latest/SKILL.md"
        "https://registry.npmjs.org/@openclaw/skill-$skill/-/skill-$skill-1.0.0.tgz"
    )
    
    for url in "${SOURCES[@]}"; do
        if curl -s -f "$url" -o "$CACHE_DIR/${skill}_SKILL.md" 2>/dev/null; then
            echo "  ✅ 从 $(echo $url | cut -d'/' -f3) 下载成功"
            break
        fi
    done
    
    sleep 2  # 避免触发速率限制
done

echo "批量下载完成！缓存位置: $CACHE_DIR"
EOF
```

#### 方法3: 使用代理或VPN
```bash
# 设置代理（如果可用）
export HTTP_PROXY="http://your-proxy:port"
export HTTPS_PROXY="http://your-proxy:port"

# 或者使用socks5代理
export ALL_PROXY="socks5://your-proxy:port"
```

### B. 优化clawhub配置

#### 1. 增加超时和重试
```bash
# 创建优化的clawhub配置
cat > ~/.clawhubrc << 'EOF'
{
  "registry": "https://registry.openclaw.ai",
  "timeout": 30000,
  "retries": 3,
  "concurrency": 1,
  "cache": {
    "enabled": true,
    "ttl": 3600000,
    "path": "~/.clawhub-cache"
  }
}
EOF
```

#### 2. 使用缓存加速
```bash
# 启用并清理clawhub缓存
clawhub cache enable
clawhub cache clean
clawhub cache list

# 手动预缓存常用技能
mkdir -p ~/.clawhub-cache/precached
```

### C. 手动安装技能（绕过clawhub）

#### 方法1: 从OpenClaw自带技能启用
```bash
# 查看所有bundled技能
openclaw skills list | grep "openclaw-bundled"

# 直接复制bundled技能到workspace
cp -r ~/.npm-global/lib/node_modules/openclaw/skills/github ~/.openclaw/workspace/skills/
cp -r ~/.npm-global/lib/node_modules/openclaw/skills/notion ~/.openclaw/workspace/skills/
cp -r ~/.npm-global/lib/node_modules/openclaw/skills/calendar ~/.openclaw/workspace/skills/

# 启用技能
openclaw skills enable github
openclaw skills enable notion
```

#### 方法2: 创建自定义技能模板
```bash
# 快速创建自定义技能模板
cat > create_custom_skill.sh << 'EOF'
#!/bin/bash
SKILL_NAME=$1
SKILL_DIR="$HOME/.openclaw/workspace/skills/$SKILL_NAME"

mkdir -p "$SKILL_DIR"
mkdir -p "$SKILL_DIR/scripts"
mkdir -p "$SKILL_DIR/references"

# 创建SKILL.md
cat > "$SKILL_DIR/SKILL.md" << SKILLEOF
---
name: $SKILL_NAME
description: 自定义 $SKILL_NAME 技能，用于OPC项目
---

# $SKILL_NAME 技能

## 功能
1. 功能1
2. 功能2
3. 功能3

## 使用方法
\`\`\`bash
# 使用示例
./scripts/${SKILL_NAME}_tool.sh
\`\`\`

## 配置
编辑 config.json 文件进行配置
SKILLEOF

# 创建示例脚本
cat > "$SKILL_DIR/scripts/${SKILL_NAME}_tool.sh" << 'EOF'
#!/bin/bash
echo "这是 $SKILL_NAME 技能的工具脚本"
echo "可以在这里添加具体功能"
EOF

chmod +x "$SKILL_DIR/scripts/${SKILL_NAME}_tool.sh"

echo "自定义技能已创建: $SKILL_DIR"
EOF

chmod +x create_custom_skill.sh
```

### D. 并行下载策略

#### 使用Python并行下载
```bash
# 创建并行下载脚本
cat > parallel_download.py << 'EOF'
#!/usr/bin/env python3
"""
并行下载OpenClaw技能
使用多线程加速下载
"""

import concurrent.futures
import requests
import os
import time
from pathlib import Path

# 需要下载的技能列表
SKILLS_TO_DOWNLOAD = [
    "github", "whatsapp", "cron", "shell", "brave-search",
    "agent-browser", "pdf", "docx", "xlsx", "pptx"
]

def download_skill(skill_name):
    """下载单个技能"""
    print(f"开始下载: {skill_name}")
    
    # 尝试多个源
    sources = [
        f"https://raw.githubusercontent.com/openclaw/skills/main/{skill_name}/SKILL.md",
        f"https://cdn.openclaw.ai/skills/{skill_name}/latest/SKILL.md"
    ]
    
    for url in sources:
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                # 保存文件
                skill_dir = Path(f"~/.openclaw/workspace/skills/{skill_name}").expanduser()
                skill_dir.mkdir(parents=True, exist_ok=True)
                
                skill_file = skill_dir / "SKILL.md"
                skill_file.write_text(response.text)
                
                print(f"  ✅ {skill_name} 下载成功")
                return True
        except Exception as e:
            continue
    
    print(f"  ❌ {skill_name} 下载失败")
    return False

def main():
    print("🚀 开始并行下载OpenClaw技能")
    print("="*50)
    
    # 创建输出目录
    output_dir = Path("~/.openclaw/workspace/skills").expanduser()
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 使用线程池并行下载
    success_count = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
        # 提交所有下载任务
        future_to_skill = {
            executor.submit(download_skill, skill): skill 
            for skill in SKILLS_TO_DOWNLOAD
        }
        
        # 等待所有任务完成
        for future in concurrent.futures.as_completed(future_to_skill):
            skill = future_to_skill[future]
            try:
                if future.result():
                    success_count += 1
            except Exception as e:
                print(f"  ❌ {skill} 下载异常: {e}")
    
    print(f"\n📊 下载完成: {success_count}/{len(SKILLS_TO_DOWNLOAD)} 个技能")
    
    # 创建启用脚本
    enable_script = output_dir / "enable_all_skills.sh"
    enable_script.write_text('''#!/bin/bash
# 启用所有下载的技能
for skill in github whatsapp cron shell brave-search agent-browser pdf docx xlsx pptx; do
    if [ -f "$HOME/.openclaw/workspace/skills/$skill/SKILL.md" ]; then
        echo "启用: $skill"
        # openclaw skills enable $skill
    fi
done
''')
    
    enable_script.chmod(0o755)
    print(f"\n✅ 启用脚本已创建: {enable_script}")

if __name__ == "__main__":
    main()
EOF
```

### E. 使用本地镜像或CDN

#### 配置本地镜像
```bash
# 如果公司或团队有内部网络，可以设置本地镜像
cat > setup_local_mirror.sh << 'EOF'
#!/bin/bash
# 设置本地OpenClaw技能镜像

MIRROR_DIR="/var/www/openclaw-mirror"
SKILLS_REPO="https://github.com/openclaw/skills.git"

echo "设置本地技能镜像..."
sudo mkdir -p "$MIRROR_DIR"
sudo chown -R $USER:$USER "$MIRROR_DIR"

# 克隆技能仓库
if [ ! -d "$MIRROR_DIR/.git" ]; then
    git clone --depth 1 "$SKILLS_REPO" "$MIRROR_DIR"
else
    cd "$MIRROR_DIR" && git pull
fi

# 创建简单的HTTP服务器
cat > "$MIRROR_DIR/serve.sh" << 'SERVEOF'
#!/bin/bash
cd "$(dirname "$0")"
python3 -m http.server 8080
SERVEOF

chmod +x "$MIRROR_DIR/serve.sh"

# 配置clawhub使用本地镜像
cat >> ~/.clawhubrc << 'CLAWEOF'
{
  "registry": "http://localhost:8080",
  "local_mirror": true
}
CLAWEOF

echo "本地镜像已设置完成!"
echo "启动服务器: cd $MIRROR_DIR && ./serve.sh"
echo "然后在另一个终端中使用: clawhub install skill-name"
EOF
```

### F. 预下载和离线包

#### 创建技能离线包
```bash
# 创建离线安装包
cat > create_offline_package.sh << 'EOF'
#!/bin/bash
# 创建OpenClaw技能离线安装包

PACKAGE_NAME="opc-essential-skills-$(date +%Y%m%d)"
PACKAGE_DIR="/tmp/$PACKAGE_NAME"
INSTALL_SCRIPT="$PACKAGE_DIR/install.sh"

echo "创建离线技能包: $PACKAGE_NAME"
mkdir -p "$PACKAGE_DIR/skills"

# 核心技能列表
CORE_SKILLS=(
    "github"
    "whatsapp"
    "cron"
    "shell"
    "brave-search"
    "agent-browser"
    "pdf"
    "docx"
    "xlsx"
    "pptx"
)

# 创建安装脚本
cat > "$INSTALL_SCRIPT" << 'INSTEOF'
#!/bin/bash
echo "安装OpenClaw技能离线包"
echo "========================"

INSTALL_DIR="$HOME/.openclaw/workspace/skills"
mkdir -p "$INSTALL_DIR"

# 复制所有技能
for skill in github whatsapp cron shell brave-search agent-browser pdf docx xlsx pptx; do
    if [ -d "skills/$skill" ]; then
        echo "安装: $skill"
        cp -r "skills/$skill" "$INSTALL_DIR/"
    fi
done

echo "安装完成!"
echo "技能位置: $INSTALL_DIR"
INSTEOF

chmod +x "$INSTALL_SCRIPT"

echo "✅ 离线包创建完成: $PACKAGE_DIR"
echo "压缩包: tar -czf $PACKAGE_NAME.tar.gz -C /tmp $PACKAGE_NAME"
EOF
```

## 🎯 立即执行的优化方案

### 方案1: 快速修复（立即执行）
```bash
# 1. 清理缓存和临时文件
rm -rf ~/.clawhub-cache/*
rm -rf /tmp/clawhub-*

# 2. 使用更稳定的registry
export CLAWHUB_REGISTRY="https://registry.npmjs.org"

# 3. 增加超时时间
export CLAWHUB_TIMEOUT=60000

# 4. 一次只安装一个技能，避免并发限制
for skill in github whatsapp; do
    echo "安装: $skill"
    clawhub install "$skill" --force
    sleep 10  # 等待10秒避免速率限制
done
```

### 方案2: 备用方案（网络恢复后）
```bash
# 使用wget直接下载技能文件
mkdir -p ~/skills-backup
cd ~/skills-backup

# 从GitHub直接下载
wget -q -r -np -nH --cut-dirs=3 -R "index.html*" \
    https://github.com/openclaw/skills/tree/main/github

# 然后手动复制到workspace
cp -r github ~/.openclaw/workspace/skills/
```

### 方案3: 长期解决方案
1. **设置本地镜像服务器**
2. **使用CDN加速**
3. **预下载常用技能包**
4. **建立团队内部技能仓库**

## 📊 监控和调试

### 检查下载速度
```bash
# 测试下载速度
cat > test_download_speed.sh << 'EOF'
#!/bin/bash
echo "测试不同源的下载速度..."
echo "1. GitHub Raw:"
time curl -s -o /dev/null https://raw.githubusercontent.com/openclaw/skills/main/github/SKILL.md

echo -e "\n2. NPM Registry:"
time curl -s -o /dev/null https://registry.npmjs.org/@openclaw/skill-github

echo -e "\n3. OpenClaw CDN:"
time curl -s -o /dev/null https://cdn.openclaw.ai/skills/github/latest/SKILL.md
EOF
```

## 🚨 紧急情况处理

如果所有方法都失败，可以采用：
1. **手动创建技能** - 根据文档自己实现功能
2. **使用替代工具** - 用Python脚本代替特定技能
3. **延迟非关键技能** - 先开发核心功能，后期再添加技能

## 📋 优先级建议

### 高优先级（立即需要）：
1. **github** - 代码管理
2. **cron** - 定时任务
3. **shell** - 系统操作

### 中优先级（一周内需要）：
1. **whatsapp** - 消息通知
2. **brave-search** - 网络搜索
3. **agent-browser** - 浏览器控制

### 低优先级（可延迟）：
1. **pdf/docx/xlsx/pptx** - 文档处理
2. 其他办公自动化技能

**建议您先尝试方案1的快速修复**，如果还是慢，我们可以实施方案2的备用方案。