import urllib.request
import re
import json

url = 'https://raw.githubusercontent.com/aryanrangra100/mk1300v2/main/_next/static/chunks/app/page-40907b002770d88c.js'
content = urllib.request.urlopen(url).read().decode('utf-8', errors='ignore')

# Find the full default layout array
# Look for objects with KC_
pattern = r'\{"name":"([^"]+)","code":"(KC_[^"]+)","type":(\d+),"value1":(\d+),"value2":(\d+),"value3":(\d+)\}'
matches = re.findall(pattern, content)

print(f"Total key matches: {len(matches)}")
# Let's see the sequence of keys
seen_seq = []
for m in matches:
    seen_seq.append(m)

# Find unique blocks or the layout array
print("First 35 keys:")
for i, k in enumerate(seen_seq[:35]):
    print(f"  [{i:2d}] {k[0]:15s} code={k[1]:15s} type={k[2]} v1={k[3]} v2={k[4]} v3={k[5]}")

