"""工具函数模块

提供日志配置、文件操作、数据处理等通用功能。
"""

import json
import logging
import os
import random
import re
import time
from typing import Dict, List, Optional, Tuple


# 日志器名称
LOGGER_NAME = 'novel_crawler'

# 文件名非法字符
INVALID_FILENAME_CHARS = '/:*?"<>|'


def setup_logger(log_file: Optional[str] = None) -> logging.Logger:
    """配置日志记录器，使用Python内置logging模块

    Args:
        log_file: 日志文件名，如果提供，则将日志保存到该文件中

    Returns:
        配置好的logger实例
    """
    logger = logging.getLogger(LOGGER_NAME)

    # 如果logger已有处理器，先清除
    if logger.handlers:
        logger.handlers.clear()

    # 设置日志级别
    logger.setLevel(logging.INFO)

    # 创建格式化器
    formatter = logging.Formatter(
        '%(asctime)s | %(filename)s:%(lineno)d | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 添加控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 如果需要，添加文件处理器
    if log_file:
        _add_file_handler(logger, log_file, formatter)

    return logger


def _add_file_handler(
    logger: logging.Logger,
    log_file: str,
    formatter: logging.Formatter,
) -> None:
    """添加文件处理器到logger

    Args:
        logger: Logger实例
        log_file: 日志文件路径
        formatter: 日志格式化器
    """
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.info(f"日志文件已配置: {log_file}")


def save_chapter_to_json(content_title: str, json_content: Dict[str, str]) -> None:
    """保存章节内容到JSON文件

    Args:
        content_title: 小说标题
        json_content: 章节内容字典
    """
    logger = logging.getLogger(LOGGER_NAME)
    filepath = f"{content_title}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_content, f, ensure_ascii=False, indent=4)

    logger.info(f"已保存JSON数据到 {filepath}")


def load_existing_json(content_title: str) -> Dict[str, str]:
    """加载已存在的JSON数据，处理空文件情况

    Args:
        content_title: 小说标题

    Returns:
        章节内容字典，如果文件不存在或格式错误则返回空字典
    """
    logger = logging.getLogger(LOGGER_NAME)
    filepath = f"./{content_title}.json"

    if not os.path.exists(filepath):
        return {}

    try:
        with open(filepath, "r", encoding="utf-8") as json_file:
            file_content = json_file.read().strip()
            if file_content:
                json_content = json.loads(file_content)
                logger.info(f"已加载现有数据，共{len(json_content)}章")
                return json_content
            else:
                logger.info("JSON文件存在但为空，创建新的数据结构")
                return {}
    except json.JSONDecodeError:
        logger.error("JSON文件格式错误，将创建新的数据结构")
        return {}


def save_novel_to_txt(
    content_title: str,
    normalized_titles: List[str],
    json_content: Dict[str, str],
) -> str:
    """将小说内容保存到TXT文件

    Args:
        content_title: 小说标题
        normalized_titles: 规范化的章节标题列表
        json_content: 章节内容字典

    Returns:
        输出文件路径
    """
    logger = logging.getLogger(LOGGER_NAME)
    output_file = f"{content_title}.txt"
    not_found_titles = set(json_content.keys())

    with open(output_file, "w", encoding="utf-8") as f:
        # 按顺序写入已匹配的章节
        for title in normalized_titles:
            if title in json_content:
                f.write(json_content[title])
                not_found_titles.remove(title)
                logger.info(f"向文件写入 {title}")
            else:
                logger.info(f"未找到: {title}")

        # 写入未匹配的章节
        if not_found_titles:
            _write_unmatched_titles(f, not_found_titles, logger, json_content)

    logger.info(f"小说已保存到: {output_file}，共{len(json_content)}章")
    return output_file


def _write_unmatched_titles(
    file_handle,
    not_found_titles: set,
    logger: logging.Logger,
    json_content: Dict[str, str],
) -> None:
    """写入未匹配的章节标题

    Args:
        file_handle: 文件句柄
        not_found_titles: 未找到的标题集合
        logger: Logger实例
        json_content: 章节内容字典
    """
    def extract_chapter_num(title: str) -> int:
        """从标题中提取章节号"""
        match = re.search(r'\d+', title)
        return int(match.group()) if match else 0

    sorted_titles = sorted(not_found_titles, key=extract_chapter_num)

    for title in sorted_titles:
        file_handle.write(json_content[title])
        logger.info(f"未匹配上: {title}, 已写入文件最后")


def normalize_chapter_title(title: str, page_num: int) -> Tuple[str, int]:
    """规范化章节标题格式，过滤无效文本

    Args:
        title: 原始章节标题
        page_num: 当前页码

    Returns:
        (规范化标题, 下一页码)
    """
    logger = logging.getLogger(LOGGER_NAME)

    # 过滤掉"立即阅读"等无效文本
    title = title.replace("立即阅读", "").strip()

    try:
        if not title.startswith("第"):
            page_num = _extract_and_format_title(title, page_num)
        else:
            page_num += 1
    except Exception as e:
        logger.info(f"标题格式调整失败: {e}")
        title = f"第 {page_num} 章" + (f": {title}" if title else "")
        page_num += 1

    return title, page_num


def _extract_and_format_title(title: str, page_num: int) -> int:
    """从标题中提取数字并格式化

    Args:
        title: 原始标题
        page_num: 当前页码

    Returns:
        下一页码
    """
    num_match = re.search(r'\d+', title)
    if num_match:
        page_num = int(num_match.group())
        title = re.sub(r'^\d+[\s:、]*', '', title).strip()

    if not title:
        title = f"第 {page_num} 章"
    else:
        title = f"第 {page_num} 章: {title}"

    return page_num + 1


def random_delay(min_delay: float = 0.1, max_delay: float = 0.2) -> None:
    """随机延迟，避免请求过快

    Args:
        min_delay: 最小延迟时间（秒）
        max_delay: 最大延迟时间（秒）
    """
    time.sleep(random.random() * (max_delay - min_delay) + min_delay)


def ensure_directory(directory: str) -> None:
    """确保目录存在

    Args:
        directory: 目录路径
    """
    logger = logging.getLogger(LOGGER_NAME)
    if not os.path.exists(directory):
        os.makedirs(directory, exist_ok=True)
        logger.info(f"创建目录: {directory}")


def save_debug_html(
    response_text: str,
    title: str,
    url: str,
    debug_dir: str = "debug_html",
    debug_enabled: bool = True,
) -> Optional[str]:
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
    logger = logging.getLogger(LOGGER_NAME)

    if not debug_enabled:
        return None

    try:
        ensure_directory(debug_dir)
        safe_title = _get_safe_filename(title, url)
        debug_path = os.path.join(debug_dir, f"{safe_title}.html")

        with open(debug_path, 'w', encoding='utf-8') as f:
            f.write(response_text)

        logger.info(f"调试页面已保存到 {debug_path}")
        return debug_path

    except Exception as e:
        logger.error(f"保存调试文件失败: {e}")
        return None


def _get_safe_filename(title: str, url: str) -> str:
    """获取安全的文件名

    Args:
        title: 原始标题
        url: 页面URL

    Returns:
        安全的文件名
    """
    # 清理章节标题，移除非法字符
    safe_title = ''.join(char for char in title if char not in INVALID_FILENAME_CHARS)

    # 如果标题为空或过于简单，使用URL的一部分作为备选
    if not safe_title or len(safe_title) < 2:
        safe_title = _extract_filename_from_url(url)

    return safe_title or f"chapter_{hash(url) % 1000}"


def _extract_filename_from_url(url: str) -> str:
    """从URL中提取文件名

    Args:
        url: 页面URL

    Returns:
        提取的文件名
    """
    url_parts = url.split('/')
    for part in reversed(url_parts):
        if part and not part.endswith('.html') and len(part) > 1:
            return part
    return ""