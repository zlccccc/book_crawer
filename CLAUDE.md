# Novel Crawler - 小说爬虫系统

可扩展的 Python 小说爬虫框架，支持多网站爬取。

## 项目结构

```
crawer/
├── src/                      # 源代码
│   ├── base_crawler.py       # 爬虫基类（抽象）
│   ├── crawer_77shuwu.py     # 77读书网
│   ├── crawer_huanghelou.py  # 黄鹤楼文学
│   └── utils.py              # 工具函数
├── tests/                    # 测试目录
│   ├── test_crawler.py       # 单元测试
│   └── test_integration.py   # 集成测试
├── scripts/                  # 运行脚本
│   ├── run_crawler.py        # 爬虫运行脚本
│   ├── run_tests.py          # 测试运行脚本
│   └── run_lint.py           # 代码检查脚本
├── skills/                   # 操作文档
│   ├── new-crawler.md        # 开发新爬虫
│   ├── debug-site.md         # 调试网站
│   ├── troubleshooting.md    # 故障排查
│   └── git-workflow.md       # Git 工作流
├── pyproject.toml            # 项目配置
├── book/                     # 存储目录
└── crawer_result/            # 结果目录（JSON + TXT）
```

## 快速开始

### 安装依赖

```bash
uv sync  # 或 pip install -r requirements.txt
```

### 运行爬虫

```bash
# 统一运行脚本（推荐）
python scripts/run_crawler.py 77shuwu --homepage_url "http://www.77shuku.org/novel/62042/"
python scripts/run_crawler.py huanghelou --homepage_url "https://www.hhlwx.org/hhlchapter/69730.html"

# 启用调试/限制章节数
python scripts/run_crawler.py 77shuwu --debug_enabled true --max_chapters 50
```

### 运行测试

**每次修改代码后必须运行测试**：

```bash
# 运行所有测试
python scripts/run_tests.py

# 或单独运行
python tests/test_crawler.py        # 单元测试
python tests/test_integration.py    # 集成测试
```

### 代码检查

**提交代码前运行代码检查**：

```bash
python scripts/run_lint.py
```

包括：Ruff 代码风格检查、Mypy 类型检查、测试

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

在 `src/` 下创建文件，继承 `BaseCrawler`：

```python
# src/my_crawler.py
from typing import List, Tuple
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler

class MySiteCrawler(BaseCrawler):
    def get_page_urls(self, url: str) -> Tuple[str, List[Tuple[str, str]]]:
        response = self._send_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        title = soup.find('h1').text.strip()
        chapters = [(link.text.strip(), self.base_url + link['href'])
                    for link in soup.select('.chapter-link')]
        return title, chapters

    def get_chapter_content(self, url: str) -> Tuple[str, str]:
        response = self._send_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        return soup.find('h1').text.strip(), soup.find('div', class_='content').get_text()

    @classmethod
    def parse_args(cls):
        import argparse
        parser = argparse.ArgumentParser(description='我的小说爬虫')
        parser.add_argument('--homepage_url', type=str, default='http://example.com/novel/1')
        parser.add_argument('--base_url', type=str, default='http://example.com')
        return parser.parse_args()

if __name__ == "__main__":
    MySiteCrawler.main()
```

在 `run_crawler.py` 中注册：

```python
from src.my_crawler import MySiteCrawler
CRAWLERS = {"77shuwu": SevenSevenShuWuCrawler, "huanghelou": HuangHeLouCrawler, "mysite": MySiteCrawler}
```

## 核心功能

- **断点续爬** - 基于 JSON 文件自动恢复
- **自动重试** - 失败递增延迟重试
- **标题规范化** - 统一章节标题格式
- **随机延迟** - 防反爬机制
- **调试模式** - 保存 HTML 便于分析

## 输出文件

- `{小说名}.json` - 章节数据（断点续爬）
- `{小说名}.txt` - 完整小说文本

## 注意事项

1. **每次修改代码后必须运行测试**：`python tests/test_crawler.py`
2. 遵守网站 robots.txt 和服务条款
3. 建议先少量测试再全量爬取
4. 新增爬虫时添加单元测试
