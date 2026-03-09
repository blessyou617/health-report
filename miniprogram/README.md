# AI 体检报告分析小程序

微信原生小程序 + 后端 API

## 页面结构

```
pages/
├── index/          # 首页
├── upload/         # 上传报告
├── questionnaire/ # 问卷调查
├── loading/       # 分析中
├── report/        # 报告展示
└── chat/          # 追问聊天
```

## 功能

1. **首页** - 展示功能介绍和最近报告
2. **上传** - 支持 PDF/JPG/PNG 体检报告
3. **问卷** - 填写生活习惯问卷
4. **分析中** - 动画展示 AI 分析过程
5. **报告** - 展示分析结果，支持语音播报
6. **追问** - 与 AI 对话，最多 2 次

## 使用说明

1. 打开微信开发者工具
2. 导入项目
3. 修改 `app.js` 中的 `baseUrl` 为你的后端 API 地址
4. 修改 `project.config.json` 中的 `appid`
5. 编译运行

## API 对接

确保后端 API 已部署，并配置以下接口：

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | /api/v1/auth/login | 微信登录 |
| POST | /api/v1/upload/report | 上传文件 |
| POST | /api/v1/questionnaire/submit | 提交问卷 |
| POST | /api/v1/analyze/report/{id} | AI 分析 |
| POST | /api/v1/qa/ask | 追问 |
| GET | /api/v1/report/{id} | 获取报告 |
| POST | /api/v1/tts/report/{id} | 生成语音 |

## 图片资源

需要在 `images/` 目录下添加：

- home.png / home-active.png
- report.png / report-active.png
- upload.png
- ai.png
- voice.png
- chat.png
- camera.png
- logo.png
- file.png
- ai-avatar.png
- play.png
- stop.png
- send.png
- summary.png
- warning.png
- check.png
- advice.png
- chat-white.png
- upload-add.png
- ai-brain.png

## 配置

在 `app.js` 中修改：

```javascript
globalData: {
  baseUrl: 'https://your-api-domain.com/api/v1'
}
```
