# CV Research Crawler

**帮你自动追踪CV领域最新论文和GitHub项目，用本地AI写中英文摘要。省下刷arxiv的时间，专注真正重要的事。**

<p align="center">
  <img src="screenshots/dashboard.png" width="45%" alt="Dashboard" />
  </p>
  <img src="screenshots/papers.png" width="45%" alt="Papers" />
</p>

---

## 为什么做这个工具？

每天打开arxiv，CV分类下又多了200篇新论文。快速扫标题、点开几篇读摘要、判断价值——一小时没了。三天后隐约记得有篇论文讲了你关心的问题，但想不起来是哪篇。

**这个工具解决的就是这个：自动收集、AI理解、分类存储、随时检索。**

---

## 它做什么？

| 你的痛点 | 它怎么解决 |
|----------|-----------|
| 论文太多看不完 | 爬下来后用**本地大模型**自动生成中文摘要，3-5句话看懂一篇 |
| 搜索太宽泛，找不到想要的 | 输入"3D视觉"，AI自动扩展出NeRF、Gaussian Splatting等十几个细分关键词，**精准筛选** |
| 看完就忘，找不到 | 自定义**彩色标签**（"必读"/"轻量化"/"代码开源"），打标后秒筛选 |
| 每天手动刷arxiv/GitHub | **全自动定时爬取**，arxiv每6小时、GitHub每2小时，打开网页就有结果 |
| 英文摘要读着累 | **中英双语摘要**自动生成，理解用中文，引用用英文 |
| 界面只有英文 | 一键**中英切换**，所有文字、按钮、标签全切换 |

---

## 核心功能

- **自动爬取** — arxiv 5个CV分类 + GitHub 9个CV主题，定时全自动，也可一键手动触发
- **AI摘要** — 本地Ollama大模型生成中英双语摘要，**免费、离线、不限量**
- **关键词扩展** — 输入研究方向 → AI生成细分关键词 → 勾选 → 只爬你关心的
- **智能筛选** — 不匹配关键词的内容不入库，过滤噪音
- **中英双语** — 全界面一键切换，150+文本项全覆盖
- **定时报告** — 每晚10点日报 + 每周一10点周报，Markdown格式
- **标签管理** — 16色调色板，论文/仓库均可打自定义标签
- **全文搜索** — FTS5全文检索，支持来源、分类、日期、标签多维度组合筛选

| Dashboard | Papers Browser |
|-----------|---------------|
| ![Dashboard](screenshots/dashboard.png) | ![Papers](screenshots/papers.png) |

| Crawl Scheduler | Keyword Management |
|----------------|-------------------|
| ![Crawls](screenshots/crawls.png) | ![Keywords](screenshots/keywords.png) |

---

## 不需要API Key，完全本地运行

只需要装一个 [Ollama](https://ollama.com)，下载任意开源模型：

```bash
ollama pull qwen3.5   # 中文能力强
# 或
ollama pull gemma4    # 速度快
```

工具自动调用Ollama生成摘要和扩展关键词。**不花钱、不联网、数据全在你本地。**

---

## 5分钟跑起来

```bash
git clone https://github.com/chenacc1/cv-research-crawler.git
cd cv-research-crawler

# 后端
cd backend
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# 前端（新终端）
cd frontend
npm install && npm run dev
```

打开 http://localhost:5173，从下载到看到论文数据不超过10分钟。

---

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端 | Python 3.12+ / FastAPI / SQLAlchemy 2.0 / APScheduler |
| 前端 | React 18 / TypeScript / Tailwind CSS 4 / Vite 6 |
| 数据库 | SQLite WAL模式 (默认) / PostgreSQL (可选) |
| AI模型 | Ollama (本地) / 任意OpenAI兼容API |
| 部署 | Docker Compose 一键部署 |

---

## 配置

编辑 `backend/.env`：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `LLM_API_BASE` | `http://localhost:11434` | Ollama或OpenAI API地址 |
| `LLM_MODEL` | `gemma4:e4b` | 模型名称 |
| `LLM_SUMMARY_ENABLED` | `true` | 是否启用AI摘要 |
| `CRAWLER_ARXIV_INTERVAL_MINUTES` | `360` | arxiv爬取间隔 |
| `CRAWLER_GITHUB_INTERVAL_MINUTES` | `120` | GitHub爬取间隔 |
| `GITHUB_TOKEN` | — | GitHub API Token（可选，提升限额） |

---

## License

MIT
