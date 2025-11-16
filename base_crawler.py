import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
import os
import argparse
from utils import (
    setup_logger,
    save_chapter_to_json,
    load_existing_json,
    save_novel_to_txt,
    normalize_chapter_title,
    random_delay,
    save_debug_html
)


class BaseCrawler:
    """爬虫基类，提供通用爬虫功能"""
    
    def __init__(self, homepage_url, base_url, max_chapters=100000, debug_dir="debug_html", debug_enabled=False, clear_files=True):
        """初始化爬虫
        
        Args:
            homepage_url: 小说主页URL
            base_url: 网站基础URL
            max_chapters: 最大爬取章节数
            debug_dir: 调试文件保存目录
            debug_enabled: 是否启用调试模式
            clear_files: 是否在爬取前清空已存在的文件
        """
        self.homepage_url = homepage_url
        self.base_url = base_url
        self.max_chapters = max_chapters
        self.debug_dir = debug_dir
        self.debug_enabled = debug_enabled
        self.clear_files = clear_files
        self.logger = setup_logger()
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_page_urls(self, url):
        """获取章节链接列表
        
        需要在子类中实现
        """
        raise NotImplementedError("子类必须实现get_page_urls方法")
    
    def get_chapter_content(self, url):
        """获取章节内容
        
        需要在子类中实现
        """
        raise NotImplementedError("子类必须实现get_chapter_content方法")
    
    def clear_existing_files(self, title):
        """清空已存在的json和txt文件"""
        json_path = f"{title}.json"
        txt_path = f"{title}.txt"
        
        # 清空json文件
        if os.path.exists(json_path):
            with open(json_path, 'w', encoding='utf-8') as f:
                f.write('{}')
            self.logger.info(f"已清空 {json_path}")
        
        # 清空txt文件
        if os.path.exists(txt_path):
            with open(txt_path, 'w', encoding='utf-8') as f:
                pass
            self.logger.info(f"已清空 {txt_path}")
    
    def crawl(self):
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
            
            # 统计已爬取的章节数
            crawled_count = len(json_content)
            
            # 计算需要爬取的章节数
            remaining_chapters = self.max_chapters - crawled_count
            if remaining_chapters <= 0:
                self.logger.info(f"已爬取章节数达到最大限制 {self.max_chapters}，无需继续爬取")
                return
            
            # 过滤出未爬取的章节
            uncrawled_chapters = {}
            for title, url in page_urls:
                normalized_title, _ = normalize_chapter_title(title, 1)
                if normalized_title not in json_content:
                    uncrawled_chapters[title] = url
            
            # 限制爬取章节数
            chapters_to_crawl = list(uncrawled_chapters.items())[:remaining_chapters]
            self.logger.info(f"需要爬取 {len(chapters_to_crawl)} 个章节")
            
            page_num = 1
            
            # 遍历章节
            for title, page_url in tqdm(chapters_to_crawl, desc="爬取章节"):
                # 规范化章节标题
                normalized_title, page_num = normalize_chapter_title(title, page_num)
                
                # 跳过已爬取的章节（双重检查）
                if normalized_title in json_content:
                    continue
                    
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
                    random_delay(0.1, 0.5)  # 随机延迟0.1-0.5秒
                    
                except Exception as e:
                    self.logger.error(f"爬取失败: {e}")
                    # 不中断，继续尝试下一个章节
                    continue
            
            self.logger.info("爬取完成!")
            
            # 保存为TXT文件
            save_novel_to_txt(content_title, json_content)
            
        except Exception as err:
            self.logger.error(f"爬取失败: {err}")
            # 保存调试HTML文件
            if self.debug_enabled:
                try:
                    response = requests.get(self.homepage_url, headers=self.headers)
                    save_debug_html(response.text, f"debug_{self.__class__.__name__}", 
                                   self.homepage_url, self.debug_dir, self.debug_enabled)
                except Exception as e:
                    self.logger.error(f"保存调试文件失败: {e}")
    
    @classmethod
    def parse_args(cls):
        """解析命令行参数"""
        parser = argparse.ArgumentParser(description=f'{cls.__name__} 小说爬虫')
        parser.add_argument('--homepage_url', type=str, 
                            default='',
                            help='小说主页URL')
        parser.add_argument('--base_url', type=str, 
                            default='',
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
    
    @classmethod
    def main(cls):
        """主函数入口"""
        args = cls.parse_args()
        crawler = cls(args.homepage_url, args.base_url, args.max_chapters, args.debug_dir, args.debug_enabled, args.clear_files)
        crawler.crawl()