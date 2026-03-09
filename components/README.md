# 体检报告 UI 组件库

适合中老年阅读的体检报告组件

## 组件列表

### 1. 健康总结卡片 (health-summary)
- 渐变紫色背景
- 大字体显示总结
- 语音播放按钮
- 适合中老年的大间距设计

### 2. 异常指标卡片 (abnormal-list)
- 红色警告标识
- 点击可查看详情
- 清晰的列表项
- 底部提示信息

### 3. 正常指标列表 (normal-list)
- 绿色成功标识
- 简洁的列表样式
- 适合快速浏览

### 4. 生活建议卡片 (lifestyle-advice)
- 绿色渐变背景
- 语音播报按钮
- 分享给家人按钮
- 追问 AI 按钮

## 设计特点

- **大字体**: 32-36rpx 适合中老年
- **清晰间距**: 24-32rpx 间距
- **高对比度**: 颜色鲜明易读
- **大按钮**: 方便点击
- **简洁排版**: 减少视觉负担

## 使用方法

```json
{
  "usingComponents": {
    "health-summary": "/components/health-summary/health-summary",
    "abnormal-list": "/components/abnormal-list/abnormal-list",
    "normal-list": "/components/normal-list/normal-list",
    "lifestyle-advice": "/components/lifestyle-advice/lifestyle-advice"
  }
}
```

```xml
<health-summary 
  summary="{{summary}}"
  bind:voiceplay="onVoicePlay"
/>

<abnormal-list 
  items="{{abnormalItems}}"
  bind:itemtap="onItemTap"
/>

<normal-list items="{{normalItems}}" />

<lifestyle-advice 
  advice="{{advice}}"
  bind:voiceplay="onVoicePlay"
  bind:askquestion="onAskQuestion"
/>
```

## 事件

| 组件 | 事件 | 说明 |
|------|------|------|
| health-summary | voiceplay | 语音播放点击 |
| abnormal-list | itemtap | 点击异常指标 |
| lifestyle-advice | voiceplay | 语音播报点击 |
| lifestyle-advice | share | 分享点击 |
| lifestyle-advice | askquestion | 追问点击 |
