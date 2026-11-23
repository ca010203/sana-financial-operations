"""Build the static, password-protected copy of the Sana Financial Operations dashboard.

    SFO_PASSWORD=... python3 tools/build.py

Reads src/index.html (the same page the Claude Data artifact runs), the CSV snapshots in
data/, the runtime stand-in tools/shim.js and d3, and writes:
  data/bundle.enc    the CSV snapshots, encrypted (the CSVs themselves are not committed)
  dist/preview.html  unencrypted, for local checks only (git-ignored)
  docs/index.html    AES-256-GCM encrypted page served by GitHub Pages
"""
import base64, csv, json, os, re, sys, pathlib, datetime
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes

ROOT = pathlib.Path(__file__).resolve().parent.parent
ITER = 250_000
# dataset id in the page -> snapshot file. labour and restmix are calcs in the artifact
# (from Push hours and POS departments); here they are pre-aggregated files.
FILES = {
    'trybe_monthly': 'trybe_monthly.csv', 'founding': 'founding.csv', 'pos_monthly': 'pos_monthly.csv',
    'labour': 'labour.csv', 'restmix': 'restmix.csv', 'ledger': 'ledger.csv',
    'costcalc': 'costcalc.csv', 'seasonal': 'seasonal.csv', 'salaries': 'salaries.csv',
}

TOKENS = """
:root{--font-anthropic-sans:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif;--font-anthropic-serif:Georgia,"Times New Roman",serif;
--color-fg:#2b2b2b;--color-fg-muted:#6f6f6f;--color-bg:#fafaf9;--color-panel:#f1f1ef;--color-border-line:#dedddb;--color-ok:#3f7d4e;--color-warn:#a8741a;--color-bad:#b0453a;
--cds-font-size-caption:12.5px;--cds-font-size-body:15px;--cds-font-size-heading:18px;--cds-font-size-title:30px;--cds-font-weight-medium:600;
--cds-gap-xs:4px;--cds-gap-sm:8px;--cds-gap-md:12px;--cds-gap-lg:20px;--cds-gap-xl:32px;--cds-pad-sm:8px;--cds-pad-md:14px;--cds-pad-lg:18px;--cds-radius:10px;
--cds-chart-grid:#e9e8e5;--cds-chart-axis:#c9c8c4;--cds-chart-muted:#9a9995;--cds-chart-reference:#8a8984;--cds-chart-status-good:#4f8a5e;--cds-chart-status-critical:#c0574b;
--cds-text-primary:#2b2b2b;--cds-text-secondary:#6f6f6f;--cds-surface-popover:#fff;--cds-border:#dedddb;--cds-shadow-popover:0 4px 14px rgba(0,0,0,.08);
--sfo-c0:#5f7f99;--sfo-c1:#c28a5c;--sfo-c2:#7c9a6d;--sfo-c3:#977190;--sfo-c4:#9a9995}
@media (prefers-color-scheme:dark){:root{--color-fg:#e6e5e2;--color-fg-muted:#a3a29e;--color-bg:#1d1d1c;--color-panel:#262625;--color-border-line:#3a3a38;--cds-chart-grid:#2f2f2d;--cds-chart-axis:#4a4a47;
--cds-text-primary:#e6e5e2;--cds-text-secondary:#a3a29e;--cds-surface-popover:#2b2b2a;--cds-border:#3a3a38;--color-ok:#79b487;--color-bad:#e0857a}}
html,body{margin:0;background:var(--color-bg);color:var(--color-fg)}#dash-root{padding:20px 18px 40px}
.dash-select{font:inherit;font-size:13px;padding:4px 8px;border:1px solid var(--color-border-line);border-radius:6px;background-color:var(--color-bg);color:var(--color-fg)}
"""


def rows(path):
    with open(path, newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def wrap_scripts(page):
    # Each script runs in its own scope in the dashboard runtime; mirror that here.
    return re.sub(r'<script>(.*?)</script>', lambda m: '<script>(function(){' + m.group(1) + '\n})();</script>', page, flags=re.S)


def load_data(pw):
    # Plain CSVs in data/ are git-ignored (the repo is public for Pages). The committed copy is
    # data/bundle.enc, encrypted with the same password; it is rebuilt whenever the CSVs exist.
    if all((ROOT / 'data' / v).exists() for v in FILES.values()):
        data = {k: rows(ROOT / 'data' / v) for k, v in FILES.items()}
        if pw:
            (ROOT / 'data' / 'bundle.enc').write_text(json.dumps(encrypt(json.dumps(data), pw)))
        return data
    if not pw:
        sys.exit('No CSVs in data/ and no SFO_PASSWORD to open data/bundle.enc')
    return json.loads(decrypt(json.loads((ROOT / 'data' / 'bundle.enc').read_text()), pw))


def decrypt(blob, password):
    d = base64.b64decode
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=d(blob['s']), iterations=blob['n']).derive(password.encode())
    return AESGCM(key).decrypt(d(blob['i']), d(blob['c']), None).decode('utf-8')


def inner_html(data):
    page = (ROOT / 'src' / 'index.html').read_text(encoding='utf-8')
    page = page.replace('<meta name="dash-one-writer">', '')
    d3 = (ROOT / 'node_modules' / 'd3' / 'dist' / 'd3.min.js').read_text(encoding='utf-8')
    shim = (ROOT / 'tools' / 'shim.js').read_text(encoding='utf-8')
    built = datetime.datetime.now(datetime.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    payload = json.dumps(data, separators=(',', ':')).replace('</', '<\\/')
    return ('<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            '<meta name="robots" content="noindex"><title>Sana Financial Operations</title><style>' + TOKENS + '</style>'
            '<script>' + d3 + '</script><script>window.__SFO_DATA=' + payload + ';window.__SFO_BUILT=' + json.dumps(built) + ';</script>'
            '<script>' + shim + '</script></head><body><div id="dash-root">' + wrap_scripts(page) + '</div></body></html>')


def encrypt(html, password):
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ITER).derive(password.encode())
    ct = AESGCM(key).encrypt(iv, html.encode('utf-8'), None)
    b = lambda x: base64.b64encode(x).decode()
    return {'s': b(salt), 'i': b(iv), 'c': b(ct), 'n': ITER}


GATE = """<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>Sana Financial Operations</title><style>
body{margin:0;min-height:100vh;display:flex;align-items:center;justify-content:center;background:#fafaf9;color:#2b2b2b;font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Inter,Helvetica,Arial,sans-serif}
form{width:min(340px,88vw);padding:28px;border:1px solid #dedddb;border-radius:12px;background:#fff}
h1{font-family:Georgia,serif;font-weight:400;font-size:24px;margin:0 0 6px}p{color:#6f6f6f;font-size:13px;margin:0 0 18px}
input{width:100%;box-sizing:border-box;padding:10px 12px;border:1px solid #cfcecb;border-radius:8px;font-size:15px;margin-bottom:12px}
button{width:100%;padding:10px;border:0;border-radius:8px;background:#4a4a48;color:#fff;font-size:14px;cursor:pointer}
#e{color:#b0453a;font-size:13px;min-height:18px;margin-top:10px}
</style></head><body><form id="f" autocomplete="off"><h1>Sana Financial Operations</h1><p>Private. Enter the password to open.</p>
<input id="p" type="password" placeholder="Password" aria-label="Password" autofocus><button type="submit">Open</button><div id="e" role="alert"></div></form>
<script>
const P=__PAYLOAD__;
const u=s=>Uint8Array.from(atob(s),c=>c.charCodeAt(0));
async function open_(pw){const k0=await crypto.subtle.importKey('raw',new TextEncoder().encode(pw),'PBKDF2',false,['deriveKey']);
 const k=await crypto.subtle.deriveKey({name:'PBKDF2',salt:u(P.s),iterations:P.n,hash:'SHA-256'},k0,{name:'AES-GCM',length:256},false,['decrypt']);
 const pt=await crypto.subtle.decrypt({name:'AES-GCM',iv:u(P.i)},k,u(P.c));return new TextDecoder().decode(pt);}
async function go(pw,remember){try{const h=await open_(pw);if(remember){try{sessionStorage.setItem('sfo_pw',pw);}catch(e){}}document.open();document.write(h);document.close();}
 catch(e){try{sessionStorage.removeItem('sfo_pw');}catch(x){}document.getElementById('e').textContent='That password did not work.';}}
document.getElementById('f').addEventListener('submit',ev=>{ev.preventDefault();document.getElementById('e').textContent='Opening…';go(document.getElementById('p').value,true);});
try{const s=sessionStorage.getItem('sfo_pw');if(s)go(s,false);}catch(e){}
</script></body></html>"""


def main():
    pw = os.environ.get('SFO_PASSWORD')
    html = inner_html(load_data(pw))
    (ROOT / 'dist').mkdir(exist_ok=True)
    (ROOT / 'dist' / 'preview.html').write_text(html, encoding='utf-8')
    if not pw:
        print('SFO_PASSWORD not set: wrote dist/preview.html only'); return
    (ROOT / 'docs').mkdir(exist_ok=True)
    (ROOT / 'docs' / 'index.html').write_text(GATE.replace('__PAYLOAD__', json.dumps(encrypt(html, pw))), encoding='utf-8')
    (ROOT / 'docs' / '.nojekyll').write_text('')
    print('wrote docs/index.html', len(html), 'bytes before encryption')


if __name__ == '__main__':
    main()
