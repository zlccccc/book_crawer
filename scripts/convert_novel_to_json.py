#!/usr/bin/env python3
"""
将小说 TXT 文件转换为 JSON 格式，并插入 docx 文件内容

功能：
1. 将 TXT 转换为 {标题: 内容} 的 JSON 格式
2. 章节标题格式化：1、xxx → 第1卷、第1章 xxx
3. 读取 docx 文件内容并插入到合适位置
"""

import json
import os
import re
from typing import Optional

from docx import Document


def parse_chapter_number(title: str) -> Optional[tuple[int, int]]:
    """解析章节标题，返回 (卷号, 章号)"""
    # 匹配 "1、xxx" 或 "2、xxx" 等格式
    match = re.match(r'^(\d+)、\s*(.+)', title.strip())
    if match:
        chapter_num = int(match.group(1))
        return None, chapter_num
    return None


def read_docx_content(docx_path: str) -> Optional[str]:
    """读取 docx 文件内容"""
    try:
        doc = Document(docx_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(paragraphs)
    except Exception as e:
        print(f"读取 docx 文件失败 {docx_path}: {e}")
        return None


def parse_volume_chapter_from_filename(filename: str) -> tuple[int | None, int | None]:
    """
    从 docx 文件名解析卷号和章号

    Returns:
        (卷号, 章号)，如果解析失败返回 (None, None)
    """
    # 中文数字映射
    cn_nums = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
               '六': 6, '七': 7, '八': 8, '九': 9}

    # 提取卷号
    vol_match = re.search(r'第([一二三四五六七八九])卷', filename)
    volume = cn_nums.get(vol_match.group(1), 0) if vol_match else None

    # 提取章号
    ch_match = re.search(r'(\d+)、', filename)
    chapter = int(ch_match.group(1)) if ch_match else None

    return volume, chapter


def parse_docx_filename(filename: str) -> Optional[str]:
    """
    解析 docx 文件名，只提取标题

    原因：docx 文件的卷号可能与实际 TXT 不一致，只按标题匹配
    """
    # 去掉扩展名
    title_part = os.path.splitext(filename)[0]

    # 去掉卷号标记（如"第七卷"、"第3卷"等）
    title = re.sub(r'第[一二三四五六七八九十百千万]+卷[、,， ]?', '', title_part)

    # 去掉章节号标记（如"14、"、"第七章、"等）
    title = re.sub(r'^\d+[、,， ]+', '', title)
    title = re.sub(r'第[一二三四五六七八九十百千万]+章[、,， ]?', '', title)

    # 去掉多余的分隔符和空白
    title = title.strip(' 、,，')

    # 处理多章节情况（如"25、大胆  26、奇兵"），只取第一个章节标题
    title = re.sub(r'\s+\d+[、,， ].*$', '', title)

    return title if title else None


def find_chapter_position(chapters: list, target_volume: int, target_chapter: int) -> int:
    """
    在章节列表中查找目标章节的插入位置

    返回应该插入的索引位置
    """
    # 先找到卷的位置
    volume_start = 0
    for i, (v, _c, _t, _content) in enumerate(chapters):
        if v == target_volume:
            volume_start = i
            break

    # 在该卷中查找章号位置
    for i in range(volume_start, len(chapters)):
        v, c, _t, _content = chapters[i]
        if v > target_volume:
            return i  # 超过目标卷，插入卷首
        if c >= target_chapter:
            return i  # 找到位置

    # 如果没找到，插入到末尾
    return len(chapters)


def convert_txt_to_json(txt_path: str, docx_dir: str, output_path: str) -> dict:
    """
    将 TXT 文件转换为 JSON 格式，并插入 docx 内容

    Args:
        txt_path: TXT 文件路径
        docx_dir: docx 文件目录
        output_path: 输出 JSON 文件路径

    Returns:
        转换后的数据字典
    """
    print(f"开始处理文件: {txt_path}")

    # 读取所有 docx 文件
    docx_files = []
    if os.path.exists(docx_dir):
        for f in os.listdir(docx_dir):
            title = parse_docx_filename(f)
            if title:
                docx_path = os.path.join(docx_dir, f)
                content = read_docx_content(docx_path)
                if content:
                    # 尝试从文件名解析卷号和章号
                    volume, chapter = parse_volume_chapter_from_filename(f)

                    docx_files.append({
                        'title': title,
                        'content': content,
                        'filename': f,
                        'volume': volume,
                        'chapter': chapter
                    })
                    print(f"  已读取 docx: {title}")

    # 解析 TXT 文件
    chapters = []  # (卷号, 章号, 标题, 内容)
    current_volume = 1
    chapter_counter = 1

    # 用于跳过开头的版权声明
    skip_intro = True
    content_lines = []
    current_title = ""

    with open(txt_path, encoding='utf-8') as f:
        for line in f:
            line = line.rstrip('\n')
            stripped = line.strip()

            # 检测章节标题（格式：数字、标题）
            chapter_match = re.match(r'^(\d+)、\s*(.+)', stripped)

            if chapter_match:
                # 保存上一个章节
                if content_lines and current_title:
                    content = '\n'.join(content_lines).strip()
                    chapters.append((current_volume, chapter_counter, current_title, content))
                    print(f"  第{current_volume}卷 第{chapter_counter}章: {current_title}")
                    content_lines = []

                new_chapter_num = int(chapter_match.group(1))

                # 检测卷边界：章节号重置为1，表示新卷开始
                if new_chapter_num == 1 and chapter_counter > 1:
                    current_volume += 1
                    print(f"\n--- 进入第{current_volume}卷 ---")

                chapter_counter = new_chapter_num
                current_title = chapter_match.group(2)
                skip_intro = False
            elif not skip_intro and current_title:
                # 累积章节内容
                content_lines.append(line)
            elif stripped and not current_title and not skip_intro:
                # 可能是标题行（没有前导空格的内容）
                if not line.startswith('\t') and not line.startswith('　'):
                    pass  # 忽略

    # 保存最后一个章节
    if content_lines and current_title:
        content = '\n'.join(content_lines).strip()
        chapters.append((current_volume, chapter_counter, current_title, content))
        print(f"  第{current_volume}卷 第{chapter_counter}章: {current_title}")

    print(f"\n共解析 {len(chapters)} 个章节")

    # 构建结果字典
    result = {}
    for volume, chapter, title, content in chapters:
        key = f"第{volume}卷、第{chapter}章 {title}"
        result[key] = content

    # 处理 docx 文件：标题匹配且章节号相同才替换，否则按文件名插入
    print(f"\n开始处理 {len(docx_files)} 个 docx 文件...")
    replaced_count = 0
    inserted_count = 0
    not_found_count = 0

    for docx in docx_files:
        docx_title = docx['title']
        docx_title_norm = re.sub(r'[。、，,.]', '', docx_title)
        docx_vol = docx['volume']
        docx_ch = docx['chapter']
        matched_key = None

        # 查找同时满足：标题匹配 且 章号相同
        for key in result.keys():
            match = re.match(r'第(\d+)卷、第(\d+)章\s+(.+)', key)
            if match:
                existing_vol = int(match.group(1))
                existing_ch = int(match.group(2))
                existing_title = match.group(3)
                existing_title_norm = re.sub(r'[。、，,.]', '', existing_title)

                # 同时满足：标题匹配 且 章号相同
                if (docx_title_norm == existing_title_norm and
                    docx_vol == existing_vol and
                    docx_ch == existing_ch):
                    matched_key = key
                    break

        if matched_key:
            result[matched_key] = docx['content']
            print(f"  ✓ 替换: {matched_key}")
            replaced_count += 1
        else:
            # 未找到完全匹配，按文件名插入缺失章节
            if docx_vol and docx_ch:
                new_key = f"第{docx_vol}卷、第{docx_ch}章 {docx_title}"
                result[new_key] = docx['content']
                print(f"  + 插入: 第{docx_vol}卷 第{docx_ch}章 - {docx_title}")
                inserted_count += 1
            else:
                print(f"  ✗ 未找到匹配: {docx_title}")
                not_found_count += 1

    print(f"\n处理结果: 替换 {replaced_count} | 插入 {inserted_count} | 未找到 {not_found_count}")

    # 保存到 JSON 文件
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n转换完成！共 {len(result)} 章")
    print(f"输出文件: {output_path}")

    return result


def main():
    """主函数"""
    # 文件路径配置
    txt_file = "/home/zlc1114/python/crawer/others/凤傲天小说里的黄毛反派也想幸福+1-卷九第29章小说精校版.txt"
    docx_directory = "/home/zlc1114/python/crawer/others/小说删减文件/小说删减文件"
    output_file = "/home/zlc1114/python/crawer/others/凤傲天小说里的黄毛反派也想幸福.json"

    convert_txt_to_json(txt_file, docx_directory, output_file)


if __name__ == "__main__":
    main()
