# 开发新爬虫 Skill

帮助用户创建新的小说网站爬虫。

## 使用方式

当用户请求添加新网站爬虫时，引导用户完成以下步骤：

1. **收集信息**
   - 目标网站 URL
   - 网站名称
   - 章节列表页的 HTML 结构
   - 章节详情页的 HTML 结构

2. **分析网站结构**
   - 使用浏览器开发者工具检查章节链接的 CSS 选择器
   - 检查章节内容的容器选择器
   - 确认网站是否有反爬机制

3. **创建爬虫文件**
   - 在 `src/` 目录下创建新文件
   - 继承 `BaseCrawler`
   - 实现 `get_page_urls()` 和 `get_chapter_content()` 方法

4. **注册爬虫**
   - 在 `run_crawler.py` 中添加爬虫映射

5. **测试**
   - 先用少量章节测试
   - 验证 JSON 和 TXT 输出正确

## 示例代码模板

```python
# src/my_crawler.py
from typing import List, Tuple
from bs4 import BeautifulSoup
from .base_crawler import BaseCrawler

class MySiteCrawler(BaseCrawler):
    """网站描述"""

    def __init__(self, homepage_url: str, base_url: str, **kwargs):
        super().__init__(homepage_url, base_url, **kwargs)

    def get_page_urls(self, url: str) -> Tuple[str, List[Tuple[str, str]]]:
        """获取章节列表"""
        response = self._send_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 根据网站结构提取标题和章节链接
        title = soup.find('h1').text.strip()
        chapters = []

        for link in soup.select('.chapter-link'):  # 修改选择器
            chapter_title = link.text.strip()
            chapter_url = self.base_url + link['href']
            chapters.append((chapter_title, chapter_url))

        return title, chapters

    def get_chapter_content(self, url: str) -> Tuple[str, str]:
        """获取章节内容"""
        response = self._send_request(url)
        soup = BeautifulSoup(response.text, 'html.parser')

        # 根据网站结构提取标题和内容
        title = soup.find('h1').text.strip()
        content = soup.find('div', class_='content').get_text()

        return title, content

    @classmethod
    def parse_args(cls):
        """定义命令行参数"""
        import argparse
        parser = argparse.ArgumentParser(description='我的小说爬虫')
        parser.add_argument('--homepage_url', type=str,
                            default='http://example.com/novel/1',
                            help='小说主页URL')
        parser.add_argument('--base_url', type=str,
                            default='http://example.com',
                            help='网站基础URL')
        # ... 其他参数继承自基类
        return parser.parse_args()

if __name__ == "__main__":
    MySiteCrawler.main()
```

## 常见问题

- **网站需要登录**：需要添加 cookie 处理
- **内容是动态加载**：需要使用 selenium 或分析 API
- **有访问频率限制**：增加 `random_delay` 的延迟时间
