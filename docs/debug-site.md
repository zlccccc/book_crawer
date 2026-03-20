# 调试网站结构 Skill

帮助用户分析小说网站的 HTML 结构，以便编写爬虫。

## 使用方式

当用户需要调试或分析新网站时：

1. **启用调试模式**
   ```bash
   python run_crawler.py 77shuwu --homepage_url "目标URL" --debug_enabled true
   ```

2. **查看调试文件**
   - HTML 文件保存在 `debug_html/` 目录
   - 使用浏览器打开查看页面结构
   - 使用开发者工具分析元素

3. **关键信息提取**
   - 章节列表：查找包含所有章节链接的容器
   - 章节链接：提取 `href` 属性和链接文本
   - 章节标题：通常在 `<h1>` 或 `<title>` 中
   - 章节内容：查找包含正文的 `div` 或 `article`

## 常用 CSS 选择器

```python
# 按选择器查找
soup.select('#content')           # ID
soup.select('.chapter-list')      # Class
soup.select('div.chapter a')      # 后代选择器
soup.select('a[href*="/chapter/"]') # 属性包含
```

## 工具函数

使用 `save_debug_html()` 保存调试信息：

```python
from src.utils import save_debug_html

# 在爬虫中
response = self._send_request(url)
save_debug_html(response.text, "调试文件名", url, self.debug_dir, True)
```
