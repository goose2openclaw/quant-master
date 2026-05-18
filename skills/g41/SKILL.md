# G41 - Active Skill Management

## 版本
**v1.2** - Active Skill Management

## 核心架构

```
G41 v1.2 Active Skill Management
         |
         +-- ActiveSkillManager
         |       |
         |       +-- 动态权重调整
         |       +-- 胜率追踪 (W/L)
         |       +-- 技能激活/休眠
         |       +-- 市场自适应
         |
         +-- 10个go技能 (动态)
         +-- Polymarket (30%)
```

## Active Skill Management

### 动态权重调整
- 根据技能胜率自动调整权重
- 胜率>60% → 权重+20%
- 胜率<40% → 权重-20%
- 胜率<30% → 技能休眠

### 市场自适应
| 市场 | 增强技能 | 减弱技能 |
|------|----------|----------|
| 趋势 | go-core, go-long-short | go-pool |
| 震荡 | go-pool, go-rotate | go-core |
| 突破 | go-detect, go-core | go-contrarian |

### 技能激活状态
- 实时追踪每个技能的W/L
- 动态启用/休眠技能
- 表现好的技能获得更高权重

## 信号公式

```
综合信号 = go技能(动态权重) x 70% + Polymarket x 30%
```

## 版本对比

| 版本 | 特性 |
|------|------|
| v1.0 | Polymarket基础 |
| v1.1 | go技能调度 |
| **v1.2** | **Active Skill Management** |

## 启动

```bash
./start_g41.sh
```

## GitHub
- Branch: g12branch
- 版本: v1.2
