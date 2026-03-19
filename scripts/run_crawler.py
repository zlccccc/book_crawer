#!/usr/bin/env python3
"""爬虫运行脚本 - 简化爬虫启动"""

import argparse
import inspect
import os
import sys


def main():
    """主函数"""
    # 获取项目根目录并添加到路径
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, root_dir)
    os.chdir(root_dir)

    from src.crawler_77shuwu import SevenSevenShuWuCrawler
    from src.crawler_huanghelou import HuangHeLouCrawler

    crawlers = {
        "77shuwu": SevenSevenShuWuCrawler,
        "huanghelou": HuangHeLouCrawler,
    }

    parser = argparse.ArgumentParser(
        description="小说爬虫运行脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  # 使用77读书网爬虫
  python scripts/run_crawler.py 77shuwu --homepage_url "http://www.77shuku.org/novel/62042/"

  # 使用黄鹤楼文学爬虫
  python scripts/run_crawler.py huanghelou --homepage_url "https://www.hhlwx.org/hhlchapter/69730.html"

  # 启用调试模式
  python scripts/run_crawler.py 77shuwu --debug_enabled true

  # 限制爬取章节数
  python scripts/run_crawler.py 77shuwu --max_chapters 50
        """
    )

    parser.add_argument(
        "crawler",
        choices=list(crawlers.keys()),
        help="选择要使用的爬虫"
    )

    # 解析爬虫特定参数
    args, remaining = parser.parse_known_args()

    # 使用选定爬虫的参数解析器，只解析剩余的参数
    crawler_class = crawlers[args.crawler]
    # 保存原始的 argv
    original_argv = sys.argv.copy()
    try:
        # 临时替换 argv 为剩余的参数
        sys.argv = [sys.argv[0]] + remaining
        crawler_args = crawler_class.parse_args()
    finally:
        # 恢复原始的 argv
        sys.argv = original_argv

    # 创建并运行爬虫
    print(f"使用爬虫: {args.crawler}")
    print(f"目标URL: {crawler_args.homepage_url}")
    print(f"最大章节数: {crawler_args.max_chapters}")
    print("-" * 50)

    # 获取 __init__ 方法的签名
    init_signature = inspect.signature(crawler_class.__init__)
    init_params = list(init_signature.parameters.keys())

    # 准备参数
    crawler_kwargs = {
        'homepage_url': crawler_args.homepage_url,
        'base_url': crawler_args.base_url,
        'max_chapters': crawler_args.max_chapters,
        'max_retries': crawler_args.max_retries,
        'debug_dir': crawler_args.debug_dir,
        'debug_enabled': crawler_args.debug_enabled,
        'clear_files': crawler_args.clear_files,
    }

    # 添加缓存相关参数（如果 __init__ 方法接受）
    if 'enable_cache' in init_params:
        crawler_kwargs['enable_cache'] = getattr(crawler_args, 'enable_cache', True)
    if 'cache_size' in init_params:
        crawler_kwargs['cache_size'] = getattr(crawler_args, 'cache_size', 100)

    # 创建爬虫实例
    crawler = crawler_class(**crawler_kwargs)

    crawler.crawl()


if __name__ == "__main__":
    main()
