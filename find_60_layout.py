import urllib.request
import re

url = 'https://raw.githubusercontent.com/aryanrangra100/mk1300v2/main/_next/static/chunks/app/page-40907b002770d88c.js'
content = urllib.request.urlopen(url).read().decode('utf-8', errors='ignore')

# Look for 61 keys (standard 60% count)
# Or where the keyboard UI keys are defined
matches = re.findall(r'\[(?:\s*\{[^{}]+?\},?\s*){55,70}\]', content)
print(f"Candidate layout arrays (55-70 keys): {len(matches)}")
for idx, m in enumerate(matches):
    print(f"--- Array {idx} (len {len(m)}) ---")
    print(m[:400])

