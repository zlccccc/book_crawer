"""Novel Crawler - 小说爬虫系统"""

from .base_crawler import BaseCrawler
from .utils import setup_logger

__version__ = "0.2.0"

__all__ = ["BaseCrawler", "setup_logger"]
