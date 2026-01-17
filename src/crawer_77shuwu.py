import re
from typing import List, Tuple, Optional

from bs4 import BeautifulSoup
import requests

from .base_crawler import BaseCrawler
from .utils import save_debug_html


class SevenSevenShuWuCrawler(BaseCrawler):
    """77读书网小说爬虫，继承自BaseCrawler"""

    # CSS选择器常量
    CONTENT_SELECTORS = [
        '#content',
        '.content',
        '#article',
        '.article',
        '#content_detail',
        '.content_detail',
        '.chapter_content',
        '#chapter_content',
        '.content_txt',
        '#content_txt',
        '.neirong',
        '#neirong',
    ]

    # 需要过滤的导航关键词
    NAVIGATION_KEYWORDS = [
        'txt下载地址',
        '手机阅读',
        '上一章',
        '下一章',
        '回目录',
    ]

    # 标题后缀清理
    TITLE_SUFFIXES = [
        '_77读书网',
        '-77读书网',
        '77读书网',
        '全文阅读',
    ]

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
        """初始化77读书网爬虫"""
        super().__init__(
            homepage_url, base_url, max_chapters, max_retries,
            debug_dir, debug_enabled, clear_files
        )
    
    def get_page_urls(self, url: str) -> Tuple[str, List[Tuple[str, str]]]:
        """获取章节链接列表，使用href前缀过滤

        Args:
            url: 页面URL

        Returns:
            (小说标题, [(章节标题, 章节URL), ...])
        """
        self.logger.info(f"获取章节列表: {url}")
        try:
            response = self._send_request(url)

            soup = BeautifulSoup(response.text, 'html.parser')

            # 获取小说标题
            novel_title = self._extract_novel_title(soup)

            # 提取小说ID，用于更精确地匹配章节链接
            novel_id = self._extract_novel_id(url)

            # 获取章节链接
            chapter_links = self._extract_chapter_links(soup, novel_id)

            # 移除重复链接并排序
            unique_links = self._deduplicate_and_sort_links(chapter_links)

            self.logger.info(f"成功获取章节列表，共{len(unique_links)}个章节")
            if unique_links:
                self.logger.info(f"前5个章节示例: {unique_links[:5]}")

            return novel_title, unique_links

        except Exception as e:
            self.logger.error(f"获取章节列表失败: {e}")
            # 保存调试HTML文件
            if self.debug_enabled and 'response' in locals():
                save_debug_html(response.text, "debug_77shuku", url, self.debug_dir, self.debug_enabled)
            raise

    def _extract_novel_title(self, soup: BeautifulSoup) -> str:
        """从HTML中提取小说标题

        Args:
            soup: BeautifulSoup对象

        Returns:
            清理后的小说标题
        """
        title_tag = soup.find('h1') or soup.find('title')
        if not title_tag:
            return "未知小说"

        novel_title = title_tag.text.strip()
        # 清理标题，移除特殊字符
        novel_title = ''.join(char for char in novel_title if char not in '/:*?"<>|')
        return novel_title

    def _extract_novel_id(self, url: str) -> str:
        """从URL中提取小说ID

        Args:
            url: 小说页面URL

        Returns:
            小说ID，如果未找到则返回空字符串
        """
        novel_id_match = re.search(r'/novel/(\d+)/', url)
        return novel_id_match.group(1) if novel_id_match else ''

    def _extract_chapter_links(
        self,
        soup: BeautifulSoup,
        novel_id: str,
    ) -> List[Tuple[str, str]]:
        """从HTML中提取章节链接

        Args:
            soup: BeautifulSoup对象
            novel_id: 小说ID

        Returns:
            [(章节标题, 章节URL), ...]
        """
        chapter_links: List[Tuple[str, str]] = []
        self.logger.info("使用href前缀过滤获取章节链接...")

        all_links = soup.find_all('a', href=True)
        for link in all_links:
            href = link['href']
            text = link.text.strip()

            # 确保文本不为空且长度合理
            if not text or len(text) > 50:
                continue

            # 过滤掉"立即阅读"等无效标题
            if text == "立即阅读":
                continue

            # 判断是否为章节链接
            if self._is_chapter_link(href, novel_id):
                full_url = self.base_url + href if href.startswith('/') else href
                chapter_links.append((text, full_url))

        return chapter_links

    def _is_chapter_link(self, href: str, novel_id: str) -> bool:
        """判断是否为章节链接

        Args:
            href: 链接href属性
            novel_id: 小说ID

        Returns:
            是否为章节链接
        """
        # 1. 优先级最高：包含小说ID的chapter链接
        if novel_id and f'/chapter/{novel_id}/' in href:
            return True
        # 2. 次优先级：所有chapter格式的链接
        if href.startswith('/chapter/'):
            return True
        # 3. 其他可能的章节链接格式
        if href.startswith('/novel/') and not href.endswith('/') and href.count('/') >= 3:
            return True

        return False

    def _deduplicate_and_sort_links(
        self,
        chapter_links: List[Tuple[str, str]],
    ) -> List[Tuple[str, str]]:
        """去重并排序章节链接

        Args:
            chapter_links: 原始章节链接列表

        Returns:
            去重排序后的章节链接列表
        """
        # 基于URL去重
        seen_urls = set()
        unique_links = []
        for text, href in chapter_links:
            if href not in seen_urls:
                seen_urls.add(href)
                unique_links.append((text, href))

        # 按URL排序
        unique_links.sort(key=lambda x: x[1])
        return unique_links

    def get_chapter_content(self, url: str) -> Tuple[str, str]:
        """获取单个章节内容，使用HTML标签结构进行内容过滤

        Args:
            url: 章节URL

        Returns:
            (章节标题, 章节内容)
        """
        self.logger.info(f"尝试获取章节内容: {url}")
        try:
            response = self._send_request(url, timeout=15)

            soup = BeautifulSoup(response.text, 'html.parser')

            # 提取章节标题
            chapter_title = self._extract_chapter_title(soup, url)

            # 保存调试HTML文件
            save_debug_html(response.text, chapter_title, url, self.debug_dir, self.debug_enabled)

            # 尝试多种方法提取内容
            content = (
                self._extract_content_from_chapter_contents(soup) or
                self._extract_content_from_selectors(soup) or
                self._extract_content_from_full_page(soup)
            )

            self.logger.info(f"成功获取章节: {chapter_title}，内容长度: {len(content)}字符")
            return chapter_title, content

        except Exception as e:
            self.logger.error(f"获取章节内容失败: {e}")
            return "未知章节", f"[章节内容获取失败 - {str(e)}]"

    def _extract_chapter_title(self, soup: BeautifulSoup, url: str) -> str:
        """从HTML中提取章节标题

        Args:
            soup: BeautifulSoup对象
            url: 章节URL

        Returns:
            章节标题
        """
        # 方法1: 查找h1标签
        h1_tag = soup.find('h1')
        if h1_tag:
            h1_text = h1_tag.text.strip()
            if h1_text and "立即阅读" not in h1_text and len(h1_text) < 100:
                return h1_text

        # 方法2: 查找meta标签
        meta_title = soup.find('meta', property='og:title')
        if meta_title and meta_title.get('content'):
            meta_text = meta_title['content'].strip()
            if meta_text and "立即阅读" not in meta_text:
                return meta_text

        # 方法3: 查找title标签
        title_tag = soup.find('title')
        if title_tag:
            title_text = title_tag.text.strip()
            # 清理标题，移除网站名称等附加信息
            for suffix in self.TITLE_SUFFIXES:
                if title_text.endswith(suffix):
                    title_text = title_text[:-len(suffix)]
            if title_text and "立即阅读" not in title_text and len(title_text) > 5:
                return title_text

        # 方法4: 从URL中提取
        url_parts = url.split('/')
        for part in url_parts:
            if part.isdigit():
                return f"第 {part} 章"

        return "未知章节"

    def _extract_content_from_chapter_contents(self, soup: BeautifulSoup) -> Optional[str]:
        """从div#ChapterContents中提取内容

        Args:
            soup: BeautifulSoup对象

        Returns:
            提取的内容，如果未找到则返回None
        """
        content_div = soup.find('div', id='ChapterContents')
        if not content_div:
            return None

        self.logger.info("找到div#ChapterContents，开始提取内容")

        # 移除顶部的广告提示
        content_tip = content_div.find('div', id='content_tip')
        if content_tip:
            content_tip.decompose()

        # 收集段落
        paragraphs = self._extract_paragraphs_from_div(content_div)

        # 过滤导航内容
        filtered_paragraphs = [
            para for para in paragraphs
            if not any(keyword in para for keyword in self.NAVIGATION_KEYWORDS)
        ]

        if filtered_paragraphs:
            content = '\n\n'.join(filtered_paragraphs)
            self.logger.info(f"成功从div#ChapterContents提取内容，长度: {len(content)}字符")
            return content

        return None

    def _extract_paragraphs_from_div(self, content_div) -> List[str]:
        """从div中提取段落

        Args:
            content_div: BeautifulSoup元素

        Returns:
            段落列表
        """
        paragraphs = []
        current_text = []

        for element in content_div.contents:
            if element.name == 'br':
                if current_text:
                    paragraphs.append(''.join(current_text))
                    current_text = []
            elif element.string:
                text = element.string.strip()
                if text:
                    current_text.append(text)
            elif element.name:
                tag_text = element.get_text().strip()
                if tag_text:
                    current_text.append(tag_text)

        # 处理最后一个段落
        if current_text:
            paragraphs.append(''.join(current_text))

        return paragraphs

    def _extract_content_from_selectors(self, soup: BeautifulSoup) -> Optional[str]:
        """使用CSS选择器提取内容

        Args:
            soup: BeautifulSoup对象

        Returns:
            提取的内容，如果未找到则返回None
        """
        content_div = None
        for selector in self.CONTENT_SELECTORS:
            content_div = soup.select_one(selector)
            if content_div:
                self.logger.info(f"找到内容容器: {selector}")
                break

        if not content_div:
            return None

        # 移除广告标签
        for element in content_div(['script', 'style', 'iframe', 'noscript']):
            element.decompose()

        # 获取并清理文本
        content = content_div.get_text(separator='\n', strip=False)
        content = self._clean_content(content)

        if len(content) >= 100:
            self.logger.info(f"成功从CSS选择器提取内容，长度: {len(content)}字符")
            return content

        return None

    def _extract_content_from_full_page(self, soup: BeautifulSoup) -> str:
        """从整个页面提取内容

        Args:
            soup: BeautifulSoup对象

        Returns:
            提取的内容
        """
        self.logger.info("尝试从整个页面提取文本...")

        # 移除脚本和样式
        for script in soup(['script', 'style']):
            script.decompose()

        # 获取文本
        all_text = soup.get_text(separator='\n', strip=False)
        lines = all_text.split('\n')

        # 查找正文开始位置
        start_idx = 0
        for i, line in enumerate(lines):
            if line.startswith('    ') or line.startswith('&nbsp;&nbsp;&nbsp;&nbsp;'):
                start_idx = i
                break

        # 过滤导航内容
        filtered_content = [
            line.strip()
            for line in lines[start_idx:]
            if line.strip() and not any(keyword in line for keyword in self.NAVIGATION_KEYWORDS)
        ]

        content = '\n\n'.join(filtered_content)
        content = self._clean_content(content)

        self.logger.info(f"成功从整个页面提取内容，长度: {len(content)}字符")
        return content

    def _clean_content(self, content: str) -> str:
        """清理内容文本

        Args:
            content: 原始内容

        Returns:
            清理后的内容
        """
        # 处理换行
        content = '\n'.join([line.strip() for line in content.split('\n') if line.strip()])
        content = re.sub(r'\n{3,}', '\n\n', content)

        # 清理广告文本
        content = re.sub(r'温馨提示：方向键左右.*?返回列表', '', content, flags=re.DOTALL)

        # 截断导航内容
        nav_keywords = ['txt下载地址', '手机阅读']
        for keyword in nav_keywords:
            nav_start = content.find(keyword)
            if nav_start != -1:
                content = content[:nav_start].strip()

        return content.strip()

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
        response = requests.get(url, headers=self.headers, timeout=timeout)
        response.encoding = response.apparent_encoding

        if response.status_code != 200:
            self.logger.error(f"请求失败，状态码: {response.status_code}")
            raise Exception(f"请求失败，状态码: {response.status_code}")

        return response

    @classmethod
    def parse_args(cls):
        """解析命令行参数，设置77书屋的默认数据源参数"""
        import argparse

        parser = argparse.ArgumentParser(description='77书屋小说爬虫')
        parser.add_argument('--homepage_url', type=str,
                            default='http://www.77shuku.org/novel/62042/',
                            help='小说主页URL')
        parser.add_argument('--base_url', type=str,
                            default='https://www.77shuwu.org',
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


if __name__ == "__main__":
    SevenSevenShuWuCrawler.main()