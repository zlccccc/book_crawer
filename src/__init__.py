"""Novel Crawler - 小说爬虫系统"""

from .base_crawler import BaseCrawler
from .config import config_manager
from .crawler_77shuwu import SevenSevenShuWuCrawler
from .crawler_huanghelou import HuangHeLouCrawler
from .utils import setup_logger

__version__ = "0.2.0"

__all__ = [
    "BaseCrawler",
    "SevenSevenShuWuCrawler",
    "HuangHeLouCrawler",
    "config_manager",
    "setup_logger"
]
