# Paper + GitHub 知识爬虫系统 — 设计文档

**日期:** 2026-06-29
**状态:** 已确认

---

## 1. 目标

自动化爬取计算机视觉领域的最新论文和 GitHub 项目，通过 Web 面板浏览筛选，每日/每周生成 Markdown 报告。帮助了解前沿进展，筛选有价值的工作进行复现。

## 2. 覆盖范围

### 数据源
- arxiv (cs.CV, cs.AI, cs.LG, cs.MM, cs.CL 等)
- GitHub Trending + 特定 topic (computer-vision, deep-learning, object-detection 等)
- Papers With Code (排行榜 + 最新论文)
- 顶会 proceedings (CVPR, ICCV, ECCV, NeurIPS, ICML, ICLR 等，通过 dblp / OpenReview)

### 关注的 CV 方向
- 图像分类 / 目标检测 / 分割
- 生成模型（扩散模型、GAN）
- 3D 视觉 / NeRF / 高斯泼溅
- 多模态 / 视觉语言模型（VLM）
- 视频理解 / 目标跟踪
- 及更多

### 交付方式
- **Web 面板** — 浏览器浏览、搜索、筛选、打标签
- **日报/周报** — 定时生成 Markdown 报告

## 3. 整体架构

模块化单体（Modular Monolith），Python 后端 + React 前端前后端分离。

```
React (Vite + TypeScript + Tailwind)
      │  REST API
      ▼
FastAPI Backend
├── Scheduler (APScheduler)  — 定时调度
├── Crawler Registry         — 爬虫插件注册
│   ├── ArxivCrawler
│   ├── GitHubCrawler
│   ├── PWCCrawler
│   └── ConfCrawler
├── Report Engine            — 生成 Markdown 报告
├── Storage (SQLAlchemy)     — ORM 抽象层
└── Database
    ├── SQLite (本地开发)
    └── PostgreSQL (服务器部署)
```

**关键决策：**
- 每个爬虫实现统一接口（`fetch → normalize → upsert`），新增来源只需加一个文件
- SQLAlchemy 抽象数据库，SQLite ↔ PostgreSQL 只需一行配置
- Docker 容器化，一键部署

## 4. 数据模型

### Paper
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID | 主键 |
| title | TEXT | 标题 |
| abstract | TEXT | 摘要 |
| url | TEXT | 论文 URL |
| pdf_url | TEXT | PDF 直链 |
| code_url | TEXT | 关联代码链接 |
| source | VARCHAR(32) | arxiv / pwc / dblp |
| source_id | VARCHAR(128) | 来源方唯一标识 |
| venue | VARCHAR(256) | 发表 venue |
| published_date | DATE | 发表日期 |
| crawled_at | TIMESTAMP | 爬取时间 |

### Author
| 字段 | 类型 |
|------|------|
| id | UUID PK |
| name | TEXT UNIQUE |
| affiliation | TEXT |

### PaperAuthor
| 字段 | 类型 |
|------|------|
| paper_id | FK → Paper |
| author_id | FK → Author |
| author_order | INT |

### Category
| 字段 | 类型 |
|------|------|
| id | UUID PK |
| name | TEXT |
| source | VARCHAR(32) |

### PaperCategory
| 字段 | 类型 |
|------|------|
| paper_id | FK → Paper |
| category_id | FK → Category |

### GitHubRepo
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| full_name | TEXT UNIQUE | owner/name |
| description | TEXT | |
| url | TEXT | |
| stars | INT | |
| forks | INT | |
| language | VARCHAR(64) | |
| topics | JSON | |
| pushed_at | TIMESTAMP | |
| crawled_at | TIMESTAMP | |
| last_crawled_at | TIMESTAMP | |

### UserTag
| 字段 | 类型 |
|------|------|
| id | UUID PK |
| name | TEXT |
| color | VARCHAR(7) |

### PaperTag / RepoTag
多对多关联表。

### CrawlLog
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| source | VARCHAR(32) | 爬虫名 |
| started_at | TIMESTAMP | |
| finished_at | TIMESTAMP | |
| items_found | INT | |
| status | VARCHAR(16) | success/partial/failed |
| error_message | TEXT | |

### Report
| 字段 | 类型 | 说明 |
|------|------|------|
| id | UUID PK | |
| type | VARCHAR(16) | daily/weekly |
| date_range_start | DATE | |
| date_range_end | DATE | |
| file_path | TEXT | 生成路径 |
| paper_count | INT | |
| repo_count | INT | |
| generated_at | TIMESTAMP | |

### 索引
- Paper: `(source, source_id)` UNIQUE — 去重；`published_date DESC` — 按日期浏览；`crawled_at` — 增量查询
- Author: `name` UNIQUE
- PaperAuthor: `(paper_id, author_id)` UNIQUE
- Category: `(source, name)` UNIQUE
- GitHubRepo: `full_name` UNIQUE — 去重；`stars DESC` / `pushed_at DESC` — 热度/活跃度排序
- CrawlLog: `(source, started_at)` — 历史查询
- Report: `(type, generated_at DESC)` — 最近报告列表

## 5. 爬虫系统

### 统一接口
```python
class BaseCrawler(ABC):
    source: str
    async def fetch(self, params) -> list[dict]
    async def normalize(self, raw) -> Paper | GitHubRepo
    async def run(self, db)  # 模板方法
```

### 具体爬虫

| 爬虫 | 来源 | 频率 |
|------|------|------|
| ArxivCrawler | arxiv API | 每 6h |
| GitHubCrawler | GitHub API + Trending | 每 2h |
| PWCCrawler | Papers With Code | 每天 |
| ConfCrawler | dblp / OpenReview | 每 3 天 |

### 去重与增量
- `source + source_id` 唯一索引 → upsert 语义
- GitHub `full_name` 唯一，`pushed_at` 判断更新
- CrawlLog 记录每次爬取状态

### 反爬与容错
- 请求间隔 1-3s 随机延迟
- GitHub API 带 token，429 自动退避重试
- 单爬虫异常不影响其他爬虫

## 6. 报告引擎

| 类型 | 触发 | 内容 |
|------|------|------|
| 日报 | 每晚 22:00 | 当日新论文 Top + 新 GitHub 热门 |
| 周报 | 每周一早 10:00 | 周精选 + rising 项目 + 分类统计 |

流程：Scheduler 触发 → 查询 DB → 按分类分组排序 → Jinja2 渲染 Markdown → 保存到 `reports/` → Report 表记录

## 7. 前端

- **技术栈:** React 18 + TypeScript + Vite + Tailwind CSS
- **页面:** 论文 / GitHub 项目 / 报告（Markdown 渲染）/ 标签管理
- **交互:** 来源/分类多选筛选、时间范围筛选、关键词搜索、点击外链跳转、自定义标签

## 8. 部署

- 本地开发：FastAPI + SQLite + Vite dev server
- 服务器部署：Docker Compose (FastAPI + PostgreSQL + Nginx 静态文件)
- 迁移工具：Alembic

## 9. 排除范围

- 用户登录/多用户
- 论文全文解析
- 社交分享
- 移动端适配（初期不做）
