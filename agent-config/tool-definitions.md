# 工具定义文件

本文档定义了AI新媒体小编团队可用的工具。

---

## 工具 1: write_article（文案写作工具）

### 基本信息
- **工具名称**: `write_article`
- **工具描述**: 撰写各种风格的文章、推文、种草笔记。支持公众号、小红书、抖音、微博等多平台风格。
- **调用方式**: HTTP POST 请求
- **超时时间**: 120秒

### 参数定义

```json
{
  "type": "object",
  "properties": {
    "topic": {
      "type": "string",
      "description": "文章主题，例如：'哈尔滨冰雪大世界旅游攻略'、'春季穿搭推荐'",
      "required": true
    },
    "style": {
      "type": "string",
      "description": "写作风格，例如：'幽默风趣'、'文艺清新'、'专业严谨'、'小红书种草风'",
      "default": "轻松幽默，吸引眼球",
      "enum": [
        "轻松幽默，吸引眼球",
        "小红书种草风，emoji丰富，亲切活泼",
        "短小精悍，节奏感强，爆点前置",
        "简洁有力，话题性强",
        "幽默风趣，段子手风格",
        "专业严谨，深度分析",
        "文艺清新，温柔治愈"
      ]
    },
    "word_count": {
      "type": "integer",
      "description": "目标字数",
      "default": 800,
      "minimum": 300,
      "maximum": 3000
    },
    "platform": {
      "type": "string",
      "description": "发布平台",
      "default": "公众号",
      "enum": ["公众号", "小红书", "抖音", "微博", "知乎", "B站"]
    }
  },
  "required": ["topic"]
}
```

### 返回格式

```json
{
  "success": true,
  "title": "文章标题",
  "content": "文章正文（Markdown格式）",
  "word_count": 850,
  "platform": "公众号"
}
```

### API 端点

```
POST {YOUR_SERVICE_URL}/copywriter/generate
Content-Type: application/json
```

---

## 工具 2: generate_illustration（配图搜索工具）

### 基本信息
- **工具名称**: `generate_illustration`
- **工具描述**: 根据文章内容搜索高质量配图。支持从Pexels等图库搜索真实照片。
- **调用方式**: HTTP POST 请求
- **超时时间**: 180秒

### 参数定义

```json
{
  "type": "object",
  "properties": {
    "prompt": {
      "type": "string",
      "description": "文章中的具体实体列表（逗号分隔的名词）。重要：必须从文章正文中提取具体的、可拍摄的实体，例如：'北京烤鸭, 全聚德, 烤鸭师傅切片, 油亮酥皮特写'。不要使用抽象概念或完整句子。",
      "required": true,
      "examples": [
        "北京烤鸭, 全聚德, 烤鸭师傅切片, 油亮酥皮特写, 荷叶饼卷鸭肉",
        "哈尔滨冰雪大世界, 冰雪城堡夜景, 冰雕灯光秀, 雪雕艺术",
        "春季穿搭, 风衣外套, 牛仔裤, 小白鞋, 针织衫"
      ]
    },
    "style": {
      "type": "string",
      "description": "图片风格",
      "default": "真实摄影",
      "enum": ["真实摄影", "插画风格", "极简风格", "文艺风格"]
    }
  },
  "required": ["prompt"]
}
```

### 返回格式

```json
{
  "success": true,
  "image_url": "https://images.pexels.com/photos/xxx.jpeg",
  "image_urls": [
    "https://images.pexels.com/photos/xxx.jpeg",
    "https://images.pexels.com/photos/yyy.jpeg"
  ],
  "prompt_used": "北京烤鸭, 全聚德, 烤鸭师傅切片",
  "search_query": "北京烤鸭, 全聚德, 烤鸭师傅切片",
  "source": "Pexels (2 张)"
}
```

### API 端点

```
POST {YOUR_SERVICE_URL}/illustrator/generate
Content-Type: application/json
```

---

## 工具调用示例

### 示例 1: 撰写公众号推文

**用户输入:**
```
帮我写一篇关于北京烤鸭的公众号推文
```

**工具调用序列:**

1. 调用 `write_article`:
```json
{
  "topic": "北京烤鸭",
  "style": "轻松幽默，吸引眼球",
  "word_count": 800,
  "platform": "公众号"
}
```

2. 从生成的文章中提取实体，调用 `generate_illustration`:
```json
{
  "prompt": "北京烤鸭, 全聚德, 烤鸭师傅切片, 油亮酥皮特写, 荷叶饼卷鸭肉",
  "style": "真实摄影"
}
```

### 示例 2: 撰写小红书种草笔记

**用户输入:**
```
写一篇小红书笔记推荐哈尔滨冰雪大世界
```

**工具调用序列:**

1. 调用 `write_article`:
```json
{
  "topic": "哈尔滨冰雪大世界推荐",
  "style": "小红书种草风，emoji丰富，亲切活泼",
  "word_count": 600,
  "platform": "小红书"
}
```

2. 从生成的文章中提取实体，调用 `generate_illustration`:
```json
{
  "prompt": "哈尔滨冰雪大世界, 冰雪城堡夜景, 冰雕灯光秀, 雪雕艺术, 冰滑梯",
  "style": "真实摄影"
}
```

---

## 错误处理

### 工具调用失败时的处理

1. **文案AI服务不可用**: 返回错误信息，建议用户检查服务状态
2. **配图AI服务不可用**: 返回错误信息，但仍输出完整文案（无配图）
3. **参数验证失败**: 返回详细的错误信息，指导用户修正

### 错误返回格式

```json
{
  "success": false,
  "error": "错误类型",
  "message": "详细错误信息",
  "suggestion": "解决建议"
}
```


[DuMate AI生成]