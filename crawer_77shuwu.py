import re
from base_crawler import BaseCrawler
from utils import save_debug_html


class SevenSevenShuWuCrawler(BaseCrawler):
    """77读书网小说爬虫，继承自BaseCrawler"""
    
    def __init__(self, homepage_url, base_url, max_chapters=100000, debug_dir="debug_html", debug_enabled=False, clear_files=True):
        """初始化77读书网爬虫"""
        super().__init__(homepage_url, base_url, max_chapters, debug_dir, debug_enabled, clear_files)
    
    def get_page_urls(self, url):
        """获取章节链接列表，使用href前缀过滤"""
        self.logger.info(f"获取章节列表: {url}")
        try:
            response = self._send_request(url)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取小说标题
            title_tag = soup.find('h1')
            if not title_tag:
                title_tag = soup.find('title')
            
            novel_title = title_tag.text.strip() if title_tag else "未知小说"
            # 清理标题，移除特殊字符
            novel_title = ''.join(char for char in novel_title if char not in '/:*?"<>|')
            
            # 提取小说ID，用于更精确地匹配章节链接
            novel_id_match = re.search(r'/novel/(\d+)/', url)
            novel_id = novel_id_match.group(1) if novel_id_match else ''
            
            # 简化的href前缀过滤方法
            chapter_links = []
            self.logger.info("使用href前缀过滤获取章节链接...")
            
            # 从整个页面获取所有链接
            all_links = soup.find_all('a', href=True)
            for link in all_links:
                href = link['href']
                text = link.text.strip()
                
                # 确保文本不为空且长度合理
                if not text or len(text) > 50:
                    continue
                
                # 过滤掉"立即阅读"等无效标题，但保留可能的章节标题
                if "立即阅读" in text:
                    # 只过滤纯"立即阅读"文本，保留有其他内容的标题
                    if text.strip() == "立即阅读":
                        continue
                
                # 使用href前缀过滤，优先级排序
                is_chapter_link = False
                
                # 1. 优先级最高：包含小说ID的chapter链接
                if novel_id and f'/chapter/{novel_id}/' in href:
                    is_chapter_link = True
                # 2. 次优先级：所有chapter格式的链接
                elif href.startswith('/chapter/'):
                    is_chapter_link = True
                # 3. 其他可能的章节链接格式
                elif href.startswith('/novel/') and not href.endswith('/') and href.count('/') >= 3:
                    is_chapter_link = True
                
                if is_chapter_link:
                    full_url = self.base_url + href if href.startswith('/') else href
                    chapter_links.append((text, full_url))
            
            # 移除重复链接，基于URL去重
            seen_urls = set()
            unique_links = []
            for text, href in chapter_links:
                if href not in seen_urls:
                    seen_urls.add(href)
                    unique_links.append((text, href))
            
            # 尝试按URL排序，假设URL包含章节顺序信息
            unique_links.sort(key=lambda x: x[1])
            
            self.logger.info(f"成功获取章节列表，共{len(unique_links)}个章节")
            # 显示前5个章节作为示例
            if len(unique_links) > 0:
                self.logger.info(f"前5个章节示例: {unique_links[:5]}")
            
            return novel_title, unique_links
        except Exception as e:
            self.logger.error(f"获取章节列表失败: {e}")
            # 保存调试HTML文件
            if self.debug_enabled and 'response' in locals():
                save_debug_html(response.text, "debug_77shuku", url, self.debug_dir, self.debug_enabled)
            raise
    
    def get_chapter_content(self, url):
        """获取单个章节内容，使用HTML标签结构进行内容过滤"""
        self.logger.info(f"尝试获取章节内容: {url}")
        try:
            response = self._send_request(url, timeout=15)
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 查找章节标题
            chapter_title = "未知章节"
            
            # 方法1: 尝试查找h1标签
            h1_tag = soup.find('h1')
            if h1_tag:
                h1_text = h1_tag.text.strip()
                # 过滤掉明显不是标题的内容
                if h1_text and "立即阅读" not in h1_text and len(h1_text) < 100:
                    chapter_title = h1_text
            
            # 方法2: 如果h1不是有效标题，尝试查找标题相关的meta标签
            if chapter_title == "未知章节":
                meta_title = soup.find('meta', property='og:title')
                if meta_title and meta_title.get('content'):
                    meta_text = meta_title['content'].strip()
                    if meta_text and "立即阅读" not in meta_text:
                        chapter_title = meta_text
            
            # 方法3: 尝试title标签
            if chapter_title == "未知章节":
                title_tag = soup.find('title')
                if title_tag:
                    title_text = title_tag.text.strip()
                    # 清理标题，移除网站名称等附加信息
                    for suffix in ['_77读书网', '-77读书网', '77读书网', '全文阅读']:
                        if title_text.endswith(suffix):
                            title_text = title_text[:-len(suffix)]
                    # 过滤掉"立即阅读"
                    if title_text and "立即阅读" not in title_text and len(title_text) > 5:
                        chapter_title = title_text
            
            # 方法4: 从URL中提取信息作为备选
            if chapter_title == "未知章节" or "立即阅读" in chapter_title:
                # 尝试从路径中提取数字作为章节编号
                url_parts = url.split('/')
                for part in url_parts:
                    if part.isdigit():
                        chapter_title = f"第 {part} 章"
                        break
            
            # 最后的清理
            if "立即阅读" in chapter_title:
                chapter_title = chapter_title.replace("立即阅读", "").strip()
                if not chapter_title:
                    chapter_title = "未知章节"
            
            # 保存调试HTML文件
            save_debug_html(response.text, chapter_title, url, self.debug_dir, self.debug_enabled)
            
            # 方法1: 优先使用HTML标签结构提取 - 找到div#ChapterContents
            content_div = soup.find('div', id='ChapterContents')
            if content_div:
                self.logger.info("找到div#ChapterContents，开始提取内容")
                
                # 移除顶部的广告提示div#content_tip
                content_tip = content_div.find('div', id='content_tip')
                if content_tip:
                    content_tip.decompose()
                
                # 收集所有文本内容，按段落结构组织
                paragraphs = []
                current_text = []
                
                # 遍历所有子元素，保留<br>分隔的段落结构
                for element in content_div.contents:
                    if element.name == 'br':
                        # 遇到<br>标签，将当前累积的文本作为段落
                        if current_text:
                            paragraphs.append(''.join(current_text))
                            current_text = []
                    elif element.string:
                        # 文本节点
                        text = element.string.strip()
                        if text:
                            current_text.append(text)
                    elif element.name:
                        # 其他标签，提取其文本
                        tag_text = element.get_text().strip()
                        if tag_text:
                            current_text.append(tag_text)
                
                # 处理最后一个段落
                if current_text:
                    paragraphs.append(''.join(current_text))
                
                # 过滤掉导航和下载链接段落
                filtered_paragraphs = []
                for para in paragraphs:
                    # 过滤掉包含导航和下载信息的段落
                    if not ('txt下载地址' in para or '手机阅读' in para or '上一章' in para or '下一章' in para or '回目录' in para):
                        # 保留段落内容
                        filtered_paragraphs.append(para)
                
                if filtered_paragraphs:
                    content = '\n\n'.join(filtered_paragraphs)
                    self.logger.info(f"成功从div#ChapterContents提取内容，长度: {len(content)}字符")
                    return chapter_title, content
            
            # 方法2: 尝试使用CSS选择器匹配内容区域
            selectors = [
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
            
            content_div = None
            for selector in selectors:
                content_div = soup.select_one(selector)
                if content_div:
                    self.logger.info(f"找到内容容器: {selector}")
                    break
            
            # 如果找到内容容器，提取文本
            if content_div:
                # 移除可能的广告标签
                for element in content_div(['script', 'style', 'iframe', 'noscript']):
                    element.decompose()
                
                # 获取文本
                content = content_div.get_text(separator='\n', strip=False)
                
                # 处理换行
                content = '\n'.join([line.strip() for line in content.split('\n') if line.strip()])
                content = re.sub(r'\n{3,}', '\n\n', content)
                
                # 清理广告文本和导航内容
                content = re.sub(r'温馨提示：方向键左右.*?返回列表', '', content, flags=re.DOTALL)
                
                # 使用HTML结构过滤导航内容
                if 'txt下载地址' in content or '手机阅读' in content:
                    # 找到导航内容的位置并截断
                    nav_start = content.find('txt下载地址')
                    if nav_start != -1:
                        content = content[:nav_start].strip()
                
                content = content.strip()
                
                if len(content) >= 100:
                    self.logger.info(f"成功获取章节: {chapter_title}，内容长度: {len(content)}字符")
                    return chapter_title, content
            
            # 方法3: 尝试从整个页面提取，基于HTML标签结构
            self.logger.info("尝试从整个页面提取文本...")
            
            # 移除脚本和样式标签
            for script in soup(['script', 'style']):
                script.decompose()
            
            # 获取所有文本内容
            all_text = soup.get_text(separator='\n', strip=False)
            lines = all_text.split('\n')
            
            # 尝试找到正文开始的位置 - 基于缩进或内容特征
            start_idx = 0
            for i, line in enumerate(lines):
                # 查找以空格缩进开始的行，通常是小说正文
                if line.startswith('    ') or line.startswith('&nbsp;&nbsp;&nbsp;&nbsp;'):
                    start_idx = i
                    break
            
            # 提取可能的正文内容
            potential_content = lines[start_idx:]
            filtered_content = []
            
            for line in potential_content:
                line = line.strip()
                # 过滤掉导航和下载链接
                if line and not ('txt下载地址' in line or '手机阅读' in line or '上一章' in line or '下一章' in line or '回目录' in line):
                    filtered_content.append(line)
            
            # 进一步过滤导航菜单内容
            content = '\n\n'.join(filtered_content)
            
            # 使用正则表达式清理剩余的导航内容
            content = re.sub(r'温馨提示：方向键左右.*?返回列表', '', content, flags=re.DOTALL)
            content = content.strip()
            
            self.logger.info(f"成功从整个页面提取内容，长度: {len(content)}字符")
            return chapter_title, content
            
        except Exception as e:
            self.logger.error(f"获取章节内容失败: {e}")
            return "未知章节", f"[章节内容获取失败 - {str(e)}]"
    
    def _send_request(self, url, timeout=10):
        """发送HTTP请求的封装方法"""
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
                            default='http://www.77shuku.org/novel/135558/',
                            help='小说主页URL')
        parser.add_argument('--base_url', type=str, 
                            default='https://www.77shuwu.org',
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


# 需要添加缺失的导入
from bs4 import BeautifulSoup
import requests


if __name__ == "__main__":
    SevenSevenShuWuCrawler.main()