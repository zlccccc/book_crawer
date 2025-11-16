from base_crawler import BaseCrawler
from utils import save_debug_html
import requests
from bs4 import BeautifulSoup


class HuangHeLouCrawler(BaseCrawler):
    """黄鹤楼文学小说爬虫，继承自BaseCrawler"""
    
    def __init__(self, homepage_url, base_url, max_chapters=100000, debug_dir="debug_html", debug_enabled=False, clear_files=True):
        """初始化黄鹤楼文学爬虫"""
        super().__init__(homepage_url, base_url, max_chapters, debug_dir, debug_enabled, clear_files)
        
    @classmethod
    def parse_args(cls):
        """解析命令行参数，设置黄鹤楼文学的默认数据源参数"""
        import argparse
        parser = argparse.ArgumentParser(description='黄鹤楼文学小说爬虫')
        parser.add_argument('--homepage_url', type=str, 
                            default='https://www.hhlwx.org/hhlchapter/69533.html',
                            help='小说主页URL')
        parser.add_argument('--base_url', type=str, 
                            default='https://www.hhlwx.org',
                            help='网站基础URL')
        parser.add_argument('--max_chapters', type=int, 
                            default=100000,
                            help='最大爬取章节数')
        parser.add_argument('--debug_dir', type=str, 
                            default='debug_html',
                            help='调试HTML保存目录')
        parser.add_argument('--debug_enabled', type=lambda x: x.lower() == 'true', 
                            default=False,
                            help='是否启用调试模式 (true/false)')
        parser.add_argument('--clear_files', type=lambda x: x.lower() == 'true', 
                            default=True,
                            help='是否在爬取前清空已存在的文件 (true/false)')
        
        return parser.parse_args()
    
    def get_page_urls(self, url):
        """从首页获取所有章节URL"""
        response = self._send_request(url)
        
        soup = BeautifulSoup(response.text, "html.parser")
        # 找到小说标题
        title_content = (
            soup.find_all(
                "div",
                {"class": "ksq_1"},
            )[0]
            .find("h1")
            .text
        )
        
        # 获取所有章节链接
        chapter_links = soup.find_all("td", class_="chapterlist")
        page_urls = []
        
        for link in chapter_links:
            # 获取章节链接
            href = link.find("a").attrs["href"]
            title = link.find("a").text.strip()
            full_url = self.base_url + href
            page_urls.append((title, full_url))
        
        return title_content, page_urls
    
    def get_chapter_content(self, url):
        """解析网页并获取小说内容"""
        self.logger.info(f"尝试获取章节内容: {url}")
        
        # 发送请求
        response = self._send_request(url)
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # 找到小说标题
        title_content = soup.find(
            "meta",
            {"property": "og:title"},
        )
        
        if not title_content:
            raise Exception(f"标题未找到 in HTML content")
        title = title_content.attrs["content"]
        
        # 找到小说内容区域
        novel_content = soup.find(
            "div",
            {
                "style": "font-size: 20px; text-indent: 30px; line-height: 38px; width: 720px; margin: 0 auto;"
            },
        )
        
        if not novel_content:
            raise Exception(f"小说内容未找到 in HTML content")
        
        novel_text = novel_content.get_text()
        
        # 保存调试HTML
        if self.debug_enabled:
            save_debug_html(response.text, title, url, self.debug_dir, self.debug_enabled)
        
        self.logger.info(f"成功获取章节内容: {title}")
        return title, novel_text
    
    def _send_request(self, url, timeout=4):
        """发送HTTP请求的封装方法"""
        response = requests.get(url, headers=self.headers, timeout=timeout)
        
        if response.status_code != 200:
            self.logger.error(f"请求失败，状态码: {response.status_code}")
            raise Exception(f"Failed to fetch page {url}")
            
        return response


if __name__ == "__main__":
    HuangHeLouCrawler.main()