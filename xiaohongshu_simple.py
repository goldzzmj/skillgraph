#!/usr/bin/env python3
"""
简单的小红书爬虫 - 直接从网页抓取内容并转成Markdown
不需要MCP服务器
"""

import requests
import re
import json
import os
from datetime import datetime
from urllib.parse import urljoin, urlparse

OUTPUT_DIR = r"F:\openclaw_data"

def sanitize_filename(name):
    """清理文件名"""
    invalid = '<>:"/\\|?*'
    for c in invalid:
        name = name.replace(c, '_')
    return name[:80]

def get_note_data(url):
    """从小红书网页URL获取笔记数据"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
    }

    try:
        # 先获取页面
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        html = response.text

        # 尝试从__INITIAL_STATE__中提取数据
        pattern = r'window\.__INITIAL_STATE__\s*=\s*({.*?});'
        match = re.search(pattern, html)

        if match:
            try:
                data_str = match.group(1)
                data = json.loads(data_str)

                # 提取笔记信息（根据小红书数据结构）
                # 注意：数据结构可能会变化，需要根据实际情况调整
                note_data = extract_note_info(data)
                return note_data
            except json.JSONDecodeError:
                print("解析JSON数据失败")
                return None
        else:
            print("未找到__INITIAL_STATE__数据")
            return None

    except Exception as e:
        print(f"获取页面失败: {str(e)}")
        return None

def extract_note_info(data):
    """从__INITIAL_STATE__中提取笔记信息"""
    # 这里的路径需要根据实际数据结构调整
    # 小红书的数据结构可能会变化
    try:
        # 常见的数据路径
        if 'note' in data:
            note = data['note']
        elif 'noteDetail' in data:
            note = data['noteDetail']['note']
        else:
            print("无法找到笔记数据")
            return None

        return note
    except Exception as e:
        print(f"提取笔记信息失败: {str(e)}")
        return None

def save_to_markdown(note_data, url):
    """保存为Markdown文件"""
    if not note_data:
        print("没有可保存的数据")
        return None

    md_lines = []

    # 标题
    title = note_data.get('title') or note_data.get('displayTitle', '无标题')
    md_lines.append(f"# {title}\n")

    # 作者信息
    user = note_data.get('user', {})
    md_lines.append(f"**作者:** {user.get('nickname', '未知')}\n")
    md_lines.append(f"**链接:** {url}\n")

    # 互动数据
    interact = note_data.get('interactInfo', {})
    md_lines.append(f"**收藏:** {interact.get('collectedCount', '0')}\n")
    md_lines.append(f"**点赞:** {interact.get('likedCount', '0')}\n")
    md_lines.append(f"**评论:** {interact.get('commentCount', '0')}\n")

    # 发布时间
    md_lines.append(f"**发布时间:** {note_data.get('time', '未知')}\n")
    md_lines.append(f"**IP位置:** {note_data.get('ipLocation', '未知')}\n")

    md_lines.append("\n---\n")

    # 标签
    tag_list = note_data.get('tagList', {})
    if isinstance(tag_list, dict):
        tags = tag_list.get('tagList', [])
    elif isinstance(tag_list, list):
        tags = tag_list
    else:
        tags = []

    if tags:
        md_lines.append("**标签:** ")
        tag_names = [tag.get('tagName', str(tag)) if isinstance(tag, dict) else str(tag) for tag in tags]
        md_lines.append(", ".join(tag_names) + "\n\n")

    # 内容
    desc = note_data.get('desc', '')
    if desc:
        md_lines.append("## 内容\n\n")
        md_lines.append(desc + "\n\n")

    # 图片
    image_list = note_data.get('imageList', [])
    if image_list:
        md_lines.append("## 图片\n\n")
        for img in image_list:
            if isinstance(img, dict):
                img_url = img.get('urlDefault') or img.get('url', '')
            else:
                img_url = str(img)

            if img_url:
                md_lines.append(f"![图片]({img_url})\n\n")

    # 视频
    video = note_data.get('video', {})
    if video and isinstance(video, dict):
        consumer = video.get('consumer', {})
        if consumer:
            md_lines.append("## 视频\n\n")
            video_url = consumer.get('originVideoKey', '')
            if video_url:
                md_lines.append(f"[视频链接]({video_url})\n\n")

    # 保存文件
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = sanitize_filename(title)
    filename = f"{timestamp}_{safe_title}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(''.join(md_lines))

    return filepath

def main():
    """主函数"""
    import sys

    print("=== 小红书爬虫 ===\n")

    # 确保输出目录存在
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 支持命令行参数或交互式输入
    if len(sys.argv) > 1:
        url = sys.argv[1].strip()
    else:
        url = input("请输入小红书笔记URL: ").strip()

    if not url:
        print("错误: URL不能为空")
        return

    if 'xiaohongshu.com' not in url:
        print("警告: 这可能不是小红书链接")

    print(f"\n正在获取: {url}")
    note_data = get_note_data(url)

    if note_data:
        print(f"✅ 成功获取笔记数据")
        print(f"   标题: {note_data.get('title', '无标题')}")

        filepath = save_to_markdown(note_data, url)
        if filepath:
            print(f"\n✅ 已保存到: {filepath}")
        else:
            print("\n❌ 保存失败")
    else:
        print("\n❌ 获取失败，可能的原因:")
        print("   - 小红书更改了网页结构")
        print("   - 需要登录才能访问该内容")
        print("   - 链接无效或笔记已被删除")

if __name__ == "__main__":
    main()
