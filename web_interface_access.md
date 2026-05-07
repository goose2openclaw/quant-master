# OpenClaw Web界面访问指南

## 🎯 根据语音指令分析
**音频转录结果**: "访问web界面"  
**理解意图**: 访问OpenClaw的Web管理界面

## 🌐 当前运行的Web服务

### 1. **Mission Control 任务管理系统**
- **URL**: http://localhost:8080
- **状态**: ✅ 运行中 (Next.js 14.2.28)
- **用途**: 多智能体任务管理看板
- **功能**: 
  - 任务创建和分配
  - 智能体状态监控
  - 工作流可视化
  - 团队协作界面

### 2. **OpenClaw Gateway 管理界面**
- **URL**: http://localhost:18789
- **状态**: ✅ 运行中
- **用途**: OpenClaw系统管理
- **功能**:
  - 系统状态监控
  - 配置管理
  - 日志查看
  - 健康检查

## 🚀 快速访问方法

### 方法1: 直接浏览器访问
```bash
# 在浏览器中打开Mission Control
xdg-open http://localhost:8080  # Linux
open http://localhost:8080      # macOS
start http://localhost:8080     # Windows

# 在浏览器中打开Gateway
xdg-open http://localhost:18789
```

### 方法2: 命令行访问测试
```bash
# 测试Mission Control
curl -s http://localhost:8080 | grep -o "<title>[^<]*</title>"

# 测试Gateway健康检查
curl -s http://localhost:18789/api/health

# 获取Gateway信息
curl -s http://localhost:18789/api/info
```

### 方法3: 创建快捷访问脚本
```bash
#!/bin/bash
# web_access.sh

echo "选择要访问的Web界面:"
echo "1) Mission Control (任务管理)"
echo "2) OpenClaw Gateway (系统管理)"
echo "3) 两个都打开"
read -p "请输入选择 (1-3): " choice

case $choice in
    1)
        echo "打开 Mission Control..."
        xdg-open http://localhost:8080 2>/dev/null || echo "请手动访问: http://localhost:8080"
        ;;
    2)
        echo "打开 OpenClaw Gateway..."
        xdg-open http://localhost:18789 2>/dev/null || echo "请手动访问: http://localhost:18789"
        ;;
    3)
        echo "打开所有Web界面..."
        xdg-open http://localhost:8080 2>/dev/null &
        xdg-open http://localhost:18789 2>/dev/null &
        echo "Mission Control: http://localhost:8080"
        echo "OpenClaw Gateway: http://localhost:18789"
        ;;
    *)
        echo "无效选择"
        ;;
esac
```

## 📊 各界面功能详解

### Mission Control 界面 (http://localhost:8080)

#### 主要功能区域
1. **任务看板**
   - 待处理任务
   - 进行中任务  
   - 已完成任务
   - 阻塞任务

2. **智能体面板**
   - 8个OPC智能体状态
   - 任务分配情况
   - 工作效率统计

3. **任务创建区**
   - 快速创建新任务
   - 分配智能体
   - 设置优先级和截止时间

4. **统计面板**
   - 任务完成率
   - 智能体活跃度
   - 系统健康状态

#### API端点
```bash
# 获取所有任务
curl http://localhost:8080/api/tasks

# 获取特定智能体的任务
curl "http://localhost:8080/api/tasks/mine?agent=crypto-monitor"

# 创建新任务
curl -X POST http://localhost:8080/api/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"测试任务","description":"这是一个测试","assignee":"lead"}'
```

### OpenClaw Gateway 界面 (http://localhost:18789)

#### 主要功能
1. **系统状态**
   - 进程监控
   - 资源使用
   - 网络连接

2. **配置管理**
   - 查看当前配置
   - 修改配置参数
   - 配置验证

3. **日志查看**
   - 实时日志流
   - 日志过滤
   - 错误追踪

4. **健康检查**
   - 组件健康状态
   - 服务可用性
   - 性能指标

#### API端点
```bash
# 健康检查
curl http://localhost:18789/api/health

# 系统信息
curl http://localhost:18789/api/info

# 配置信息
curl http://localhost:18789/api/config
```

## 🔧 高级访问配置

### 1. 远程访问配置
```bash
# 如果需要从其他设备访问，可以配置端口转发
ssh -L 8080:localhost:8080 user@remote-host  # Mission Control
ssh -L 18789:localhost:18789 user@remote-host # Gateway

# 或者使用ngrok创建临时公开URL
ngrok http 8080  # Mission Control
ngrok http 18789 # Gateway
```

### 2. 安全访问配置
```bash
# 添加基本认证
# 在OpenClaw配置中添加
{
  "gateway": {
    "auth": {
      "enabled": true,
      "username": "admin",
      "password": "secure-password"
    }
  }
}
```

### 3. 监控仪表板集成
```bash
# 将OpenClaw指标集成到Grafana
# 创建Prometheus数据源
# 配置监控面板显示:
# - 任务处理速度
# - 智能体响应时间
# - 系统资源使用
# - API调用成功率
```

## 📱 移动设备访问

### 1. 本地网络访问
```bash
# 查找本机IP地址
ip addr show | grep "inet " | grep -v "127.0.0.1"

# 示例: 如果IP是192.168.1.100
# 手机浏览器访问:
# Mission Control: http://192.168.1.100:8080
# Gateway: http://192.168.1.100:18789
```

### 2. 响应式设计支持
- **Mission Control**: 支持移动端响应式布局
- **Gateway界面**: 基础移动端支持
- **建议**: 横屏模式获得最佳体验

### 3. 移动端快捷方式
```bash
# 生成二维码方便手机扫描
qrencode -t ANSI "http://localhost:8080"
qrencode -t ANSI "http://localhost:18789"
```

## 🛠️ 故障排除

### 常见问题及解决方案

#### 1. 无法访问localhost
```bash
# 检查服务是否运行
ss -tulpn | grep -E "(8080|18789)"

# 检查防火墙
sudo ufw status
sudo ufw allow 8080
sudo ufw allow 18789

# 检查绑定地址
# 确保服务绑定到0.0.0.0而不是127.0.0.1
```

#### 2. 页面加载缓慢
```bash
# 检查系统资源
top -b -n 1 | grep -E "(node|openclaw)"

# 检查网络延迟
ping localhost

# 清理浏览器缓存
```

#### 3. API调用失败
```bash
# 测试API端点
curl -v http://localhost:8080/api/tasks
curl -v http://localhost:18789/api/health

# 检查CORS设置
# 在配置中添加CORS头
```

#### 4. 界面显示异常
```bash
# 检查JavaScript控制台错误
# 在浏览器中按F12打开开发者工具

# 检查Next.js构建状态
cd /home/goose/.openclaw/mission-control-app
npm run build

# 重启服务
bash /home/goose/.openclaw/workspace/scripts/restart_openclaw_optimized.sh
```

## 🎯 最佳实践

### 1. 日常使用建议
- **书签保存**: 将常用界面添加到浏览器书签
- **多标签页**: 同时打开两个界面方便切换
- **快捷键**: 使用浏览器快捷键快速导航
- **自动刷新**: 对监控页面设置自动刷新

### 2. 安全建议
- **本地访问**: 尽量在本地网络访问
- **HTTPS**: 生产环境启用HTTPS
- **访问控制**: 设置适当的访问权限
- **日志监控**: 监控异常访问尝试

### 3. 性能优化
- **缓存策略**: 合理配置浏览器缓存
- **资源压缩**: 启用Gzip压缩
- **连接复用**: 使用HTTP/2或HTTP/3
- **懒加载**: 对大型页面启用懒加载

## 📈 监控和告警

### 1. 健康检查脚本
```bash
#!/bin/bash
# web_health_check.sh

echo "=== Web界面健康检查 ==="
echo "检查时间: $(date)"
echo ""

# 检查Mission Control
echo "1. Mission Control (8080):"
if curl -s -f http://localhost:8080 > /dev/null; then
    echo "  ✅ 运行正常"
    # 获取版本信息
    VERSION=$(curl -s http://localhost:8080 | grep -o "Next.js [0-9.]*" | head -1)
    echo "  版本: $VERSION"
else
    echo "  ❌ 无法访问"
fi

echo ""

# 检查OpenClaw Gateway
echo "2. OpenClaw Gateway (18789):"
if curl -s -f http://localhost:18789 > /dev/null; then
    echo "  ✅ 运行正常"
    # 获取健康状态
    HEALTH=$(curl -s http://localhost:18789/api/health | python3 -c "import json,sys; print(json.load(sys.stdin).get('status', '未知'))")
    echo "  健康状态: $HEALTH"
else
    echo "  ❌ 无法访问"
fi

echo ""
echo "=== 检查完成 ==="
```

### 2. 自动化监控
```bash
# 添加到cron定时检查
crontab -l | grep -q "web_health_check" || echo "*/5 * * * * /home/goose/.openclaw/workspace/scripts/web_health_check.sh >> /var/log/openclaw_web_health.log" | crontab -
```

### 3. 告警配置
```bash
# 如果服务异常，发送通知
if ! curl -s -f http://localhost:8080 > /dev/null; then
    # 发送Telegram通知
    curl -s -X POST "https://api.telegram.org/botYOUR_BOT_TOKEN/sendMessage" \
        -d "chat_id=YOUR_CHAT_ID" \
        -d "text=⚠️ Mission Control服务异常，请检查！"
fi
```

## 🎨 界面定制

### 1. Mission Control主题定制
```javascript
// 在Mission Control项目中自定义主题
// mission-control-app/app/globals.css
:root {
  --opc-primary: #4f46e5;
  --opc-secondary: #10b981;
  --opc-background: #f9fafb;
}

// 重新构建应用
cd /home/goose/.openclaw/mission-control-app
npm run build
```

### 2. 自定义仪表板
```bash
# 创建自定义监控面板
# 集成到Mission Control或独立部署
# 使用React + Chart.js创建可视化
```

### 3. 多语言支持
```bash
# 如果需要多语言界面
# 配置i18n支持
# 添加中文/英文切换
```

## 📞 支持资源

### 官方文档
- **Mission Control文档**: https://docs.openclaw.ai/mission-control
- **Gateway API文档**: https://docs.openclaw.ai/api/gateway
- **故障排除指南**: https://docs.openclaw.ai/troubleshooting/web

### 社区资源
- **Discord社区**: https://discord.com/invite/clawd
- **GitHub Issues**: https://github.com/openclaw/openclaw/issues
- **示例项目**: https://github.com/openclaw/examples

### 工具推荐
- **浏览器扩展**: React Developer Tools, Redux DevTools
- **API测试**: Postman, Insomnia, curl
- **监控工具**: Prometheus, Grafana, Datadog

---

**最后更新**: 2026-03-01 05:35  
**状态**: ✅ 两个Web界面都在运行，可以正常访问  
**Mission Control**: http://localhost:8080 (任务管理系统)  
**OpenClaw Gateway**: http://localhost:18789 (系统管理界面)  
**下一步**: 打开浏览器访问，或使用提供的脚本快速访问