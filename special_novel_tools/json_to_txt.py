#!/usr/bin/env python3
"""将小说 JSON 文件转换为 TXT 格式。"""

import argparse
import json
import re


def parse_chapter_key(key: str) -> tuple[int, int, str]:
    """解析章节 key，返回 (卷号, 章号, 原 key)。"""
    match = re.match(r"第(\d+)卷、第(\d+)章", key)
    if match:
        return int(match.group(1)), int(match.group(2)), key
    return 999, 999, key


def convert_json_to_txt(json_path: str, txt_path: str) -> None:
    """将 JSON 格式的小说转换为 TXT 格式。"""
    print(f"读取 JSON 文件: {json_path}")

    with open(json_path, encoding="utf-8") as file:
        data = json.load(file)

    print(f"共 {len(data)} 章")

    sorted_items = sorted(data.items(), key=lambda item: parse_chapter_key(item[0]))

    print(f"写入 TXT 文件: {txt_path}")
    with open(txt_path, "w", encoding="utf-8") as file:
        for key, content in sorted_items:
            title_line = key.replace("、", " ")
            file.write(f"{title_line}\n")
            file.write(f"{content}\n\n")

    print("转换完成！")


def main() -> None:
    """主函数。"""
    parser = argparse.ArgumentParser(description="将小说 JSON 文件转换为 TXT 格式")
    parser.add_argument("json_file", help="JSON 文件路径")
    parser.add_argument(
        "--txt_file",
        help="输出 TXT 文件路径，默认与 JSON 文件同名但扩展名为 .txt",
    )

    args = parser.parse_args()
    txt_file = args.txt_file or f"{args.json_file.rsplit('.', 1)[0]}.txt"
    convert_json_to_txt(args.json_file, txt_file)


if __name__ == "__main__":
    main()
