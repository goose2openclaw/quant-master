# OpenClaw 摄像头控制能力配置指南

## 🎯 根据语音指令分析
**音频转录结果**: "让opencl的获得控制摄像头的能"  
**理解意图**: 让OpenClaw获得控制摄像头的能力

## 📋 OpenClaw摄像头控制功能概述

### 已内置的功能
OpenClaw通过`nodes`工具已经内置了完整的摄像头控制能力：

#### 1. **摄像头拍照**
```bash
# 从配对节点拍照
openclaw nodes camera snap --node <节点ID>

# 指定摄像头方向
openclaw nodes camera snap --node <节点ID> --facing front    # 前置摄像头
openclaw nodes camera snap --node <节点ID> --facing back     # 后置摄像头
openclaw nodes camera snap --node <节点ID> --facing both     # 前后摄像头都拍

# 控制图片质量
openclaw nodes camera snap --node <节点ID> --maxWidth 1920 --quality 85
```

#### 2. **摄像头录像**
```bash
# 录制短视频
openclaw nodes camera clip --node <节点ID> --duration 5s

# 录制带音频的视频
openclaw nodes camera clip --node <节点ID> --duration 10s --includeAudio

# 控制帧率
openclaw nodes camera clip --node <节点ID> --duration 15s --fps 30
```

#### 3. **屏幕录制**
```bash
# 录制屏幕
openclaw nodes screen record --node <节点ID> --duration 10s

# 指定屏幕索引
openclaw nodes screen record --node <节点ID> --screenIndex 0 --duration 5s
```

## 🔧 配置步骤

### 步骤1: 节点配对
摄像头控制需要先配对设备节点：

#### 1.1 检查待配对节点
```bash
openclaw nodes pending
```

#### 1.2 安装OpenClaw节点应用
- **iOS**: 从App Store安装"OpenClaw Node"
- **Android**: 从Google Play安装"OpenClaw Node"
- **macOS**: 使用Homebrew安装: `brew install openclaw-node`
- **Windows**: 从GitHub Releases下载安装包

#### 1.3 配对流程
1. 在设备上打开OpenClaw Node应用
2. 应用会显示配对码
3. 在OpenClaw CLI中批准配对:
   ```bash
   openclaw nodes approve <配对请求ID>
   ```

### 步骤2: 验证配对状态
```bash
# 查看已配对节点
openclaw nodes status

# 查看节点详情
openclaw nodes describe --node <节点ID>
```

### 步骤3: 测试摄像头功能
```bash
# 测试前置摄像头
openclaw nodes camera snap --node <节点ID> --facing front

# 测试后置摄像头
openclaw nodes camera snap --node <节点ID> --facing back

# 测试录像功能
openclaw nodes camera clip --node <节点ID> --duration 3s
```

## 🚀 自动化摄像头控制

### 1. 创建摄像头控制脚本
```bash
#!/bin/bash
# camera_control.sh

NODE_ID="$1"
ACTION="$2"

case $ACTION in
    "photo-front")
        openclaw nodes camera snap --node $NODE_ID --facing front --maxWidth 1920
        ;;
    "photo-back")
        openclaw nodes camera snap --node $NODE_ID --facing back --maxWidth 1920
        ;;
    "video-5s")
        openclaw nodes camera clip --node $NODE_ID --duration 5s --includeAudio
        ;;
    "video-10s")
        openclaw nodes camera clip --node $NODE_ID --duration 10s --includeAudio
        ;;
    "screen-record")
        openclaw nodes screen record --node $NODE_ID --duration 10s
        ;;
    *)
        echo "用法: $0 <节点ID> <动作>"
        echo "可用动作: photo-front, photo-back, video-5s, video-10s, screen-record"
        ;;
esac
```

### 2. 集成到Telegram Bot
创建Telegram命令处理摄像头控制：

```python
# telegram_camera_bot.py
import subprocess
import json

def handle_camera_command(command, node_id):
    """处理摄像头命令"""
    commands = {
        "拍照": f"openclaw nodes camera snap --node {node_id} --facing back",
        "自拍": f"openclaw nodes camera snap --node {node_id} --facing front",
        "录像5秒": f"openclaw nodes camera clip --node {node_id} --duration 5s",
        "录像10秒": f"openclaw nodes camera clip --node {node_id} --duration 10s",
        "录屏": f"openclaw nodes screen record --node {node_id} --duration 10s"
    }
    
    if command in commands:
        result = subprocess.run(commands[command], shell=True, capture_output=True, text=True)
        return result.stdout
    else:
        return "未知命令，可用命令: " + ", ".join(commands.keys())
```

### 3. 定时摄像头任务
```bash
# 创建定时拍照任务
cat > ~/.openclaw/cron/daily_camera_check.json << 'EOF'
{
  "name": "每日摄像头检查",
  "enabled": true,
  "schedule": {"kind": "every", "everyMs": 86400000},
  "payload": {
    "channel": "telegram",
    "to": "user",
    "sessionTarget": "isolated",
    "message": "执行每日摄像头检查。使用nodes工具测试前后摄像头。"
  }
}
EOF
```

## 🛡️ 安全和隐私考虑

### 1. 权限控制
```bash
# 只允许特定节点访问摄像头
openclaw nodes rename --node <节点ID> "客厅摄像头"
openclaw nodes rename --node <另一个节点ID> "办公室摄像头"
```

### 2. 使用日志
```bash
# 启用摄像头使用日志
openclaw gateway logs --filter "camera"
```

### 3. 隐私保护措施
1. **明确告知**: 每次使用摄像头前发送通知
2. **权限确认**: 需要用户确认才能访问摄像头
3. **数据加密**: 传输的媒体文件加密
4. **自动删除**: 设置媒体文件自动删除时间

## 📱 实际应用场景

### 1. 家庭安防监控
```bash
# 安防监控脚本
#!/bin/bash
# security_monitor.sh

NODE_ID="客厅摄像头"

# 每小时拍照检查
openclaw nodes camera snap --node $NODE_ID --facing back
openclaw nodes camera snap --node $NODE_ID --facing front

# 检测到运动时录像（需要运动检测传感器）
# openclaw nodes camera clip --node $NODE_ID --duration 30s
```

### 2. 远程工作协助
```bash
# 远程协助脚本
#!/bin/bash
# remote_assist.sh

NODE_ID="工作电脑"

# 分享屏幕
openclaw nodes screen record --node $NODE_ID --duration 60s --fps 15

# 拍摄工作环境
openclaw nodes camera snap --node $NODE_ID --facing back
```

### 3. 宠物监控
```bash
# 宠物监控脚本
#!/bin/bash
# pet_monitor.sh

NODE_ID="宠物区域摄像头"

# 定时拍摄宠物照片
openclaw nodes camera snap --node $NODE_ID --facing back

# 检测到声音时录像（需要声音检测）
# openclaw nodes camera clip --node $NODE_ID --duration 10s --includeAudio
```

## 🔍 故障排除

### 常见问题及解决方案

#### 1. 节点未连接
```bash
# 检查节点状态
openclaw nodes status

# 重启节点应用
openclaw nodes invoke --node <节点ID> --command "restart"
```

#### 2. 摄像头权限被拒绝
```bash
# 检查节点权限
openclaw nodes describe --node <节点ID>

# 在设备上手动授予摄像头权限
```

#### 3. 媒体文件无法保存
```bash
# 检查存储权限
openclaw nodes invoke --node <节点ID> --command "checkStorage"

# 清理旧文件
openclaw nodes invoke --node <节点ID> --command "cleanupMedia"
```

#### 4. 网络连接问题
```bash
# 测试网络连接
openclaw nodes invoke --node <节点ID> --command "pingGateway"

# 检查防火墙设置
```

## 📊 性能优化建议

### 1. 媒体质量设置
```bash
# 平衡质量和速度的设置
openclaw nodes camera snap --node <节点ID> --maxWidth 1280 --quality 75
openclaw nodes camera clip --node <节点ID> --duration 5s --fps 15
```

### 2. 网络优化
```bash
# 使用较低分辨率减少带宽
openclaw nodes camera snap --node <节点ID> --maxWidth 640
```

### 3. 存储管理
```bash
# 自动清理旧文件
openclaw nodes invoke --node <节点ID> --command "autoCleanup --days 7"
```

## 🎯 快速开始指南

### 5分钟快速配置
1. **安装节点应用**: 在手机上安装OpenClaw Node
2. **启动配对**: 在节点应用中点击"配对"
3. **批准配对**: `openclaw nodes approve <请求ID>`
4. **测试摄像头**: `openclaw nodes camera snap --node <节点ID>`
5. **集成到工作流**: 创建自动化脚本

### 常用命令速查
```bash
# 查看节点
openclaw nodes status

# 拍照
openclaw nodes camera snap --node <ID> --facing back

# 录像
openclaw nodes camera clip --node <ID> --duration 5s

# 录屏
openclaw nodes screen record --node <ID> --duration 10s

# 发送通知
openclaw nodes notify --node <ID> --title "摄像头已启用" --body "正在拍摄照片"
```

## 📞 支持资源

### 官方文档
- **OpenClaw Nodes文档**: https://docs.openclaw.ai/cli/nodes
- **摄像头API参考**: https://docs.openclaw.ai/api/nodes-camera
- **故障排除指南**: https://docs.openclaw.ai/troubleshooting/nodes

### 社区支持
- **Discord社区**: https://discord.com/invite/clawd
- **GitHub Issues**: https://github.com/openclaw/openclaw/issues
- **示例项目**: https://github.com/openclaw/examples

---

**最后更新**: 2026-03-01 05:30  
**状态**: ✅ OpenClaw已具备摄像头控制能力，需要配对节点设备  
**下一步**: 安装OpenClaw Node应用并配对设备，然后测试摄像头功能