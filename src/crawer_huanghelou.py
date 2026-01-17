from typing import List, Tuple

import requests
from bs4 import BeautifulSoup

from .base_crawler import BaseCrawler
from .utils import save_debug_html


class HuangHeLouCrawler(BaseCrawler):
    """黄鹤楼文学小说爬虫，继承自BaseCrawler"""

    # 黄鹤楼文学的特定选择器
    TITLE_CONTAINER_CLASS = "ksq_1"
    CHAPTER_LINK_CLASS = "chapterlist"
    CONTENT_DIV_STYLE = "font-size: 20px; text-indent: 30px; line-height: 38px; width: 720px; margin: 0 auto;"

    def __init__(
        self,
        homepage_url: str,
        base_url: str,
        max_chapters: int = 100000,
        max_retries: int = 3,
        debug_dir: str = "debug_html",
        debug_enabled: bool = False,
        clear_files: bool = True,
    ) -> None:
        """初始化黄鹤楼文学爬虫"""
        super().__init__(
            homepage_url, base_url, max_chapters, max_retries,
            debug_dir, debug_enabled, clear_files
        )

    @classmethod
    def parse_args(cls):
        """解析命令行参数，设置黄鹤楼文学的默认数据源参数"""
        import argparse

        parser = argparse.ArgumentParser(description='黄鹤楼文学小说爬虫')
        parser.add_argument('--homepage_url', type=str,
                            default='https://www.hhlwx.org/hhlchapter/69730.html',
                            help='小说主页URL')
        parser.add_argument('--base_url', type=str,
                            default='https://www.hhlwx.org',
                            help='网站基础URL')
        parser.add_argument('--max_chapters', type=int,
                            default=100000,
                            help='最大爬取章节数')
        parser.add_argument('--max_retries', type=int,
                            default=3,
                            help='每个章节的最大重试次数')
        parser.add_argument('--debug_dir', type=str,
                            default='debug_html',
                            help='调试HTML保存目录')
        parser.add_argument('--debug_enabled', type=lambda x: x.lower() == 'true',
                            default=False,
                            help='是否启用调试模式 (true/false)')
        parser.add_argument('--clear_files', type=lambda x: x.lower() == 'true',
                            default=False,
                            help='是否在爬取前清空已存在的文件 (true/false)')

        return parser.parse_args()

    def get_page_urls(self, url: str) -> Tuple[str, List[Tuple[str, str]]]:
        """从首页获取所有章节URL

        Args:
            url: 小说首页URL

        Returns:
            (小说标题, [(章节标题, 章节URL), ...])

        Raises:
            Exception: 如果无法提取标题或章节链接
        """
        response = self._send_request(url)

        soup = BeautifulSoup(response.text, "html.parser")

        # 找到小说标题
        title_content = self._extract_novel_title(soup)

        # 获取所有章节链接
        page_urls = self._extract_chapter_links(soup)

        return title_content, page_urls

    def _extract_novel_title(self, soup: BeautifulSoup) -> str:
        """从HTML中提取小说标题

        Args:
            soup: BeautifulSoup对象

        Returns:
            小说标题

        Raises:
            Exception: 如果无法找到标题
        """
        title_container = soup.find("div", {"class": self.TITLE_CONTAINER_CLASS})
        if not title_container:
            raise Exception("标题容器未找到")

        h1_tag = title_container.find("h1")
        if not h1_tag:
            raise Exception("标题h1标签未找到")

        return h1_tag.text.strip()

    def _extract_chapter_links(self, soup: BeautifulSoup) -> List[Tuple[str, str]]:
        """从HTML中提取章节链接

        Args:
            soup: BeautifulSoup对象

        Returns:
            [(章节标题, 章节URL), ...]
        """
        chapter_links = soup.find_all("td", class_=self.CHAPTER_LINK_CLASS)
        page_urls: List[Tuple[str, str]] = []

        for link in chapter_links:
            a_tag = link.find("a")
            if not a_tag or not a_tag.attrs.get("href"):
                continue

            href = a_tag.attrs["href"]
            title = a_tag.text.strip()
            full_url = self.base_url + href
            page_urls.append((title, full_url))

        return page_urls

    def get_chapter_content(self, url: str) -> Tuple[str, str]:
        """解析网页并获取小说内容

        Args:
            url: 章节URL

        Returns:
            (章节标题, 章节内容)

        Raises:
            Exception: 如果无法提取标题或内容
        """
        self.logger.info(f"尝试获取章节内容: {url}")

        response = self._send_request(url)
        soup = BeautifulSoup(response.text, "html.parser")

        # 找到章节标题
        title = self._extract_chapter_title(soup)

        # 找到章节内容
        novel_text = self._extract_chapter_text(soup)

        # 保存调试HTML
        if self.debug_enabled:
            save_debug_html(response.text, title, url, self.debug_dir, self.debug_enabled)

        self.logger.info(f"成功获取章节内容: {title}")
        return title, novel_text

    def _extract_chapter_title(self, soup: BeautifulSoup) -> str:
        """从HTML中提取章节标题

        Args:
            soup: BeautifulSoup对象

        Returns:
            章节标题

        Raises:
            Exception: 如果无法找到标题
        """
        title_content = soup.find("meta", {"property": "og:title"})
        if not title_content or not title_content.attrs.get("content"):
            raise Exception("标题未找到 in HTML content")

        return title_content.attrs["content"]

    def _extract_chapter_text(self, soup: BeautifulSoup) -> str:
        """从HTML中提取章节正文

        Args:
            soup: BeautifulSoup对象

        Returns:
            章节正文内容

        Raises:
            Exception: 如果无法找到内容区域
        """
        novel_content = soup.find("div", {"style": self.CONTENT_DIV_STYLE})
        if not novel_content:
            raise Exception("小说内容未找到 in HTML content")

        return novel_content.get_text()

    def _send_request(self, url: str, timeout: int = 4) -> requests.Response:
        """发送HTTP请求的封装方法

        Args:
            url: 请求URL
            timeout: 超时时间（秒）

        Returns:
            HTTP响应对象

        Raises:
            Exception: 请求失败时抛出异常
        """
        response = requests.get(url, headers=self.headers, timeout=timeout)

        if response.status_code != 200:
            self.logger.error(f"请求失败，状态码: {response.status_code}")
            raise Exception(f"Failed to fetch page {url}")

        return response


if __name__ == "__main__":
    HuangHeLouCrawler.main()