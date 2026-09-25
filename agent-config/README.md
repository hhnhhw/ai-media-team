# AI新媒体小编团队 - 千帆智能体配置包

本配置包包含将"AI新媒体小编团队"发布到百度千帆应用广场所需的所有配置文件。

---

## 📁 文件清单

```
agent-config/
├── qianfan-agent-import.json  # 千帆一键导入配置（推荐使用）
├── agent-profile.json         # 智能体基本信息配置
├── system-prompt.md           # 系统提示词（完整版）
├── tool-definitions.md        # 工具定义详细文档
├── publish-guide.md           # 千帆发布操作指南
└── README.md                  # 本文件
```

---

## 🚀 快速开始

### 方法一：一键导入（推荐）

1. 打开 `qianfan-agent-import.json`
2. 替换其中的环境变量：
   - `${COPYWRITER_SERVICE_URL}` → 你的文案AI服务地址
   - `${ILLUSTRATOR_SERVICE_URL}` → 你的配图AI服务地址
3. 在千帆控制台选择"导入配置"，上传该 JSON 文件

### 方法二：手动配置

按照 `publish-guide.md` 的步骤，逐项在千帆控制台填写配置。

---

## 📝 配置文件说明

### 1. qianfan-agent-import.json

**用途**: 千帆平台一键导入配置

**包含内容**:
- 智能体基本信息（名称、描述、图标等）
- 模型配置（DeepSeek-V4-Pro）
- 系统提示词（完整版）
- 工具定义（write_article、generate_illustration）
- 环境变量配置

**使用方法**:
```bash
# 1. 修改服务地址
vim qianfan-agent-import.json
# 将 COPYWRITER_SERVICE_URL 和 ILLUSTRATOR_SERVICE_URL 替换为实际地址

# 2. 在千帆控制台导入
# 进入：应用广场 → 创建应用 → 导入配置 → 选择此文件
```

### 2. agent-profile.json

**用途**: 智能体基本信息配置

**包含内容**:
- 应用名称、描述、分类
- 能力标签
- 使用场景示例
- 模型参数配置

**适用场景**: 手动创建智能体时参考

### 3. system-prompt.md

**用途**: 完整的系统提示词

**包含内容**:
- 角色设定
- 工作流程（四步法）
- 风格识别规则
- 实体提取规则
- 输出格式规范
- 注意事项

**适用场景**: 
- 直接复制到千帆的"系统提示词"配置区域
- 或作为 `qianfan-agent-import.json` 中 system_prompt 字段的来源

### 4. tool-definitions.md

**用途**: 工具定义详细文档

**包含内容**:
- 工具参数定义
- API 端点配置
- 调用示例
- 错误处理

**适用场景**: 
- 理解工具的工作原理
- 调试工具调用问题
- 扩展新工具时参考

### 5. publish-guide.md

**用途**: 千帆发布操作指南

**包含内容**:
- 发布前准备
- 后端服务部署
- 千帆配置步骤（详细）
- 测试与发布流程
- 常见问题解答

**适用场景**: 首次发布时按步骤操作

---

## 🔧 后端服务部署

### 前置要求

- Python 3.10+
- DeepSeek API Key
- Pexels API Key

### 部署步骤

```bash
# 1. 进入项目目录
cd D:\ai-media-team

# 2. 创建虚拟环境
python -m venv .venv
.venv\Scripts\activate  # Windows
# source .venv/bin/activate  # Linux/Mac

# 3. 安装依赖
pip install -r requirements.txt

# 4. 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的 API Key

# 5. 启动服务
python run_services.py
```

### 服务验证

```bash
# 测试文案AI服务
curl http://localhost:8001/health

# 测试配图AI服务
curl http://localhost:8002/health
```

---

## 🌐 云服务部署选项

### 选项 1: 百度云函数 CFC

**优点**: 
- 无需管理服务器
- 按调用计费
- 自动扩缩容

**步骤**:
1. 创建云函数
2. 上传代码包
3. 配置环境变量
4. 配置 API 网关触发器

**参考文档**: `publish-guide.md` → 后端服务部署 → 方案A

### 选项 2: 云服务器 BCC

**优点**: 
- 完全控制
- 适合长期稳定运行

**步骤**:
1. 购买云服务器
2. 安装 Python 环境
3. 部署代码
4. 使用 Supervisor 或 systemd 管理进程
5. 配置 Nginx 反向代理

### 选项 3: 容器服务 CCE

**优点**: 
- 适合微服务架构
- 便于扩展

**步骤**:
1. 编写 Dockerfile
2. 构建镜像
3. 推送到镜像仓库
4. 部署到 CCE 集群

---

## 🔑 环境变量配置

在千帆控制台配置以下环境变量：

| 变量名 | 说明 | 示例值 |
|--------|------|--------|
| COPYWRITER_SERVICE_URL | 文案AI服务地址 | https://api.your-domain.com/copywriter |
| ILLUSTRATOR_SERVICE_URL | 配图AI服务地址 | https://api.your-domain.com/illustrator |

---

## 📊 功能特性

### ✅ 已实现

- [x] 多平台风格适配（公众号、小红书、抖音、微博）
- [x] 多种写作风格（幽默、文艺、专业、种草风等）
- [x] 智能实体提取配图
- [x] 流式输出
- [x] 对话历史管理

### 🚧 计划中

- [ ] 支持用户上传参考图片
- [ ] 支持更多图库（Unsplash、Pixabay）
- [ ] 支持视频脚本生成
- [ ] 支持多语言（英文、日文等）

---

## 🐛 常见问题

### Q: 工具调用失败怎么办？

**检查项**:
1. 后端服务是否正常运行
2. API Key 是否配置正确
3. 服务地址是否填写正确
4. 网络是否连通

### Q: 配图搜索不准确怎么办？

**原因**: 实体提取不够精准

**解决**: 优化 `system-prompt.md` 中的实体提取规则

### Q: 如何切换大模型？

**方法**: 在 `qianfan-agent-import.json` 中修改 `model` 配置：
```json
{
  "model": {
    "provider": "baidu",
    "model": "ERNIE-Bot-4",
    "temperature": 0.8,
    "max_tokens": 4096
  }
}
```

---

## 📞 技术支持

- **千帆平台文档**: https://cloud.baidu.com/doc/WENXINWORKSHOP/index.html
- **项目 Issues**: 在项目仓库提 Issue
- **百度智能云客服**: 400-890-0088

---

## 📄 License

MIT License

---

**祝你发布成功！🎉**

如有问题，请参考 `publish-guide.md` 或联系技术支持。


[DuMate AI生成]