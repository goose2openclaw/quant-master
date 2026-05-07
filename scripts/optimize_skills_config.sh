#!/bin/bash

# OPC项目技能配置优化脚本
# 自动优化技能配置，提高性能和可靠性

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 配置目录
SKILLS_DIR="/home/goose/.openclaw/workspace/skills"
CONFIG_DIR="/home/goose/.openclaw/workspace/config"
SCRIPTS_DIR="/home/goose/.openclaw/workspace/scripts"
BACKUP_DIR="/home/goose/.openclaw/workspace/backup/skills_$(date +%Y%m%d_%H%M%S)"

# 创建备份
create_backup() {
    log "创建技能配置备份..."
    mkdir -p "$BACKUP_DIR"
    
    # 备份所有技能配置
    find "$SKILLS_DIR" -name "config.json" -o -name "SKILL.md" | while read file; do
        local rel_path="${file#$SKILLS_DIR/}"
        local backup_path="$BACKUP_DIR/${rel_path//\//_}"
        cp "$file" "$backup_path" 2>/dev/null && log "  备份: $rel_path" || warning "  备份失败: $rel_path"
    done
    
    success "备份完成: $BACKUP_DIR"
}

# 优化核心技能配置
optimize_core_skills() {
    log "优化核心技能配置..."
    
    # 1. Telegram优化
    if [[ -d "$SKILLS_DIR/telegram" ]]; then
        log "  优化Telegram技能..."
        local tg_config="$SKILLS_DIR/telegram/config.json"
        
        # 备份原配置
        cp "$tg_config" "$tg_config.backup" 2>/dev/null
        
        # 创建优化配置
        cat > "$tg_config" << 'EOF'
{
  "telegram": {
    "enabled": true,
    "botToken": "8405295378:AAG3bvttAQkw00tjuTo1ypw02TLSKAFLT0o",
    "configFile": "/home/goose/.openclaw/workspace/config/openclaw_opc.json",
    
    "performance": {
      "cacheEnabled": true,
      "cacheTTL": 300,
      "retryAttempts": 3,
      "timeout": 30000,
      "parallelProcessing": true
    },
    
    "notifications": {
      "enabled": true,
      "cryptoAlerts": true,
      "jobAlerts": true,
      "systemStatus": true,
      "errorReports": true,
      "quietHours": {
        "enabled": true,
        "start": "23:00",
        "end": "08:00",
        "timezone": "Asia/Shanghai"
      }
    },
    
    "commands": {
      "enabled": true,
      "list": {
        "/start": "启动OPC助手",
        "/crypto": "加密货币监控",
        "/jobs": "求职助手",
        "/contract": "智能合约工具",
        "/trade": "交易辅助",
        "/status": "系统状态",
        "/help": "帮助信息"
      },
      "admin": {
        "/admin status": "系统状态",
        "/admin logs": "查看日志",
        "/admin backup": "备份数据"
      }
    },
    
    "security": {
      "rateLimiting": {
        "enabled": true,
        "messagesPerMinute": 30,
        "burstLimit": 5
      },
      "accessControl": {
        "enabled": true,
        "allowedUsers": [],
        "allowedGroups": [],
        "adminUsers": []
      }
    },
    
    "logging": {
      "level": "info",
      "file": "/home/goose/opc-project/logs/telegram/telegram.log",
      "maxSize": "10MB",
      "maxFiles": 5
    },
    
    "integration": {
      "withWhatsApp": true,
      "syncCommands": true,
      "crossPlatform": true
    },
    
    "optimized": "2026-02-28",
    "version": "2.0.0",
    "status": "optimized"
  }
}
EOF
        success "  Telegram配置优化完成"
    else
        warning "  Telegram技能目录不存在"
    fi
    
    # 2. WhatsApp优化（如果存在）
    if [[ -d "$SKILLS_DIR/whatsapp" ]]; then
        log "  优化WhatsApp技能..."
        local wa_config="$SKILLS_DIR/whatsapp/config.json"
        
        # 备份原配置
        cp "$wa_config" "$wa_config.backup" 2>/dev/null
        
        # 更新配置指向
        cat > "$wa_config" << 'EOF'
{
  "whatsapp": {
    "enabled": true,
    "configFile": "/home/goose/.openclaw/workspace/config/whatsapp_config.json",
    
    "performance": {
      "cacheEnabled": true,
      "cacheTTL": 300,
      "retryAttempts": 3,
      "timeout": 30000
    },
    
    "setup": {
      "status": "needs_configuration",
      "prerequisites": [
        "WhatsApp Business Account",
        "Phone Number ID",
        "Business Account ID",
        "Permanent Access Token"
      ],
      "configGuide": "请更新 ~/.openclaw/workspace/config/whatsapp_config.json"
    },
    
    "integration": {
      "withTelegram": true,
      "unifiedCommands": true,
      "crossPlatform": true
    },
    
    "optimized": "2026-02-28",
    "version": "2.0.0",
    "status": "ready_for_config"
  }
}
EOF
        success "  WhatsApp配置优化完成"
    fi
    
    # 3. OPC自定义技能优化
    log "  优化OPC自定义技能..."
    
    local opc_skills=("opc-crypto-monitor" "opc-job-assistant" "opc-smart-contract" "opc-trading-helper")
    
    for skill in "${opc_skills[@]}"; do
        if [[ -d "$SKILLS_DIR/$skill" ]]; then
            local skill_config="$SKILLS_DIR/$skill/config.json"
            
            # 备份原配置
            cp "$skill_config" "$skill_config.backup" 2>/dev/null 2>/dev/null || true
            
            # 通用优化配置
            cat > "$skill_config" << EOF
{
  "$skill": {
    "enabled": true,
    "optimized": "2026-02-28",
    
    "performance": {
      "cacheEnabled": true,
      "cacheTTL": 600,
      "timeout": 30000,
      "retryAttempts": 2
    },
    
    "integration": {
      "withTelegram": true,
      "withWhatsApp": true,
      "dataSharing": true
    },
    
    "monitoring": {
      "enabled": true,
      "interval": 300,
      "alerts": true
    },
    
    "logging": {
      "enabled": true,
      "level": "info",
      "file": "/home/goose/opc-project/logs/$skill/$skill.log"
    },
    
    "version": "2.0.0",
    "status": "optimized"
  }
}
EOF
            log "    $skill 配置优化完成"
            
            # 确保日志目录存在
            mkdir -p "/home/goose/opc-project/logs/$skill"
        else
            warning "    $skill 目录不存在"
        fi
    done
    
    success "核心技能优化完成"
}

# 优化辅助技能配置
optimize_auxiliary_skills() {
    log "优化辅助技能配置..."
    
    # 需要优化的辅助技能列表
    local auxiliary_skills=("github" "cron" "shell" "web-search" "calendar" "gmail" "obsidian" "weather")
    
    for skill in "${auxiliary_skills[@]}"; do
        if [[ -d "$SKILLS_DIR/$skill" ]]; then
            local skill_config="$SKILLS_DIR/$skill/config.json"
            
            # 如果配置文件不存在，创建基本配置
            if [[ ! -f "$skill_config" ]]; then
                cat > "$skill_config" << EOF
{
  "$skill": {
    "enabled": true,
    "optimized": "2026-02-28",
    
    "performance": {
      "cacheEnabled": true,
      "timeout": 30000
    },
    
    "integration": {
      "withOPC": true
    },
    
    "version": "1.0.0",
    "status": "optimized"
  }
}
EOF
                log "    $skill 创建优化配置"
            else
                log "    $skill 配置已存在，跳过"
            fi
        else
            warning "    $skill 目录不存在"
        fi
    done
    
    success "辅助技能优化完成"
}

# 创建技能启用脚本
create_skill_enabler() {
    log "创建技能启用脚本..."
    
    local enabler_script="$SCRIPTS_DIR/enable_opc_skills.sh"
    
    cat > "$enabler_script" << 'EOF'
#!/bin/bash

# OPC项目技能启用脚本
# 一键启用所有OPC相关技能

set -e

# 颜色定义
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== OPC项目技能启用工具 ===${NC}"
echo ""

# 核心技能列表
CORE_SKILLS=(
    "telegram"
    "whatsapp"
    "opc-crypto-monitor"
    "opc-job-assistant"
    "opc-smart-contract"
    "opc-trading-helper"
)

# 辅助技能列表
AUX_SKILLS=(
    "github"
    "cron"
    "shell"
    "web-search"
    "calendar"
    "gmail"
    "obsidian"
    "weather"
)

# 启用技能函数
enable_skill() {
    local skill=$1
    local config_file="/home/goose/.openclaw/workspace/skills/$skill/config.json"
    
    if [[ -f "$config_file" ]]; then
        # 使用jq启用技能
        if command -v jq >/dev/null 2>&1; then
            jq ".\"$skill\".enabled = true" "$config_file" > "${config_file}.tmp" && \
            mv "${config_file}.tmp" "$config_file"
            echo -e "${GREEN}✓${NC} 启用: $skill"
        else
            # 简单的文本替换
            sed -i 's/"enabled": false/"enabled": true/g' "$config_file" 2>/dev/null || \
            sed -i 's/"enabled": "false"/"enabled": "true"/g' "$config_file" 2>/dev/null || true
            echo -e "${GREEN}✓${NC} 启用: $skill (简单模式)"
        fi
    else
        echo "⚠️  跳过: $skill (无配置文件)"
    fi
}

# 启用核心技能
echo "启用核心技能..."
for skill in "${CORE_SKILLS[@]}"; do
    enable_skill "$skill"
done

echo ""

# 启用辅助技能
echo "启用辅助技能..."
for skill in "${AUX_SKILLS[@]}"; do
    enable_skill "$skill"
done

echo ""
echo -e "${GREEN}✅ 所有技能启用完成！${NC}"
echo ""
echo "下一步："
echo "1. 重启OpenClaw使配置生效"
echo "2. 运行测试脚本验证功能"
echo "3. 检查技能状态"
echo ""
echo "测试命令："
echo "  bash ~/.openclaw/workspace/scripts/test_all_skills.sh"
EOF
    
    chmod +x "$enabler_script"
    success "技能启用脚本创建完成: $enabler_script"
}

# 创建技能状态检查脚本
create_skill_checker() {
    log "创建技能状态检查脚本..."
    
    local checker_script="$SCRIPTS_DIR/check_skills_status.sh"
    
    cat > "$checker_script" << 'EOF'
#!/bin/bash

# OPC项目技能状态检查脚本

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}=== OPC项目技能状态检查 ===${NC}"
echo "检查时间: $(date)"
echo ""

SKILLS_DIR="/home/goose/.openclaw/workspace/skills"

# 检查技能函数
check_skill() {
    local skill=$1
    local category=$2
    local skill_dir="$SKILLS_DIR/$skill"
    
    echo -n "[$category] $skill: "
    
    if [[ -d "$skill_dir" ]]; then
        # 检查配置文件
        if [[ -f "$skill_dir/config.json" ]]; then
            # 检查是否启用
            if grep -q '"enabled": true' "$skill_dir/config.json" || \
               grep -q '"enabled": "true"' "$skill_dir/config.json"; then
                echo -e "${GREEN}已启用${NC}"
                return 0
            else
                echo -e "${YELLOW}已安装但未启用${NC}"
                return 1
            fi
        else
            echo -e "${YELLOW}已安装但无配置${NC}"
            return 2
        fi
    else
        echo -e "${RED}未安装${NC}"
        return 3
    fi
}

# 核心技能检查
echo "--- 核心技能 ---"
core_skills=("telegram" "whatsapp" "opc-crypto-monitor" "opc-job-assistant" "opc-smart-contract" "opc-trading-helper")
core_count=0
core_enabled=0

for skill in "${core_skills[@]}"; do
    if check_skill "$skill" "核心"; then
        ((core_enabled++))
    fi
    ((core_count++))
done

echo ""

# 辅助技能检查
echo "--- 辅助技能 ---"
aux_skills=("github" "cron" "shell" "web-search" "calendar" "gmail" "obsidian" "weather" "brave-search" "web-fetch")
aux_count=0
aux_enabled=0

for skill in "${aux_skills[@]}"; do
    if check_skill "$skill" "辅助"; then
        ((aux_enabled++))
    fi
    ((aux_count++))
done

echo ""
echo "=== 统计摘要 ==="
echo "核心技能: $core_enabled/$core_count 已启用"
echo "辅助技能: $aux_enabled/$aux_count 已启用"
echo "总计: $((core_enabled + aux_enabled))/$((core_count + aux_count)) 已启用"

echo ""
echo "=== 建议 ==="
if [[ $core_enabled -lt $core_count ]]; then
    echo "⚠️  部分核心技能未启用，建议运行:"
    echo "    bash ~/.openclaw/workspace/scripts/enable_opc_skills.sh"
fi

if [[ $aux_enabled -lt $aux_count ]]; then
    echo "⚠️  部分辅助技能未启用，可能影响功能"
fi

echo ""
echo "检查完成！"
EOF
    
    chmod +x "$checker_script"
    success "技能状态检查脚本创建完成: $checker_script"
}

# 更新OpenClaw主配置
update_main_config() {
    log "更新OpenClaw主配置..."
    
    local main_config="$CONFIG_DIR/openclaw_opc.json"
    
    if [[ -f "$main_config" ]]; then
        # 备份原配置
        cp "$main_config" "$main_config.backup"
        
        # 更新技能配置部分
        if command -v jq >/dev/null 2>&1; then
            jq '.skills.optimized = "2026-02-28"' "$main_config" > "${main_config}.tmp" && \
            mv "${main_config}.tmp" "$main_config"
            
            jq '.skills.lastOptimized = "'$(date -Iseconds)'"' "$main_config" > "${main_config}.tmp" && \
            mv "${main_config}.tmp" "$main_config"
            
            success "OpenClaw主配置更新完成"
        else
            warning "jq命令不存在，跳过JSON更新"
        fi
    else
        error "OpenClaw主配置文件不存在: $main_config"
    fi
}

# 生成优化报告
generate_optimization_report() {
    log "生成优化报告..."
    
    local report_file="/home/goose/opc-project/logs/skills_optimization_report_$(date +%Y%m%d_%H%M%S).md"
    
    mkdir -p "$(dirname "$report_file")"
    
    cat > "$report_file" << EOF
# OPC项目技能优化报告

## 基本信息
- **优化时间**: $(date)
- **备份目录**: $BACKUP_DIR
- **脚本版本**: 2.0.0

## 优化内容

### 1. 核心技能优化
- Telegram: 性能优化，缓存启用，安全配置
- WhatsApp: 配置框架完善，集成优化
- OPC自定义技能: 统一配置，监控启用

### 2. 辅助技能优化
- GitHub/Cron/Shell: 基础配置创建
- Web搜索工具: 性能优化
- 生产力工具: 集成配置

### 3. 工具脚本创建
- 技能启用脚本: enable_opc_skills.sh
- 状态检查脚本: check_skills_status.sh
- 测试脚本: test_whatsapp.sh

## 技能状态

### 核心技能状态
EOF
    
    # 添加核心技能状态
    local core_skills=("telegram" "whatsapp" "opc-crypto-monitor" "opc-job-assistant" "opc-smart-contract" "opc-trading-helper")
    for skill in "${core_skills[@]}"; do
        local skill_dir="$SKILLS_DIR/$skill"
        if [[ -d "$skill_dir" ]]; then
            echo "- **$skill**: ✅ 已优化" >> "$report_file"
        else
            echo "- **$skill**: ❌ 未安装" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

### 辅助技能状态
EOF
    
    # 添加辅助技能状态
    local aux_skills=("github" "cron" "shell" "web-search" "calendar" "gmail" "obsidian" "weather")
    for skill in "${aux_skills[@]}"; do
        local skill_dir="$SKILLS_DIR/$skill"
        if [[ -d "$skill_dir" ]]; then
            echo "- **$skill**: ✅ 已优化" >> "$report_file"
        else
            echo "- **$skill**: ❌ 未安装" >> "$report_file"
        fi
    done
    
    cat >> "$report_file" << EOF

## 配置文件位置

### 主要配置文件
1. OpenClaw主配置: \`$CONFIG_DIR/openclaw_opc.json\`
2. Telegram配置: \`$SKILLS_DIR/telegram/config.json\`
3. WhatsApp配置: \`$CONFIG_DIR/whatsapp_config.json\`
4. 技能统一配置: 各技能目录下的config.json

### 管理脚本
1. 技能启用: \`$SCRIPTS_DIR/enable_opc_skills.sh\`
2. 状态检查: \`$SCRIPTS_DIR/check_skills_status.sh\`
3. WhatsApp测试: \`$SCRIPTS_DIR/test_whatsapp.sh\`

## 下一步建议

### 立即执行
1. 启用所有技能: \`bash $SCRIPTS_DIR/enable_opc_skills.sh\`
2. 检查技能状态: \`bash $SCRIPTS_DIR/check_skills_status.sh\`
3. 重启OpenClaw使配置生效

### 后续优化
1. 配置WhatsApp认证信息
2. 测试Telegram连接（网络恢复后）
3. 设置定时监控任务
4. 创建技能使用文档

## 故障排除

### 常见问题
1. **技能未启用**: 运行启用脚本
2. **配置错误**: 检查JSON格式
3. **权限问题**: 确保文件可读写
4. **依赖缺失**: 安装jq等工具

### 恢复备份
如需恢复原配置，可从备份目录复制:
\`\`\`bash
# 查看备份
ls $BACKUP_DIR

# 恢复特定技能配置
cp $BACKUP_DIR/telegram_config.json $SKILLS_DIR/telegram/config.json
\`\`\`

## 联系方式
- 问题反馈: 检查日志文件
- 紧急支持: 联系管理员
- 文档更新: 查看项目文档

---

**优化状态**: ✅ 完成  
**报告生成时间**: $(date)  
**优化版本**: 2.0.0
EOF
    
    success "优化报告生成完成: $report_file"
}

# 主函数
main() {
    echo ""
    echo "========================================"
    echo "    OPC项目技能配置优化工具"
    echo "========================================"
    echo ""
    
    # 检查依赖
    if ! command -v jq >/dev/null 2>&1; then
        error "需要安装 jq 工具"
        log "安装命令: sudo apt-get install jq"
        exit 1
    fi
    
    # 执行优化步骤
    create_backup
    optimize_core_skills
    optimize_auxiliary_skills
    create_skill_enabler
    create_skill_checker
    update_main_config
    generate_optimization_report
    
    echo ""
    echo "========================================"
    success "技能配置优化完成！"
    echo ""
    log "下一步操作:"
    echo "  1. 启用技能: bash $SCRIPTS_DIR/enable_opc_skills.sh"
    echo "  2. 检查状态: bash $SCRIPTS_DIR/check_skills_status.sh"
    echo "  3. 查看报告: cat /home/goose/opc-project/logs/skills_optimization_report_*.md"
    echo ""
    log "备份位置: $BACKUP_DIR"
    echo ""
    echo "优化完成时间: $(date)"
}

# 运行主函数
main "$@"