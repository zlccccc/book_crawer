from __future__ import annotations

import argparse
import json
import os
from abc import ABC, abstractmethod
from types import SimpleNamespace
from typing import Any, cast

import requests
from tqdm import tqdm

from .utils import (
    load_existing_json,
    normalize_chapter_title,
    random_delay,
    save_chapter_to_json,
    save_debug_html,
    save_novel_to_txt,
    setup_logger,
)


class BaseCrawler(ABC):
    """爬虫基类，提供通用爬虫功能"""

    # 默认请求头
    DEFAULT_HEADERS = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 '
                      '(KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }

    def __init__(
        self,
        homepage_url: str,
        base_url: str,
        max_chapters: int = 100000,
        max_retries: int = 3,
        debug_dir: str = "debug_html",
        debug_enabled: bool = False,
        clear_files: bool = True,
        enable_cache: bool = True,
        cache_size: int = 100,
    ) -> None:
        """初始化爬虫

        Args:
            homepage_url: 小说主页URL
            base_url: 网站基础URL
            max_chapters: 最大爬取章节数
            max_retries: 每个章节的最大重试次数
            debug_dir: 调试文件保存目录
            debug_enabled: 是否启用调试模式
            clear_files: 是否在爬取前清空已存在的文件
            enable_cache: 是否启用缓存机制
            cache_size: 缓存大小
        """
        self.homepage_url = homepage_url
        self.base_url = base_url
        self.max_chapters = max_chapters
        self.max_retries = max_retries
        self.debug_dir = debug_dir
        self.debug_enabled = debug_enabled
        self.clear_files = clear_files
        self.enable_cache = enable_cache
        self.cache_size = cache_size
        self.cache: dict[str, str] = {}
        self.logger = setup_logger()
        self.headers = self.DEFAULT_HEADERS.copy()

    @abstractmethod
    def get_page_urls(self, url: str) -> tuple[str, list[tuple[str, str]]]:
        """获取章节链接列表

        Args:
            url: 页面URL

        Returns:
            (小说标题, [(章节标题, 章节URL), ...])

        需要在子类中实现
        """
        raise NotImplementedError("子类必须实现get_page_urls方法")

    @abstractmethod
    def get_chapter_content(self, url: str) -> tuple[str, str]:
        """获取章节内容

        Args:
            url: 章节URL

        Returns:
            (章节标题, 章节内容)

        需要在子类中实现
        """
        raise NotImplementedError("子类必须实现get_chapter_content方法")

    def clear_existing_files(self, title: str) -> None:
        """清空已存在的json和txt文件

        Args:
            title: 小说标题
        """
        files = {
            f"{title}.json": '{}',
            f"{title}.txt": '',
        }

        for filepath, content in files.items():
            if os.path.exists(filepath):
                try:
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    self.logger.info(f"已清空 {filepath}")
                except OSError as e:
                    self.logger.error(f"清空文件失败 {filepath}: {e}")

    def crawl(self) -> None:
        """执行爬取流程"""
        try:
            # 获取章节列表
            content_title, page_urls = self.get_page_urls(self.homepage_url)
            self.logger.info(f"开始爬取小说: {content_title}")

            # 根据配置决定是否清空已存在的文件
            if self.clear_files:
                self.clear_existing_files(content_title)
                self.logger.info("已启用清空现有文件功能")
            else:
                self.logger.info("已禁用清空现有文件功能")

            # 加载已存在的数据
            json_content = load_existing_json(content_title)
            crawled_count = len(json_content)

            # 计算需要爬取的章节数
            remaining_chapters = self.max_chapters - crawled_count
            if remaining_chapters <= 0:
                self.logger.info(f"已爬取章节数达到最大限制 {self.max_chapters}，无需继续爬取")
                return

            # 过滤出未爬取的章节
            normalized_titles = []
            uncrawled_chapters: dict[str, str] = {}
            for title, url in page_urls:
                normalized_title, _ = normalize_chapter_title(title, 1)
                normalized_titles.append(normalized_title)
                if normalized_title not in json_content:
                    uncrawled_chapters[title] = url

            # 限制爬取章节数
            chapters_to_crawl = list(uncrawled_chapters.items())[:remaining_chapters]
            self.logger.info(f"需要爬取 {len(chapters_to_crawl)} 个章节")

            # 爬取章节
            self._crawl_chapters(
                chapters_to_crawl, content_title, json_content, normalized_titles
            )

            self.logger.info("爬取完成!")

            # 保存为TXT文件
            save_novel_to_txt(content_title, normalized_titles, json_content)

        except requests.RequestException as err:
            self.logger.error(f"网络请求失败: {err}")
            self._save_debug_html_on_error()
        except json.JSONDecodeError as err:
            self.logger.error(f"JSON解析错误: {err}")
        except FileNotFoundError as err:
            self.logger.error(f"文件不存在: {err}")
        except PermissionError as err:
            self.logger.error(f"权限错误: {err}")
        except Exception as err:
            self.logger.error(f"爬取失败: {err}")
            import traceback
            self.logger.error(f"异常详情: {traceback.format_exc()}")
            self._save_debug_html_on_error()

    def _crawl_chapters(
        self,
        chapters_to_crawl: list[tuple[str, str]],
        content_title: str,
        json_content: dict[str, str],
        normalized_titles: list[str],
    ) -> None:
        """爬取章节内容

        Args:
            chapters_to_crawl: 待爬取的章节列表 [(标题, URL), ...]
            content_title: 小说标题
            json_content: 已爬取的内容字典
            normalized_titles: 规范化的标题列表
        """
        page_num = 1

        for title, page_url in tqdm(chapters_to_crawl, desc="爬取章节"):
            # 规范化章节标题
            normalized_title, page_num = normalize_chapter_title(title, page_num)

            # 跳过已爬取的章节（双重检查）
            if normalized_title in json_content:
                continue

            # 实现重试逻辑
            self._fetch_chapter_with_retry(
                page_url, normalized_title, content_title, json_content, page_num
            )

    def _fetch_chapter_with_retry(
        self,
        page_url: str,
        normalized_title: str,
        content_title: str,
        json_content: dict[str, str],
        retry_num: int,
    ) -> None:
        """带重试机制的章节获取

        Args:
            page_url: 章节URL
            normalized_title: 规范化的章节标题
            content_title: 小说标题
            json_content: 已爬取的内容字典
            retry_num: 当前重试次数
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                # 获取章节内容
                chapter_title, novel_text = self.get_chapter_content(page_url)

                # 按格式保存
                current_page = f"{normalized_title}\n\n{novel_text}\n\n"
                json_content[normalized_title] = current_page

                self.logger.info(
                    f"爬取小说： [{normalized_title}] from url {page_url} 内容长度： {len(novel_text)}"
                )

                # 保存到JSON
                save_chapter_to_json(content_title, json_content)

                # 使用统一的随机延迟函数
                random_delay(0.1, 0.5)
                return

            except Exception as e:
                self.logger.error(f"爬取失败 (第 {attempt}/{self.max_retries} 次尝试): {e}")

                # 如果不是最后一次重试，增加延迟后继续尝试
                if attempt < self.max_retries:
                    delay = attempt
                    self.logger.info(f"{delay} 秒后重试...")
                    random_delay(delay, delay + 1)
                else:
                    self.logger.error(f"达到最大重试次数 {self.max_retries}，放弃该章节")

    def _send_request(self, url: str, timeout: int = 10) -> requests.Response:
        """发送HTTP请求的封装方法

        Args:
            url: 请求URL
            timeout: 超时时间（秒）

        Returns:
            HTTP响应对象

        Raises:
            Exception: 请求失败时抛出异常
        """
        # 检查缓存
        if self.enable_cache and url in self.cache:
            self.logger.debug(f"从缓存获取: {url}")
            # 创建一个模拟的响应对象
            mock_response = SimpleNamespace()
            mock_response.text = self.cache[url]
            mock_response.status_code = 200
            mock_response.encoding = 'utf-8'
            mock_response.apparent_encoding = 'utf-8'
            return cast(requests.Response, mock_response)

        # 发送实际请求
        response = requests.get(url, headers=self.headers, timeout=timeout)
        response.encoding = response.apparent_encoding

        if response.status_code != 200:
            self.logger.error(f"请求失败，状态码: {response.status_code}")
            raise Exception(f"请求失败，状态码: {response.status_code}")

        # 存入缓存
        if self.enable_cache:
            if len(self.cache) >= self.cache_size:
                # 移除最早的缓存项
                oldest_url = next(iter(self.cache))
                self.cache.pop(oldest_url)
            self.cache[url] = response.text
            self.logger.debug(f"缓存保存: {url}")

        return response

    def _save_debug_html_on_error(self) -> None:
        """在错误发生时保存调试HTML"""
        if not self.debug_enabled:
            return

        try:
            response = self._send_request(self.homepage_url)
            save_debug_html(
                response.text,
                f"debug_{self.__class__.__name__}",
                self.homepage_url,
                self.debug_dir,
                self.debug_enabled,
            )
        except Exception as e:
            self.logger.error(f"保存调试文件失败: {e}")

    @classmethod
    def parse_args(
        cls, defaults: dict[str, Any] | None = None
    ) -> argparse.Namespace:
        """解析命令行参数

        Args:
            defaults: 默认参数值字典

        Returns:
            解析后的参数命名空间
        """
        default_values: dict[str, Any] = {
            'homepage_url': '',
            'base_url': '',
            'max_chapters': 100000,
            'max_retries': 3,
            'debug_dir': 'debug_html',
            'debug_enabled': False,
            'clear_files': False,
            'enable_cache': True,
            'cache_size': 100
        }

        if defaults:
            default_values.update(defaults)

        parser = argparse.ArgumentParser(description=f'{cls.__name__} 小说爬虫')
        parser.add_argument(
            '--homepage_url',
            type=str,
            default=default_values['homepage_url'],
            help='小说主页URL'
        )
        parser.add_argument(
            '--base_url',
            type=str,
            default=default_values['base_url'],
            help='网站基础URL'
        )
        parser.add_argument(
            '--max_chapters',
            type=int,
            default=default_values['max_chapters'],
            help='最大爬取章节数'
        )
        parser.add_argument(
            '--max_retries',
            type=int,
            default=default_values['max_retries'],
            help='每个章节的最大重试次数'
        )
        parser.add_argument(
            '--debug_dir',
            type=str,
            default=default_values['debug_dir'],
            help='调试HTML保存目录'
        )
        parser.add_argument(
            '--debug_enabled',
            type=lambda x: x.lower() == 'true',
            default=default_values['debug_enabled'],
            help='是否启用调试模式 (true/false)'
        )
        parser.add_argument(
            '--clear_files',
            type=lambda x: x.lower() == 'true',
            default=default_values['clear_files'],
            help='是否在爬取前清空已存在的文件 (true/false)'
        )
        parser.add_argument(
            '--enable_cache',
            type=lambda x: x.lower() == 'true',
            default=default_values['enable_cache'],
            help='是否启用缓存机制 (true/false)'
        )
        parser.add_argument(
            '--cache_size',
            type=int,
            default=default_values['cache_size'],
            help='缓存大小'
        )

        return parser.parse_args()

    @classmethod
    def main(cls) -> None:
        """主函数入口"""
        args = cls.parse_args()
        crawler = cls(
            args.homepage_url,
            args.base_url,
            args.max_chapters,
            args.max_retries,
            args.debug_dir,
            args.debug_enabled,
            args.clear_files,
            args.enable_cache,
            args.cache_size,
        )
        crawler.crawl()
