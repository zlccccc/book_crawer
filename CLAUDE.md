# Novel Crawler - 小说爬虫系统

可扩展的 Python 小说爬虫框架，支持多网站爬取。

## 项目结构

```text
crawler/
├── src/                      # 源代码
│   ├── __init__.py           # 包初始化
│   ├── base_crawler.py       # 爬虫基类（抽象）
│   ├── config.py             # 配置与常量
│   ├── crawler_77shuwu.py    # 77 书屋爬虫
│   ├── crawler_huanghelou.py # 黄鹤楼文学爬虫
│   └── utils.py              # 工具函数
├── scripts/                  # 运行与检查脚本
│   ├── convert_novel_to_json.py
│   ├── run_crawler.py
│   ├── run_lint.py
│   └── run_tests.py
├── special_novel_tools/      # 特殊小说处理工具
│   └── json_to_txt.py        # JSON 转 TXT 工具
├── tests/                    # 测试目录
│   ├── test_crawler.py       # 单元测试
│   └── test_integration.py   # 集成测试
├── docs/                     # 使用与排障文档
│   ├── debug-site.md
│   ├── git-workflow.md
│   ├── new-crawler.md
│   └── troubleshooting.md
├── output/                   # 爬虫结果输出目录
├── pyproject.toml            # 项目配置
├── uv.lock                   # 依赖锁文件
└── README.md                 # 项目说明
```

## 快速开始

### 安装依赖

```bash
uv sync --extra dev
```

### 运行爬虫

```bash
python scripts/run_crawler.py 77shuwu --homepage_url "http://www.77shuku.org/novel/62042/"
python scripts/run_crawler.py huanghelou --homepage_url "https://www.hhlwx.org/hhlchapter/69730.html"
```

### 运行测试

```bash
python scripts/run_tests.py
```

### 代码检查

```bash
uv run python scripts/run_lint.py
```

包括：Ruff 代码风格检查、Mypy 类型检查、测试。

## 命令行参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `--homepage_url` | 爬虫默认值 | 小说主页 URL |
| `--base_url` | 爬虫默认值 | 网站基础 URL |
| `--max_chapters` | 100000 | 最大爬取章节数 |
| `--max_retries` | 3 | 每章节最大重试次数 |
| `--debug_enabled` | False | 是否启用调试模式 |
| `--clear_files` | False | 爬取前是否清空已存在文件 |

## 开发新爬虫

在 `src/` 下创建文件，继承 `BaseCrawler`，并在 `scripts/run_crawler.py` 中注册。
详细步骤见 `docs/new-crawler.md`。

## 核心功能

- 断点续爬：基于 JSON 文件自动恢复
- 自动重试：失败递增延迟重试
- 标题规范化：统一章节标题格式
- 随机延迟：降低请求频率
- 调试模式：保存 HTML 便于分析

## 输出文件

- `output/{小说名}.json`：章节数据（断点续爬）
- `output/{小说名}.txt`：完整小说文本

## 注意事项

1. 每次修改代码后运行 `python scripts/run_tests.py`。
2. 提交前运行 `uv run python scripts/run_lint.py`。
3. 遵守网站 robots.txt 和服务条款。
4. 建议先少量测试再全量爬取。
