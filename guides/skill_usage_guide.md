# OpenClaw技能使用指南
## 基于2026-02-28的经验总结

## 已安装技能分类

### 音频处理类
1. **speech-to-text** - 语音转文字
   - 来源: inference.sh
   - 使用: 自动处理.ogg音频文件
   - 输出: `transcriptions/`目录

2. **whisper** - OpenAI语音识别
   - 备用方案，支持99种语言

3. **faster-whisper** - 轻量级替代
   - 已成功安装，推荐使用
   - 脚本: `scripts/transcribe_with_faster_whisper.py`

### 搜索类
1. **brave-search** - Brave搜索
   - 隐私优先的网页搜索
   - 使用: `./search.js "query" -n 10 --content`
   - 无需API Key

2. **skillsmp-searcher** - SkillsMP搜索
   - 技能市场搜索
   - 需要API Key配置

3. **find-skills** - 技能发现
   - 主要技能搜索工具
   - 使用: `npx skills find <关键词>`

### 智能体增强类
1. **self-improving-agent** - 自我改进
   - 从经验中学习
   - 自动优化响应

2. **humanize** - 人性化
   - 优化文本输出
   - 使回复更自然

3. **effect-index** - 本体索引
   - 知识管理和组织

### 系统工具类
1. **openclaw-watchdog** - 监控
   - 系统状态监控

2. **ai-wrapper-product** - API包装
   - 包装第三方API

3. **skill-creator** - 技能创建
   - 创建自定义技能

### 通信类
1. **telegram** - Telegram集成
2. **whatsapp** - WhatsApp集成
3. **discord** - Discord集成

## 常用工作流

### 音频处理工作流
```
1. 发送.ogg音频文件
2. 自动转录到transcriptions/
3. 根据内容执行任务
4. 归档处理结果
```

### 技能安装工作流
```
1. 搜索: npx skills find <关键词>
2. 安装: npx skills add <来源> -y
3. 配置: 查看SKILL.md了解需求
4. 测试: 运行示例命令
```

### 搜索工作流
```
1. 网页搜索: brave-search "query"
2. 技能搜索: find-skills 或 skillsmp-searcher
3. 内容提取: ./content.js <URL>
```

## 最佳实践

### 安装技能时
1. **先搜索**: 使用find-skills查看选项
2. **看安装量**: 选择高安装量的版本
3. **检查安全**: 注意安全风险等级
4. **测试功能**: 安装后立即测试

### 处理问题时
1. **检查日志**: `openclaw logs`
2. **查看状态**: `openclaw status --deep`
3. **搜索解决方案**: 使用brave-search
4. **记录经验**: 更新记忆文件

### 优化交互时
1. **使用音频**: 发送.ogg文件更高效
2. **明确需求**: 清晰说明需要什么
3. **提供反馈**: 帮助智能体学习
4. **定期检查**: 使用heartbeat机制

## 故障排除

### 常见问题
1. **技能安装失败**
   - 检查网络连接
   - 尝试不同的技能来源
   - 查看错误日志

2. **音频处理问题**
   - 确认文件格式(.ogg)
   - 检查依赖安装(faster-whisper)
   - 查看transcriptions/目录

3. **搜索功能问题**
   - Brave搜索: 检查网络
   - SkillsMP: 配置API Key
   - 内容提取: 确认URL可访问

### 系统维护
1. **定期更新**
   ```bash
   openclaw update
   npx skills update
   ```

2. **备份配置**
   ```bash
   # 备份重要文件
   cp -r ~/.openclaw/workspace ~/backup/
   ```

3. **清理空间**
   ```bash
   # 清理旧日志和缓存
   ```

## 高级用法

### 技能组合
```bash
# 音频搜索组合
1. 发送音频查询
2. 转录为文本
3. 使用brave-search搜索
4. 返回搜索结果
```

### 自动化脚本
```bash
# 创建自定义脚本
# 参考: scripts/auto_audio_processor.sh
```

### 自定义技能
```bash
# 使用skill-creator
# 创建针对特定需求的技能
```

## 学习资源

### 官方文档
- OpenClaw: https://docs.openclaw.ai/
- ClawHub: https://clawhub.com/
- SkillsMP: https://skillsmp.com/

### 社区支持
- Discord: https://discord.com/invite/clawd
- GitHub: https://github.com/openclaw/openclaw

### 技能市场
1. **ClawHub** - 主要市场
2. **SkillsMP** - 备用市场
3. **GitHub** - 直接安装

## 下一步学习

### 推荐技能
1. **crypto-ta-analyzer** - 加密货币分析
2. **smart-contract-security** - 智能合约安全
3. **github** - GitHub集成
4. **workflow-automation** - 工作流自动化

### 学习路径
1. 掌握基础技能使用
2. 创建自动化工作流
3. 开发自定义技能
4. 优化系统性能

---

**最后更新**: 2026-02-28
**基于**: 今日的交互经验和学习