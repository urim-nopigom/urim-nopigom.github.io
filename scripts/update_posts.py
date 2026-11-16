#!/usr/bin/env python3
"""Read public Naver RSS, save titles/links/dates for the static homepage."""
import json
import html
import re
import pathlib
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

ROOT = pathlib.Path(__file__).resolve().parents[1]
RSS_URL = 'https://rss.blog.naver.com/urim_cozy_study.xml'
DEST = ROOT / 'posts.json'


def valid_url(value):
    parsed = urllib.parse.urlparse(value or '')
    return parsed.scheme == 'https' and (parsed.hostname or '').lower() in ('blog.naver.com', 'm.blog.naver.com')


# Only accept image URLs from known Naver image hosts.
IMAGE_HOSTS = {
    'blogfiles.pstatic.net',
    'postfiles.pstatic.net',
    'mblogthumb-phinf.pstatic.net',
    'phinf.pstatic.net',
    'ssl.pstatic.net',
}


def valid_image_url(value):
    try:
        url = urllib.parse.urlparse(html.unescape(value or '').strip())
        return url.scheme == 'https' and (url.hostname or '').lower() in IMAGE_HOSTS
    except ValueError:
        return False


def find_image(item):
    # RSS feeds may include the thumbnail in different optional fields.
    thumbnails = []
    for node in item.iter():
        tag = node.tag.rsplit('}', 1)[-1].lower()
        if tag in ('thumbnail', 'content', 'image', 'enclosure'):
            thumbnails.extend((node.attrib.get('url', ''), node.text or ''))
    descriptions = [
        item.findtext('description') or '',
        item.findtext('{http://purl.org/rss/1.0/modules/content/}encoded') or '',
    ]
    for description in descriptions:
        decoded = html.unescape(description)
        # Prefer actual image elements over arbitrary URLs in post text.
        for match in re.finditer(r'<img\b[^>]*>', decoded, re.IGNORECASE):
            tag = match.group(0)
            for key in ('data-lazy-src', 'data-src', 'src'):
                attribute = re.search(r'\b' + key + r'\s*=\s*[\"\']([^\"\']+)[\"\']', tag, re.IGNORECASE)
                if attribute:
                    thumbnails.append(attribute.group(1))
    for candidate in thumbnails:
        candidate = html.unescape(candidate.strip())
        if valid_image_url(candidate):
            return candidate
    return ''


def main():
    request = urllib.request.Request(RSS_URL, headers={'User-Agent': 'Mozilla/5.0 (compatible; NopigomRSS/1.0)', 'Accept': 'application/rss+xml, application/xml, text/xml'})
    with urllib.request.urlopen(request, timeout=25) as response:
        document = response.read(3_000_000)
    root = ET.fromstring(document)
    posts = []
    for item in root.findall('./channel/item'):
        title = (item.findtext('title') or '').strip()
        link = (item.findtext('link') or '').strip()
        if not title or not valid_url(link):
            continue
        date = ''
        pub = (item.findtext('pubDate') or '').strip()
        if pub:
            try:
                date = parsedate_to_datetime(pub).astimezone(timezone.utc).date().isoformat()
            except (TypeError, ValueError, OverflowError):
                pass
        posts.append({'title': title[:160], 'url': link, 'date': date, 'image': find_image(item)})
        if len(posts) >= 6:
            break
    if not posts:
        raise RuntimeError('RSS returned no public posts; existing posts.json left unchanged')
    result = {'posts': posts}
    output = json.dumps(result, ensure_ascii=False, indent=2) + '\n'
    DEST.write_text(output, encoding='utf-8')
    print(f'Updated {len(posts)} posts')

if __name__ == '__main__':
    main()
