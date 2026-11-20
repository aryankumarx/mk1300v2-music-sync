import urllib.request
import re

url = 'https://antesports.com/pages/download'
req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
try:
    with urllib.request.urlopen(req, timeout=10) as resp:
        html = resp.read().decode('utf-8', errors='ignore')
        for match in re.finditer(r'<a[^>]+href=[\"\']([^\"\']+)[\"\'][^>]*>(.*?)</a>', html, re.I | re.S):
            href, text = match.group(1), match.group(2)
            if '1300' in href.lower() or '1300' in text.lower():
                print(f"Match: {text.strip()} -> {href}")
except Exception as e:
    print('Error:', e)

