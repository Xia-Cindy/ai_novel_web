# AI 小说风格仿写生成系统

本项目是一个本地可运行的作者工作台：输入灵感后，可一键生成完整大纲、精美封面、正文内容和多线路剧情走向；也支持私有样章学文风、拆书仿写、审稿、章节情报汇总、角色关系网、历史记录和每日签到字数。

## 目录结构

```text
ai_novel_web/
├── backend/
│   ├── main.py
│   ├── analyzer.py
│   ├── llm.py
│   ├── prompt_engine.py
│   └── models.py
├── frontend/
│   ├── index.html
│   ├── app.js
│   └── style.css
├── data/
│   └── reference.txt
├── requirements.txt
└── README.md
```

## 运行方式

```bash
cd ai_novel_web
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn backend.main:app --reload --host 127.0.0.1 --port 8000
```

打开浏览器访问：

```text
http://127.0.0.1:8000
```

## 可选：接入 OpenAI

不设置 API Key 时，系统会使用本地演示生成器，方便完整跑通流程。要接入 OpenAI，可设置：

```bash
export OPENAI_API_KEY="你的 API Key"
export OPENAI_MODEL="gpt-4.1-mini"
```

然后重新启动服务。

## 永久版功能

- 一键生成：完整大纲、封面、正文、剧情走向
- 私有库配置：上传或粘贴样章，分析并模仿文风
- 公有库配置：内置爽文升级、悬疑反转、情绪虐恋、群像权谋等底层逻辑
- 模块化配置：可选择文风和剧情模板
- 角色关系网：前端可视化拖拽
- 章节情报：自动汇总主线、支线、感情线、势力线和风险点
- 拆书功能：输出结构、钩子、冲突和仿写规则
- 审稿功能：AI 检测风险、亮点和修改意见
- 平台资讯：本地版提供查询框架、关键词和行动建议
- 历史记录：生成内容写入 `data/history.json`
- 签到任务：每日领取 2500 字
- 响应式页面：手机、平板、电脑通用

## API

- `POST /upload_reference`：上传 TXT 文件或粘贴参考文本
- `POST /analyze_reference`：输出结构化文风分析 JSON
- `POST /generate_world`：生成世界观
- `POST /generate_plot`：生成剧情大纲
- `POST /generate_outline`：生成完整大纲
- `POST /generate_novel`：生成第一章正文
- `POST /generate_cover`：生成 SVG 小说封面
- `POST /generate_directions`：生成多线路剧情走向
- `POST /generate_all`：一键生成大纲、封面、正文、走向
- `POST /deconstruct_book`：拆书仿写分析
- `POST /review_text`：审稿
- `POST /summarize_chapter`：章节情报汇总
- `POST /query_info`：平台资讯查询建议
- `POST /daily_checkin`：每日签到领取字数
- `GET /history`：读取历史记录
- `GET /public_libraries`：读取公有库配置
- `GET /cache_state`：查看当前缓存状态
- `GET /health`：健康检查

## 说明

- 后端使用内存缓存 `reference_cache` 保存参考文本与文风分析结果。
- 参考文本会同步保存到 `data/reference.txt`，服务重启时会自动载入。
- 所有生成请求都要求先完成文风分析。
- 所有提示词统一由 `backend/prompt_engine.py` 构建。
- 模型调用统一封装在 `backend/llm.py`。
- 当前平台资讯为本地知识框架，不抓取实时网页；如需实时资讯，可在 `backend/features.py` 的 `query_info` 接入搜索 API。
