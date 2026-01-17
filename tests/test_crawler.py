"""测试脚本 - 测试爬虫基本功能"""

import sys
import os

# 添加项目根目录到路径，使 src 成为一个包
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import unittest
from unittest.mock import Mock, patch, MagicMock
from src.base_crawler import BaseCrawler
from src.utils import (
    setup_logger,
    normalize_chapter_title,
    random_delay,
    _get_safe_filename,
)


class TestNormalizeChapterTitle(unittest.TestCase):
    """测试章节标题规范化"""

    def test_title_starting_with_chapter(self):
        """测试以'第'开头的标题"""
        title, page_num = normalize_chapter_title("第123章 测试标题", 1)
        self.assertEqual(page_num, 2)

    def test_title_with_number_only(self):
        """测试纯数字标题"""
        title, page_num = normalize_chapter_title("456 测试内容", 1)
        self.assertEqual(page_num, 457)
        # 标题应该被规范化，数字被提取作为章节号
        self.assertTrue("456" in title or "第" in title)

    def test_title_without_number(self):
        """测试无数字标题"""
        title, page_num = normalize_chapter_title("测试章节", 5)
        # 无数字且不以"第"开头时，页码递增，标题保持不变
        self.assertEqual(page_num, 6)
        self.assertEqual(title, "测试章节")

    def test_title_filters_invalid_text(self):
        """测试过滤无效文本"""
        title, page_num = normalize_chapter_title("立即阅读", 1)
        self.assertNotIn("立即阅读", title)


class TestGetSafeFilename(unittest.TestCase):
    """测试安全文件名生成"""

    def test_removes_invalid_chars(self):
        """测试移除非法字符"""
        safe_name = _get_safe_filename("测试/文件:名?称", "http://example.com")
        self.assertNotIn("/", safe_name)
        self.assertNotIn(":", safe_name)
        self.assertNotIn("?", safe_name)

    def test_empty_title_uses_url(self):
        """测试空标题使用URL"""
        safe_name = _get_safe_filename("", "http://example.com/chapter/123")
        self.assertIsNotNone(safe_name)
        self.assertGreater(len(safe_name), 0)


class TestBaseCrawler(unittest.TestCase):
    """测试爬虫基类"""

    def test_cannot_instantiate_abstract_class(self):
        """测试无法实例化抽象类"""
        with self.assertRaises(TypeError):
            BaseCrawler(
                homepage_url="http://example.com/novel/1",
                base_url="http://example.com",
            )


class TestSetupLogger(unittest.TestCase):
    """测试日志配置"""

    def test_logger_creation(self):
        """测试日志器创建"""
        logger = setup_logger()
        self.assertIsNotNone(logger)
        self.assertEqual(logger.name, 'novel_crawler')

    def test_logger_has_handlers(self):
        """测试日志器有处理器"""
        logger = setup_logger()
        self.assertGreater(len(logger.handlers), 0)


class TestRandomDelay(unittest.TestCase):
    """测试随机延迟"""

    @patch('time.sleep')
    def test_random_delay_calls_sleep(self, mock_sleep):
        """测试随机延迟调用sleep"""
        random_delay(0.1, 0.2)
        mock_sleep.assert_called_once()
        # 验证延迟时间在范围内
        call_args = mock_sleep.call_args[0][0]
        self.assertGreaterEqual(call_args, 0.1)
        self.assertLessEqual(call_args, 0.2)


def run_tests():
    """运行所有测试"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()

    # 添加所有测试类
    suite.addTests(loader.loadTestsFromTestCase(TestNormalizeChapterTitle))
    suite.addTests(loader.loadTestsFromTestCase(TestGetSafeFilename))
    suite.addTests(loader.loadTestsFromTestCase(TestBaseCrawler))
    suite.addTests(loader.loadTestsFromTestCase(TestSetupLogger))
    suite.addTests(loader.loadTestsFromTestCase(TestRandomDelay))

    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    sys.exit(run_tests())
