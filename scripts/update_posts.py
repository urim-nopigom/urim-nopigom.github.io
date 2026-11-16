#!/usr/bin/env python3
"""Publish Naver RSS posts and their available thumbnail photos."""
import html
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from datetime import timezone
from email.utils import parsedate_to_datetime

ROOT = Path(__file__).resolve().parents[1]
RSS = 'https://rss.blog.naver.com/urim_cozy_study.xml'
DEST = ROOT / 'posts.json'
IMAGE_DIR = ROOT / 'images'


def request(url, referer=None):
    headers = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile Safari/604.1'}
    if referer:
        headers['Referer'] = referer
    return urllib.request.urlopen(urllib.request.Request(url, headers=headers), timeout=15)


def valid_image(url):
    try:
        p = urllib.parse.urlsplit(html.unescape(url or ''))
        h = (p.hostname or '').lower()
        return p.scheme == 'https' and (h.endswith('.pstatic.net') or h == 'blogfiles.naver.net')
    except ValueError:
        return False


class Images(HTMLParser):
    def __init__(self):
        super().__init__()
        self.meta = []
        self.img = []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == 'meta' and (a.get('property') or a.get('name') or '').lower() in ('og:image','twitter:image'):
            self.meta.append(a.get('content') or '')
        if tag == 'img':
            self.img.extend([a.get(k, '') for k in ('data-lazy-src','data-src','src')])


def post_details(url):
    p = urllib.parse.urlsplit(url)
    qs = urllib.parse.parse_qs(p.query)
    number = (qs.get('logNo') or [''])[0]
    blog_id = (qs.get('blogId') or ['urim_cozy_study'])[0]
    if not number:
        m = re.search(r'/([0-9]{7,})/?$', p.path)
        if m:
            number = m.group(1)
    if not number.isdigit() or blog_id != 'urim_cozy_study':
        return '', ''
    return f'https://m.blog.naver.com/urim_cozy_study/{number}', number


def candidates(item, post_url):
    found = []
    for node in item.iter():
        name = node.tag.rsplit('}',1)[-1].lower()
        if name in ('thumbnail','image','enclosure','content'):
            found.extend([node.attrib.get('url',''), node.text or ''])
    for field in ('description', '{http://purl.org/rss/1.0/modules/content/}encoded'):
        parser = Images()
        parser.feed(html.unescape(item.findtext(field) or ''))
        found.extend(parser.meta + parser.img)
    if not any(valid_image(x) for x in found) and post_url:
        try:
            with request(post_url) as resp:
                source = resp.read(2_000_000).decode('utf-8', 'replace')
            parser = Images()
            parser.feed(source)
            found.extend(parser.meta + parser.img)
        except Exception as exc:
            print('Post page image lookup failed:', type(exc).__name__)
    return [html.unescape(x).strip() for x in found if valid_image(x)]


def save_image(urls, number, referer):
    if not number:
        return ''
    for url in urls[:6]:
        try:
            with request(url, referer) as resp:
                typ = resp.headers.get_content_type().lower()
                ext = {'image/jpeg':'jpg','image/png':'png','image/webp':'webp'}.get(typ)
                if not ext:
                    continue
                data = resp.read(3_000_001)
                if not data or len(data) > 3_000_000:
                    continue
            IMAGE_DIR.mkdir(exist_ok=True)
            name = f'blog-{number}.{ext}'
            dest = IMAGE_DIR / name
            if not dest.exists() or dest.read_bytes() != data:
                dest.write_bytes(data)
            return 'images/' + name
        except Exception as exc:
            print('Image download failed:', type(exc).__name__)
    return urls[0] if urls else ''


def main():
    with request(RSS) as resp:
        root = ET.fromstring(resp.read(3_000_000))
    posts = []
    for item in root.findall('./channel/item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        u = urllib.parse.urlsplit(link)
        if not title or u.scheme != 'https' or u.hostname not in ('blog.naver.com','m.blog.naver.com'):
            continue
        day = ''
        try:
            parsed = parsedate_to_datetime((item.findtext('pubDate') or '').strip())
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            day = parsed.astimezone(timezone.utc).date().isoformat()
        except (ValueError,TypeError,OverflowError):
            pass
        post_url, number = post_details(link)
        choices = candidates(item, post_url)
        image = save_image(choices, number, post_url or link) if choices else ''
        posts.append({'title':title[:160],'url':link,'date':day,'image':image})
        print('Photo found:', bool(image), 'for', title[:40])
        if len(posts) >= 6:
            break
    if not posts:
        raise RuntimeError('No RSS posts found; existing file not overwritten')
    DEST.write_text(json.dumps({'posts':posts},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print('Updated',len(posts),'posts')

if __name__ == '__main__':
    main()
