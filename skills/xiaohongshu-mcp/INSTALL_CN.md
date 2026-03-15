# 小红书爬虫配置指南

## 已完成
✅ 技能已安装: `xiaohongshu-mcp`
✅ 输出目录已创建: `F:\openclaw_data`
✅ Markdown转换脚本已创建: `xhs_to_md.py`

## 需要手动完成的步骤

### 1. 下载 MCP 服务器二进制文件

访问 GitHub Releases 页面下载 Windows 版本:
https://github.com/xpzouying/xiaohongshu-mcp/releases

需要下载这两个文件:
- `xiaohongshu-mcp-windows-amd64.exe` (MCP服务器)
- `xiaohongshu-login-windows-amd64.exe` (登录工具)

建议保存到: `C:\Users\GX\xiaohongshu-mcp\` (或你喜欢的位置)

### 2. 首次登录(只需一次)

打开 PowerShell/CMD，运行登录工具:
```powershell
cd C:\Users\GX\xiaohongshu-mcp
.\xiaohongshu-login-windows-amd64.exe
```

会自动打开浏览器显示二维码，用**小红书APP**扫描登录。

⚠️ **重要**: 登录后不要在其他浏览器登录同一小红书账号，否则会失效。

### 3. 启动 MCP 服务器

每次使用前需要启动 MCP 服务器(保持运行):

```powershell
cd C:\Users\GX\xiaohongshu-mcp
.\xiaohongshu-mcp-windows-amd64.exe
```

服务器会在 `http://localhost:18060` 运行。

---

## 使用方法

### 方法1: 搜索并批量爬取

```powershell
cd C:\Users\GX\.openclaw\workspace\skills\xiaohongshu-mcp\scripts
python xhs_to_md.py search_crawl "关键词" 5
```

参数说明:
- `"关键词"` - 搜索关键词
- `5` - 爬取数量(可选，默认5条)

示例:
```powershell
python xhs_to_md.py search_crawl "户外电源" 10
python xhs_to_md.py search_crawl "咖啡机推荐"
```

### 方法2: 爬取单条笔记

先搜索获取 feed_id 和 xsec_token:
```powershell
python xhs_client.py search "关键词"
```

然后用这两个信息爬取:
```powershell
python xhs_to_md.py crawl "feed_id" "xsec_token"
```

---

## 输出文件

爬取的文件会保存为 Markdown 格式:
- **路径**: `F:\openclaw_data\`
- **文件名格式**: `20260211_073000_标题_部分ID.md`

文件包含:
- 笔记标题、作者、链接
- 收藏量、点赞量、评论量
- 完整内容(文字+图片)
- 热门评论(前10条)
- 完整元数据(JSON格式)

---

## 其他命令

### 检查登录状态
```powershell
python xhs_client.py status
```

### 获取推荐内容
```powershell
python xhs_client.py feeds
```

---

## 常见问题

**Q: 提示无法连接到 MCP 服务器?**
A: 确保先启动 `xiaohongshu-mcp-windows-amd64.exe`

**Q: 登录后提示未登录?**
A: 检查是否在其他浏览器登录了同一账号，重新运行登录工具

**Q: 如何修改输出路径?**
A: 编辑 `xhs_to_md.py` 中的 `OUTPUT_DIR` 变量

---

## 技能位置
- 技能目录: `C:\Users\GX\.openclaw\workspace\skills\xiaohongshu-mcp\`
- Python脚本: `scripts\xhs_client.py` (基础客户端)
- Python脚本: `scripts\xhs_to_md.py` (Markdown转换，我们新增的)
- 配置文件: `INSTALL_CN.md` (本文件)
