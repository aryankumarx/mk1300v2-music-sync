import urllib.request
import re

url = 'https://raw.githubusercontent.com/aryanrangra100/mk1300v2/main/_next/static/chunks/app/page-40907b002770d88c.js'
content = urllib.request.urlopen(url).read().decode('utf-8', errors='ignore')

# Find variables or arrays holding the layout for 60% or MK1300
# Look for 61 keys or index mappings
for match in re.finditer(r'\[(?:\s*\{"name":"[^"]+","code":"KC_[^"]+",[^}]+\},?\s*){20,}\]', content):
    arr_str = match.group(0)
    names = re.findall(r'"name":"([^"]+)"', arr_str)
    print(f"Found layout array with {len(names)} keys:")
    print(" ", names[:25])
    print(" ", names[25:50])
    print(" ", names[50:])
    print("-" * 50)

