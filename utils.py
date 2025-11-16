import json
import os
import re
import time
import random
import logging
import inspect

def setup_logger(log_file=None):
    """配置日志记录器，使用Python内置logging模块
    
    Args:
        log_file: 日志文件名，如果提供，则将日志保存到该文件中
    
    Returns:
        配置好的logger实例
    """
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    
    # 如果logger已有处理器，先清除
    if logger.handlers:
        logger.handlers.clear()
    
    # 设置日志级别
    logger.setLevel(logging.INFO)
    
    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    
    # 设置日志格式，使用内置变量获取记录日志时的实际文件名和行号
    formatter = logging.Formatter('%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s', 
                               datefmt='%Y-%m-%d %H:%M:%S')
    console_handler.setFormatter(formatter)
    
    # 添加控制台处理器到logger
    logger.addHandler(console_handler)
    
    # 如果提供了日志文件名，则添加文件处理器
    if log_file:
        # 确保日志文件目录存在
        log_dir = os.path.dirname(log_file)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir)
        
        # 创建文件处理器
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(formatter)
        
        # 添加文件处理器到logger
        logger.addHandler(file_handler)
        logger.info(f"日志文件已配置: {log_file}")
    
    return logger

def save_chapter_to_json(content_title, json_content):
    """保存章节内容到JSON文件"""
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    with open(f"{content_title}.json", "w", encoding="utf-8") as f:
        json.dump(json_content, f, ensure_ascii=False, indent=4)
    logger.info(f"已保存JSON数据到 {content_title}.json")

def load_existing_json(content_title):
    """加载已存在的JSON数据，处理空文件情况"""
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    json_content = {}
    if os.path.exists(f"./{content_title}.json"):
        try:
            with open(f"./{content_title}.json", "r", encoding="utf-8") as json_file:
                file_content = json_file.read().strip()
                if file_content:
                    json_content = json.loads(file_content)
                else:
                    logger.info(f"JSON文件存在但为空，创建新的数据结构")
            logger.info(f"已加载现有数据，共{len(json_content)}章")
        except json.JSONDecodeError:
            logger.error(f"JSON文件格式错误，将创建新的数据结构")
    return json_content

def save_novel_to_txt(content_title, json_content):
    """将小说内容保存到TXT文件"""
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    output_file = f"{content_title}.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        for title, content in json_content.items():
            logger.info(f"向文件写入 {title}")
            f.write(content)
    logger.info(f"小说已保存到: {output_file}，共{len(json_content)}章")
    return output_file

def normalize_chapter_title(title, page_num):
    """规范化章节标题格式，过滤无效文本"""
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    
    # 过滤掉"立即阅读"等无效文本
    title = title.replace("立即阅读", "").strip()
    
    try:
        if not title.startswith("第"):
            # 尝试从标题中提取数字
            num_match = re.search(r'\d+', title)
            if num_match:
                page_num = int(num_match.group())
                # 移除标题中的数字部分
                title = re.sub(r'^\d+[\s:、]*', '', title).strip()
            
            # 如果标题为空，使用默认格式
            if not title:
                title = f"第 {page_num} 章"
            else:
                title = f"第 {page_num} 章: {title}"
    except Exception as e:
        logger.info(f"标题格式调整失败: {e}")
        # 即使失败也确保不包含"立即阅读"
        title = f"第 {page_num} 章" + (f": {title}" if title else "")
    
    return title, page_num + 1

def random_delay(min_delay=0.1, max_delay=0.2):
    """随机延迟，避免请求过快"""
    time.sleep(random.random() * (max_delay - min_delay) + min_delay)

def ensure_directory(directory):
    """确保目录存在"""
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    if not os.path.exists(directory):
        os.makedirs(directory)
        logger.info(f"创建目录: {directory}")

def save_debug_html(response_text, title, url, debug_dir="debug_html", debug_enabled=True):
    """保存调试HTML文件到指定目录
    
    Args:
        response_text: HTTP响应文本
        title: 章节标题
        url: 章节URL
        debug_dir: 调试文件保存目录
        debug_enabled: 是否启用调试模式
        
    Returns:
        保存的文件路径，如果未保存则返回None
    """
    # 获取logger实例
    logger = logging.getLogger('novel_crawler')
    
    # 如果调试模式未启用，直接返回
    if not debug_enabled:
        return None
    
    try:
        # 确保调试目录存在
        ensure_directory(debug_dir)
        
        # 清理章节标题，移除非法字符
        safe_title = ''.join(char for char in title if char not in '/:*?"<>|')
        
        # 如果标题为空或过于简单，使用URL的一部分作为备选
        if not safe_title or len(safe_title) < 2:
            url_parts = url.split('/')
            for part in reversed(url_parts):
                if part and not part.endswith('.html') and len(part) > 1:
                    safe_title = part
                    break
            if not safe_title:
                safe_title = f"chapter_{hash(url) % 1000}"
        
        # 构造保存路径
        debug_path = os.path.join(debug_dir, f"{safe_title}.html")
        
        # 保存文件
        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(response_text)
        
        logger.info(f"调试页面已保存到 {debug_path}")
        return debug_path
    except Exception as e:
        logger.error(f"保存调试文件失败: {e}")
        return None