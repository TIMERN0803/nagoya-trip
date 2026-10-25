from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
class H(SimpleHTTPRequestHandler):
 def __init__(self,*a,**kw):super().__init__(*a,directory=str(ROOT/'app-source'),**kw)
 def end_headers(self):
  self.send_header('Content-Security-Policy',"default-src 'self' data: blob:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; connect-src 'self'; img-src 'self' data: blob:; font-src 'self' data:")
  super().end_headers()
 def do_GET(self):
  if self.path.split('?')[0] in ('/','/index.html'):
   s=(ROOT/'app-source'/'index.html').read_text(encoding='utf8').replace('https://www.gstatic.com/firebasejs/','http://localhost:8767/mock/firebasejs/')
   body=s.encode();self.send_response(200);self.send_header('Content-Type','text/html; charset=utf-8');self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body);return
  if self.path.startswith('/mock/firebasejs/'):
   n='fs.js' if self.path.endswith('firebase-firestore.js') else 'app.js';body=(ROOT/'test-tools'/'ft'/n).read_bytes();self.send_response(200);self.send_header('Content-Type','text/javascript');self.end_headers();self.wfile.write(body);return
  return super().do_GET()
ThreadingHTTPServer(('127.0.0.1',8767),H).serve_forever()
