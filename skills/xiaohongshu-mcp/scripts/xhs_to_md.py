#!/usr/bin/env python3
"""
Xiaohongshu to Markdown Converter
Converts Xiaohongshu notes to markdown files and saves to F:\openclaw_data

Usage:
    python xhs_to_md.py <command> [options]

Commands:
    crawl <feed_id> <xsec_token>         Crawl single note to markdown
    search_crawl <keyword> [count]       Search and crawl multiple notes
"""

import argparse
import json
import sys
import os
from datetime import datetime
import requests

BASE_URL = "http://localhost:18060"
TIMEOUT = 60
OUTPUT_DIR = r"F:\openclaw_data"


def sanitize_filename(name):
    """Sanitize filename by removing invalid characters."""
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        name = name.replace(char, '_')
    return name[:100]  # Limit length


def save_to_markdown(note_data, feed_id):
    """Save note data to markdown file."""
    note = note_data.get("note", {})
    comments = note_data.get("comments", {})
    interact = note.get("interactInfo", {})
    user = note.get("user", {})

    # Build markdown content
    md_content = []
    md_content.append(f"# {note.get('title', '无标题')}\n")
    md_content.append(f"**作者:** {user.get('nickname', '未知')}\n")
    md_content.append(f"**链接:** https://www.xiaohongshu.com/explore/{note.get('noteId', '')}\n")
    md_content.append(f"**收藏量:** {interact.get('collectedCount', '0')}\n")
    md_content.append(f"**点赞量:** {interact.get('likedCount', '0')}\n")
    md_content.append(f"**评论量:** {interact.get('commentCount', '0')}\n")
    md_content.append(f"**发布时间:** {note.get('time', '未知')}\n")
    md_content.append(f"**IP位置:** {note.get('ipLocation', '未知')}\n")
    md_content.append("\n---\n")

    # Tags
    tag_list = note.get("tagList", {})
    if tag_list:
        tags = tag_list.get("tagList", [])
        if tags:
            md_content.append("**标签:** ")
            tag_names = [tag.get("tagName", "") for tag in tags]
            md_content.append(", ".join(tag_names) + "\n\n")

    # Content
    md_content.append("## 内容\n\n")
    md_content.append(note.get('desc', '无内容') + "\n\n")

    # Images
    image_list = note.get("imageList", [])
    if image_list:
        md_content.append("## 图片\n\n")
        for img in image_list:
            md_content.append(f"![图片]({img.get('urlDefault', '')})\n\n")

    # Comments
    comment_list = comments.get("list", [])
    if comment_list:
        md_content.append(f"## 热门评论 (前10条)\n\n")
        for i, c in enumerate(comment_list[:10], 1):
            user_info = c.get("userInfo", {})
            md_content.append(f"### {i}. {user_info.get('nickname', '匿名')}\n")
            md_content.append(f"{c.get('content', '')}\n")
            md_content.append(f"👍 {c.get('subCommentCount', 0)} | ❤️ {c.get('likedCount', 0)}\n\n")

    # Metadata
    md_content.append("\n---\n")
    md_content.append("## 元数据\n\n")
    md_content.append(f"```json\n{json.dumps(note_data, ensure_ascii=False, indent=2)}\n```\n")

    # Save file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_title = sanitize_filename(note.get('title', '无标题'))
    filename = f"{timestamp}_{safe_title}_{feed_id[:8]}.md"
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(''.join(md_content))

    return filepath


def crawl_note(feed_id, xsec_token):
    """Crawl a single note and save to markdown."""
    try:
        payload = {
            "feed_id": feed_id,
            "xsec_token": xsec_token,
            "load_all_comments": True
        }
        resp = requests.post(
            f"{BASE_URL}/api/v1/feeds/detail",
            json=payload,
            timeout=TIMEOUT
        )
        data = resp.json()

        if data.get("success"):
            note_data = data.get("data", {}).get("data", {})
            filepath = save_to_markdown(note_data, feed_id)
            note = note_data.get("note", {})
            print(f"✅ 已保存: {note.get('title', '无标题')}")
            print(f"   📁 路径: {filepath}")
            return filepath
        else:
            print(f"❌ 获取笔记失败: {data.get('error', '未知错误')}")
            return None
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 MCP 服务器。请确保 xiaohongshu-mcp 正在运行")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return None


def search_and_crawl(keyword, count=5):
    """Search notes and crawl top results."""
    try:
        payload = {
            "keyword": keyword,
            "filters": {
                "sort_by": "综合",
                "note_type": "不限",
                "publish_time": "不限"
            }
        }
        resp = requests.post(
            f"{BASE_URL}/api/v1/feeds/search",
            json=payload,
            timeout=TIMEOUT
        )
        data = resp.json()

        if data.get("success"):
            feeds = data.get("data", {}).get("feeds", [])
            actual_count = min(count, len(feeds))

            print(f"🔍 找到 {len(feeds)} 条笔记，将爬取前 {actual_count} 条\n")

            saved_files = []
            for i, feed in enumerate(feeds[:actual_count], 1):
                note_card = feed.get("noteCard", {})
                title = note_card.get('displayTitle', '无标题')
                feed_id = feed.get('id')
                xsec_token = feed.get('xsecToken')

                print(f"[{i}/{actual_count}] 爬取: {title}")
                filepath = crawl_note(feed_id, xsec_token)
                if filepath:
                    saved_files.append(filepath)
                print()

            print(f"\n✅ 完成! 共保存 {len(saved_files)} 个文件到 F:\\openclaw_data")
            return saved_files
        else:
            print(f"❌ 搜索失败: {data.get('error', '未知错误')}")
            return []
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到 MCP 服务器")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 错误: {str(e)}")
        return []


def main():
    parser = argparse.ArgumentParser(
        description="Xiaohongshu to Markdown Converter",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # crawl command
    crawl_parser = subparsers.add_parser("crawl", help="Crawl single note")
    crawl_parser.add_argument("feed_id", help="Feed ID")
    crawl_parser.add_argument("xsec_token", help="Security token")

    # search_crawl command
    search_parser = subparsers.add_parser("search_crawl", help="Search and crawl multiple notes")
    search_parser.add_argument("keyword", help="Search keyword")
    search_parser.add_argument("count", nargs="?", type=int, default=5, help="Number of notes to crawl (default: 5)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    if args.command == "crawl":
        crawl_note(args.feed_id, args.xsec_token)
    elif args.command == "search_crawl":
        search_and_crawl(args.keyword, args.count)


if __name__ == "__main__":
    main()
