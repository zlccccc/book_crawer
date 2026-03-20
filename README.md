# Novel Crawler

小说爬虫项目，用于从各大小说网站抓取小说内容。

## 目录结构

```
crawler/
├── src/           # 源代码
│   ├── base_crawler.py
│   ├── crawler_77shuwu.py
│   ├── crawler_huanghelou.py
│   └── utils.py
├── scripts/       # 脚本
│   ├── run_crawler.py
│   └── convert_novel_to_json.py
├── special_novel_tools/  # 特殊小说处理工具
│   └── json_to_txt.py
├── tests/         # 测试
├── docs/          # 文档
├── output/        # 爬虫结果输出
└── pyproject.toml
```

## 安装

```bash
cd ~/python/crawler
uv sync
```

## 运行

```bash
python scripts/run_crawler.py
```

## 测试

```bash
pytest tests/
```
