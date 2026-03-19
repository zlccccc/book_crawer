from __future__ import annotations

import argparse
from typing import cast

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
    def parse_args(
        cls, defaults: dict[str, object] | None = None
    ) -> argparse.Namespace:
        """解析命令行参数，设置黄鹤楼文学的默认数据源参数"""
        crawler_defaults = {
            'homepage_url': 'https://www.hhlwx.org/hhlchapter/69730.html',
            'base_url': 'https://www.hhlwx.org'
        }
        return super().parse_args(crawler_defaults)

    def get_page_urls(self, url: str) -> tuple[str, list[tuple[str, str]]]:
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

        return cast(str, h1_tag.get_text(strip=True))

    def _extract_chapter_links(self, soup: BeautifulSoup) -> list[tuple[str, str]]:
        """从HTML中提取章节链接

        Args:
            soup: BeautifulSoup对象

        Returns:
            [(章节标题, 章节URL), ...]
        """
        chapter_links = soup.find_all("td", class_=self.CHAPTER_LINK_CLASS)
        page_urls: list[tuple[str, str]] = []

        for link in chapter_links:
            a_tag = link.find("a")
            if not a_tag or not a_tag.attrs.get("href"):
                continue

            href = cast(str, a_tag.get("href"))
            title = a_tag.get_text(strip=True)
            full_url = self.base_url + href
            page_urls.append((title, full_url))

        return page_urls

    def get_chapter_content(self, url: str) -> tuple[str, str]:
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

        return cast(str, title_content.get("content"))

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


if __name__ == "__main__":
    HuangHeLouCrawler.main()
