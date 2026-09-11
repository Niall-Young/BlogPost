#!/usr/bin/env python3
"""Fetch article evidence or render approved copy on the fixed poster template."""
import argparse
import json
import re
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit
from PIL import Image, ImageDraw, ImageFont
import qrcode
import zxingcpp
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]

def valid_url(url):
    parsed = urlsplit(url)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or any(c.isspace() for c in url):
        raise ValueError('Provide a complete HTTP(S) URL without whitespace')
    return url

def fetch(url):
    valid_url(url)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    with urllib.request.urlopen(req, timeout=30) as response:
        raw = response.read(5_000_001)
        if len(raw) > 5_000_000:
            raise ValueError('Page too large; use browser extraction')
        soup = BeautifulSoup(raw, 'html.parser')
    for el in soup.select('script, style, nav, footer, header, aside'):
        el.decompose()
    heading = soup.find('h1')
    body = soup.select_one('.article-body') or soup.find('article') or soup.find('main')
    if body is None:
        raise ValueError('No article body found; use browser extraction or ask for article text')
    text = body.get_text('\n', strip=True)
    if len(text) < 100:
        raise ValueError('Insufficient article text; use browser extraction or ask for article text')
    return {'url': url, 'source_title': heading.get_text(' ', strip=True) if heading else '', 'body': text}

def get_font(size, bold=False):
    config = json.loads((ROOT / 'assets/layout.json').read_text())
    paths = [Path(config['font'])] if config.get('font') else []
    paths += list(Path('/System/Library/AssetsV2/com_apple_MobileAsset_Font8').glob('*/AssetData/PingFang.ttc'))
    paths += [Path('/System/Library/Fonts/PingFang.ttc'), Path('/System/Library/Fonts/STHeiti Medium.ttc')]
    for path in paths:
        if path.is_file():
            # Locate the actual Simplified Chinese weight in the font collection.
            for idx in range(30):
                try:
                    font = ImageFont.truetype(str(path), size, index=idx)
                except OSError:
                    break
                family, style = font.getname()
                if 'PingFang SC' == family and style == ('Semibold' if bold else 'Regular'):
                    return font
            return ImageFont.truetype(str(path), size)
    raise ValueError('Chinese font missing; set assets/layout.json font to a CJK font path')

def wrap(text, font, width):
    lines = []
    for paragraph in text.split('\n'):
        line = ''
        for token in re.findall(r'[A-Za-z0-9]+(?:[ /+.-][A-Za-z0-9]+)*|.', paragraph):
            if font.getlength(token) > width:
                raise ValueError('Unbreakable text exceeds region width; shorten copy')
            if line and font.getlength(line + token) > width:
                if token in '，。！？；：、）》」』' and line:
                    tail = line[-1]
                    lines.append(line[:-1].rstrip())
                    line = tail + token
                else:
                    lines.append(line.rstrip())
                    line = token.lstrip()
            else:
                line += token
        if line:
            lines.append(line.rstrip())
    return lines

def draw_region(draw, text, spec):
    x, y, width, height = spec['box']
    font = get_font(spec['size'], spec.get('bold', False))
    lines = wrap(text, font, width)
    total = len(lines) * spec['line_height']
    if len(lines) > spec['max_lines'] or total > height:
        raise ValueError('Text overflows fixed region; shorten copy: ' + text)
    top = y + (height - total) / 2
    for i, line in enumerate(lines):
        left = x + (width - font.getlength(line)) / 2 if spec['align'] == 'center' else x
        draw.text((left, top + i * spec['line_height']), line, font=font, fill=spec['color'], anchor='lt')
    return lines

def render(data, output):
    url = valid_url(data['url'])
    for field in ('title', 'subtitle', 'summary'):
        if not isinstance(data.get(field), str) or not data[field].strip():
            raise ValueError('Missing nonempty field: ' + field)
    config = json.loads((ROOT / 'assets/layout.json').read_text())
    canvas = Image.open(ROOT / 'assets/background.png').convert('RGB').resize(tuple(config['size']), Image.Resampling.LANCZOS)
    draw = ImageDraw.Draw(canvas)
    lines = {key: draw_region(draw, data[key], config[key]) for key in ('title', 'subtitle', 'summary')}
    qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_M, border=4, box_size=1)
    qr.add_data(url)
    qr.make(fit=True)
    x, y, side = config['qr']
    modules = len(qr.get_matrix())
    scale = side // modules
    if scale < 3:
        raise ValueError('URL too long for readable QR in fixed region; request a shorter user-approved URL')
    qr.box_size = scale
    tile = qr.make_image(fill_color='#23334B', back_color='white').convert('RGB')
    canvas.paste(tile, (x + (side-tile.width)//2, y + (side-tile.height)//2))
    checks = {}
    for size in ((1080,1440), (540,720)):
        decoded = zxingcpp.read_barcodes(canvas.resize(size, Image.Resampling.LANCZOS))
        checks[f'{size[0]}x{size[1]}'] = any(item.text == url for item in decoded)
    if not all(checks.values()):
        raise ValueError('Final poster QR verification failed: ' + str(checks))
    output.mkdir(parents=True, exist_ok=True)
    # Never silently overwrite an existing deliverable.
    for name in ('poster.png', 'qr.png', 'copy.json', 'verification.json'):
        if (output / name).exists():
            raise ValueError('Output already exists; use a new output directory: ' + str(output))
    canvas.save(output / 'poster.png')
    tile.save(output / 'qr.png')
    (output / 'copy.json').write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n')
    report = {'qr': checks, 'lines': lines, 'size': config['size']}
    (output / 'verification.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    fetch_args = commands.add_parser('fetch')
    fetch_args.add_argument('url')
    render_args = commands.add_parser('render')
    render_args.add_argument('copy', type=Path)
    render_args.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = fetch(args.url) if args.command == 'fetch' else render(json.loads(args.copy.read_text()), args.out)
    except Exception as exc:
        parser.exit(1, f'Error: {exc}\n')
    print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
