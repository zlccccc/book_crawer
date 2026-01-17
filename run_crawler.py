#!/usr/bin/env python3
"""爬虫运行脚本 - 简化爬虫启动"""

import sys
import os

# 添加 src 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

import argparse
from src.crawer_77shuwu import SevenSevenShuWuCrawler
from src.crawer_huanghelou import HuangHeLouCrawler


# 爬虫映射
CRAWLERS = {
    "77shuwu": SevenSevenShuWuCrawler,
    "huanghelou": HuangHeLouCrawler,
}


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="小说爬虫运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用77读书网爬虫
  python run_crawler.py 77shuwu --homepage_url "http://www.77shuku.org/novel/62042/"

  # 使用黄鹤楼文学爬虫
  python run_crawler.py huanghelou --homepage_url "https://www.hhlwx.org/hhlchapter/69730.html"

  # 启用调试模式
  python run_crawler.py 77shuwu --debug_enabled true

  # 限制爬取章节数
  python run_crawler.py 77shuwu --max_chapters 50
        """
    )

    parser.add_argument(
        "crawler",
        choices=list(CRAWLERS.keys()),
        help="选择要使用的爬虫"
    )

    # 解析爬虫特定参数
    args, remaining = parser.parse_known_args()

    # 使用选定爬虫的参数解析器
    crawler_class = CRAWLERS[args.crawler]
    crawler_args = crawler_class.parse_args()

    # 创建并运行爬虫
    print(f"使用爬虫: {args.crawler}")
    print(f"目标URL: {crawler_args.homepage_url}")
    print(f"最大章节数: {crawler_args.max_chapters}")
    print("-" * 50)

    crawler = crawler_class(
        homepage_url=crawler_args.homepage_url,
        base_url=crawler_args.base_url,
        max_chapters=crawler_args.max_chapters,
        max_retries=crawler_args.max_retries,
        debug_dir=crawler_args.debug_dir,
        debug_enabled=crawler_args.debug_enabled,
        clear_files=crawler_args.clear_files,
    )

    crawler.crawl()


if __name__ == "__main__":
    main()
