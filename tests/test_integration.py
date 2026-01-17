"""集成测试 - 测试爬虫核心流程"""

import sys
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from bs4 import BeautifulSoup
from src.crawer_77shuwu import SevenSevenShuWuCrawler
from src.crawer_huanghelou import HuangHeLouCrawler


class MockResponse:
    """模拟 HTTP 响应"""
    def __init__(self, text, status_code=200):
        self.text = text
        self.status_code = status_code
        self.apparent_encoding = 'utf-8'

    def raise_for_status(self):
        if self.status_code != 200:
            raise Exception(f"HTTP {self.status_code}")


class TestSevenSevenShuWuCrawler(unittest.TestCase):
    """77读书网爬虫集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

        self.crawler = SevenSevenShuWuCrawler(
            homepage_url="http://test.com/novel/123/",
            base_url="http://test.com",
            max_chapters=2,
            max_retries=2,
            debug_enabled=False,
        )

    def tearDown(self):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def test_extract_novel_title(self):
        """测试提取小说标题"""
        html = '<html><h1>测试小说</h1></html>'
        soup = BeautifulSoup(html, 'html.parser')
        title = self.crawler._extract_novel_title(soup)
        self.assertEqual(title, "测试小说")

    def test_extract_novel_id(self):
        """测试提取小说ID"""
        novel_id = self.crawler._extract_novel_id("http://test.com/novel/456/")
        self.assertEqual(novel_id, "456")

    def test_is_chapter_link(self):
        """测试章节链接判断"""
        # 包含小说ID的章节链接
        self.assertTrue(
            self.crawler._is_chapter_link("/chapter/123/1.html", "123")
        )
        # 普通章节链接
        self.assertTrue(
            self.crawler._is_chapter_link("/chapter/456/2.html", "")
        )
        # 非章节链接
        self.assertFalse(
            self.crawler._is_chapter_link("/author/test", "123")
        )

    def test_deduplicate_and_sort_links(self):
        """测试去重和排序"""
        links = [
            ("第一章", "http://test.com/chapter/2.html"),
            ("第二章", "http://test.com/chapter/1.html"),
            ("第一章", "http://test.com/chapter/2.html"),  # 重复
        ]
        result = self.crawler._deduplicate_and_sort_links(links)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][1], "http://test.com/chapter/1.html")

    def test_extract_chapter_title_from_h1(self):
        """测试从h1提取章节标题"""
        html = '<html><h1>第一章 测试内容</h1></html>'
        soup = BeautifulSoup(html, 'html.parser')
        title = self.crawler._extract_chapter_title(soup, "http://test.com")
        self.assertEqual(title, "第一章 测试内容")

    def test_clean_content(self):
        """测试内容清理"""
        content = "测试内容\n\n\n\n多余空行"
        cleaned = self.crawler._clean_content(content)
        self.assertNotIn("\n\n\n", cleaned)

    @patch('src.crawer_77shuwu.requests.get')
    def test_send_request_success(self, mock_get):
        """测试成功发送请求"""
        mock_get.return_value = MockResponse("<html></html>", 200)
        response = self.crawler._send_request("http://test.com")
        self.assertEqual(response.status_code, 200)

    def test_send_request_raises_exception_on_404(self):
        """测试请求404时抛出异常"""
        import logging
        from unittest.mock import patch

        # 临时设置日志级别为 CRITICAL 以上，抑制 ERROR 输出
        logging.getLogger('novel_crawler').setLevel(logging.CRITICAL + 1)

        try:
            with patch('src.crawer_77shuwu.requests.get') as mock_get:
                mock_get.return_value = MockResponse("<html></html>", 404)
                with self.assertRaises(Exception) as context:
                    self.crawler._send_request("http://test.com")
                self.assertIn("404", str(context.exception))
        finally:
            # 恢复日志级别
            logging.getLogger('novel_crawler').setLevel(logging.INFO)


class TestHuangHeLouCrawler(unittest.TestCase):
    """黄鹤楼文学爬虫集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.crawler = HuangHeLouCrawler(
            homepage_url="http://test.com/novel/123/",
            base_url="http://test.com",
            max_chapters=2,
            debug_enabled=False,
        )

    def test_parse_args(self):
        """测试参数解析"""
        import sys
        # 临时清空命令行参数，避免测试受外部参数影响
        original_argv = sys.argv
        sys.argv = ['test']
        try:
            args = HuangHeLouCrawler.parse_args()
            self.assertEqual(args.max_chapters, 100000)
            self.assertEqual(args.max_retries, 3)
        finally:
            sys.argv = original_argv


class TestBaseCrawlerIntegration(unittest.TestCase):
    """基类集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def test_clear_existing_files(self):
        """测试清空已存在文件"""
        from src.crawer_77shuwu import SevenSevenShuWuCrawler

        # 创建测试文件
        with open("test.json", "w") as f:
            f.write('{"test": "data"}')
        with open("test.txt", "w") as f:
            f.write("test content")

        crawler = SevenSevenShuWuCrawler(
            homepage_url="http://test.com",
            base_url="http://test.com",
        )

        crawler.clear_existing_files("test")

        # 验证文件被清空
        with open("test.json") as f:
            self.assertEqual(f.read(), '{}')
        with open("test.txt") as f:
            self.assertEqual(f.read(), '')


class TestUtilsIntegration(unittest.TestCase):
    """工具函数集成测试"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def test_save_and_load_json(self):
        """测试JSON保存和加载"""
        from src.utils import save_chapter_to_json, load_existing_json

        data = {"第一章": "内容1", "第二章": "内容2"}
        save_chapter_to_json("test", data)

        loaded = load_existing_json("test")
        self.assertEqual(loaded, data)

    def test_load_nonexistent_json(self):
        """测试加载不存在的JSON"""
        from src.utils import load_existing_json
        result = load_existing_json("nonexistent")
        self.assertEqual(result, {})

    def test_save_novel_to_txt(self):
        """测试保存小说为TXT"""
        from src.utils import save_novel_to_txt

        json_content = {
            "第 1 章": "第一章内容\n\n",
            "第 2 章": "第二章内容\n\n",
        }
        normalized_titles = ["第 1 章", "第 2 章"]

        filepath = save_novel_to_txt("test", normalized_titles, json_content)

        self.assertTrue(os.path.exists(filepath))
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("第一章内容", content)
            self.assertIn("第二章内容", content)

    def test_ensure_directory(self):
        """测试目录创建"""
        from src.utils import ensure_directory
        test_dir = os.path.join(self.temp_dir, "test_subdir")

        ensure_directory(test_dir)
        self.assertTrue(os.path.exists(test_dir))


class TestRealWebRequest(unittest.TestCase):
    """真实网络请求测试（不使用mock）"""

    def setUp(self):
        """设置测试环境"""
        self.temp_dir = tempfile.mkdtemp()
        self.original_dir = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """清理测试环境"""
        os.chdir(self.original_dir)
        shutil.rmtree(self.temp_dir)

    def test_real_request_to_77shuwu(self):
        """测试真实请求到77读书网"""
        from src.crawer_77shuwu import SevenSevenShuWuCrawler

        crawler = SevenSevenShuWuCrawler(
            homepage_url="http://www.77shuku.org/novel/62042/",
            base_url="https://www.77shuwu.org",
            max_chapters=1,
            debug_enabled=False,
        )

        # 发送真实请求到小说主页
        response = crawler._send_request("http://www.77shuku.org/novel/62042/")

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.text)

    def test_real_request_to_huanghelou(self):
        """测试真实请求到黄鹤楼文学"""
        from src.crawer_huanghelou import HuangHeLouCrawler

        crawler = HuangHeLouCrawler(
            homepage_url="https://www.hhlwx.org/hhlchapter/69730.html",
            base_url="https://www.hhlwx.org",
            max_chapters=1,
            debug_enabled=False,
        )

        # 发送真实请求到小说主页
        response = crawler._send_request("https://www.hhlwx.org/hhlchapter/69730.html")

        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(response.text)

    def test_77shuwu_headers(self):
        """测试77读书网请求头设置"""
        from src.crawer_77shuwu import SevenSevenShuWuCrawler

        crawler = SevenSevenShuWuCrawler(
            homepage_url="http://www.77shuku.org/novel/62042/",
            base_url="https://www.77shuwu.org",
        )

        self.assertIn("User-Agent", crawler.headers)
        self.assertIsNotNone(crawler.headers["User-Agent"])

    def test_random_delay_range(self):
        """测试随机延迟在合理范围内"""
        from src.utils import random_delay
        import time

        start = time.time()
        random_delay(0.05, 0.1)  # 50-100ms
        elapsed = time.time() - start

        self.assertGreaterEqual(elapsed, 0.05)
        self.assertLessEqual(elapsed, 0.15)  # 留一点余量

    def test_logger_output(self):
        """测试日志输出"""
        from src.utils import setup_logger
        import logging

        logger = setup_logger()
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'novel_crawler')
        self.assertEqual(logger.level, logging.INFO)


def run_tests():
    """运行所有集成测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    suite.addTests(loader.loadTestsFromTestCase(TestSevenSevenShuWuCrawler))
    suite.addTests(loader.loadTestsFromTestCase(TestHuangHeLouCrawler))
    suite.addTests(loader.loadTestsFromTestCase(TestBaseCrawlerIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestUtilsIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestRealWebRequest))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
