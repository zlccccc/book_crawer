from __future__ import annotations

import json
import os
from typing import Any


class ConfigManager:
    """配置管理类"""

    def __init__(self, config_file: str = "config.json"):
        """初始化配置管理器

        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.config: dict[str, Any] = self._load_config()

    def _load_config(self) -> dict[str, Any]:
        """加载配置文件

        Returns:
            配置字典
        """
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, encoding='utf-8') as f:
                    loaded = json.load(f)
                    if isinstance(loaded, dict):
                        return dict(loaded)
                    return {}
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                return {}
        return {}

    def save_config(self) -> None:
        """保存配置到文件
        """
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存配置文件失败: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """获取配置值

        Args:
            key: 配置键
            default: 默认值

        Returns:
            配置值或默认值
        """
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        self.config[key] = value

    def get_crawler_config(self, crawler_name: str) -> dict[str, Any]:
        """获取特定爬虫的配置

        Args:
            crawler_name: 爬虫名称

        Returns:
            爬虫配置字典
        """
        crawlers = self.config.get('crawlers', {})
        if not isinstance(crawlers, dict):
            return {}
        crawler_config = crawlers.get(crawler_name, {})
        if not isinstance(crawler_config, dict):
            return {}
        return dict(crawler_config)

    def set_crawler_config(self, crawler_name: str, config: dict[str, Any]) -> None:
        """设置特定爬虫的配置

        Args:
            crawler_name: 爬虫名称
            config: 爬虫配置字典
        """
        if 'crawlers' not in self.config:
            self.config['crawlers'] = {}
        self.config['crawlers'][crawler_name] = config


# 创建全局配置实例
config_manager = ConfigManager()
