# 饭团链接海报 / Fantuan Link Poster

[中文](#中文) | [English](#english)

<a id="中文"></a>
## 中文

### 项目简介

Codex 技能：读取文章链接，提炼中文大标题并输出固定饭团插画模板的 1080×1440 PNG 海报。

### 核心能力

仅保留黑色大标题和二维码，关键词支持蓝紫渐变；程序排版；原图与 540×720 缩略图二维码校验。底图源自用户提供的模板，使用内置 imagegen 移除标题蓝底、副标题框、摘要卡片和假二维码，保留饭团与装饰。

### 快速开始

需要 Python 3.10+。macOS 自动查找苹方；其他系统在 `assets/layout.json` 的 `font` 中配置中文字体路径。

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/link-to-fantuan-poster/scripts/requirements.txt
```

将 `skills/link-to-fantuan-poster` 复制到 `~/.codex/skills/`，在新会话调用 `$link-to-fantuan-poster` 并附上链接。已有同名技能时先检查差异，避免覆盖。

### 使用方法

代理负责读取并提炼正文，脚本负责抓取和确定性排版。JSON 必填 `url`、`title`；可选 `highlight` 指定渐变关键词。旧 `subtitle`、`summary` 字段忽略。

```sh
.venv/bin/python skills/link-to-fantuan-poster/scripts/poster.py fetch https://doc.niallspace.com/ai/posts/components-dev
.venv/bin/python skills/link-to-fantuan-poster/scripts/poster.py render examples/components-dev.json --out output/my-poster
```

输出 `poster.png`、`qr.png`、`copy.json`、`verification.json`。输出目录必须无同名文件。文案溢出需精简；链接过长会报错；无法读取正文时由代理尝试浏览器或请求正文，不生成猜测摘要。

### 配置

`skills/link-to-fantuan-poster/assets/layout.json` 集中配置字号、颜色、区域和字体。底图固定，日常生成不调用图像生成服务。

### 开发与验证

```sh
.venv/bin/python -m unittest discover -s skills/link-to-fantuan-poster/scripts -p 'test_*.py'
```

六项测试覆盖导出与重复输出、长标题、长链接、过密二维码、读取失败以及旧摘要字段不渲染。交付前还需人工查看海报，程序解码不替代手机实扫。

<a id="english"></a>
## English

### Overview

A Codex skill that reads an article URL, extracts a short Chinese headline, and exports a 1080×1440 PNG using a fixed illustrated rice-ball template.

### Features

Only a large black headline and QR code, with optional blue-purple gradient keywords; deterministic typography; QR decoding at full size and 540×720. The user supplied the template. Built-in imagegen removed the title pill, subtitle pill, summary card and fake QR symbol while preserving the character and decorations.

### Quick Start

Requires Python 3.10+. PingFang is located automatically on macOS. On other systems, configure a Chinese font path in the `font` field of `assets/layout.json`.

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r skills/link-to-fantuan-poster/scripts/requirements.txt
```

Copy `skills/link-to-fantuan-poster` into `~/.codex/skills/`, then invoke `$link-to-fantuan-poster` with a URL in a new session. Inspect any existing installation before replacing it.

### Usage

The agent reads and summarizes the article; the script fetches content and renders the approved copy. JSON requires `url` and `title`; optional `highlight` selects gradient text. Legacy `subtitle` and `summary` fields are ignored.

```sh
.venv/bin/python skills/link-to-fantuan-poster/scripts/poster.py fetch https://doc.niallspace.com/ai/posts/components-dev
.venv/bin/python skills/link-to-fantuan-poster/scripts/poster.py render examples/components-dev.json --out output/my-poster
```

Exports `poster.png`, `qr.png`, `copy.json`, and `verification.json`. Existing output files are not overwritten. Shorten overflowing copy; excessively long URLs are rejected. If content cannot be read, the agent tries a browser or requests the article text instead of inventing a summary.

### Configuration

`skills/link-to-fantuan-poster/assets/layout.json` centralizes font sizes, colors, regions and font selection. Routine rendering reuses the background without calling an image generation service.

### Development and Verification

```sh
.venv/bin/python -m unittest discover -s skills/link-to-fantuan-poster/scripts -p 'test_*.py'
```

Six tests cover export and overwrite protection, long titles, long URLs, dense QR rejection, fetch failure, and omission of legacy summary fields. Visually inspect the final poster before delivery; software decoding does not replace scanning with a phone.
