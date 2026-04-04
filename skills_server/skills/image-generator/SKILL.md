---
name: "image-generator"
description: "使用字节跳动Seedream API生成图片。调用场景：用户要求生成图片、配图、插图时使用。"
---

# 图片生成技能 (Image Generator)

使用字节跳动 Seedream API 生成图片。

## 功能

- 调用字节跳动 Seedream 图片生成模型生成图片
- 支持自定义图片描述、尺寸
- 图片自动保存到 data/images 目录
- 返回 Web 访问路径

## 使用方法

当用户需要生成图片时，调用 `generate_image` 工具：

### 工具参数

| 参数 | 类型 | 必填 | 说明 |
|-----|------|------|------|
| prompt | string | 是 | 图片描述文本 |
| size | string | 否 | 图片尺寸，可选: 1K, 2K, 4K，默认: 2K |
| watermark | boolean | 否 | 是否添加水印，默认: true |

### 返回结果

```json
{
  "status": "success",
  "message": "图片生成成功",
  "filepath": "d:\\anaconda\\envs\\agent\\my_agent\\data\\images\\image_20260302_153246.jpg",
  "web_path": "/data/images/image_20260302_153246.jpg"
}
```

## 配置

- API Key: `35e01833-c9da-41f0-bb82-7432f18c1987`
- 模型: `doubao-seedream-5-0-260128`
- 图片保存路径: `d:\anaconda\envs\agent\my_agent\data\images`

## 测试

```bash
python d:\anaconda\envs\agent\my_agent\agent_skill\skills\image-generator\generate.py "一只可爱的橘猫"
```
