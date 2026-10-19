import hashlib, html, re, unicodedata
from urllib.parse import urlparse, urlunparse, parse_qsl, urlencode
from rapidfuzz.fuzz import ratio

def plain(value):
    return re.sub(r'\s+', ' ', re.sub(r'<[^>]*>', ' ', html.unescape(str(value or '')))).strip()
def normalize(value):
    return re.sub(r'[^\w\s]', ' ', unicodedata.normalize('NFKC', plain(value)).casefold()).strip()
def safe_url(url):
    try:
        p=urlparse(url)
        return p.scheme in ('https','http') and bool(p.hostname) and not p.username and not p.password
    except ValueError: return False
def canonical_url(url):
    p=urlparse(url)
    q=[(k,v) for k,v in parse_qsl(p.query) if not k.lower().startswith(('utm_', 'fbclid', 'gclid'))]
    return urlunparse((p.scheme,p.netloc.lower(),p.path.rstrip('/'),'',urlencode(q),''))
def fingerprint(text): return hashlib.sha256(text.encode()).hexdigest()[:20]
def deduplicate(articles):
    output=[]; urls=set(); titles=set()
    for a in sorted(articles,key=lambda x:x['published_at'],reverse=True):
        url=canonical_url(a['url']); title=normalize(a['title'])
        if url in urls or title in titles: continue
        if any(a['publisher_id']==b['publisher_id'] and ratio(title,normalize(b['title']))>94 for b in output): continue
        urls.add(url); titles.add(title); output.append(a)
    return output
