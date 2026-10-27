# 測試用網站伺服器（8768 埠）：可以模擬訊號差
# - /__slow?on=1：之後所有回應都晚 4 秒（模擬手機訊號差），/__slow?on=0 恢復
# - 網址帶 ?split：首頁先送到開啟畫面為止，停 0.9 秒再送剩下的（模擬下載很慢，看得到開啟畫面）
import http.server, os, sys, time, threading
ROOT = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/nagoya-trip"
SLOW = {"on": False}
class H(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *a, **k): super().__init__(*a, directory=ROOT, **k)
    def log_message(self, *a): pass
    def do_GET(self):
        if self.path.startswith("/__slow"):
            SLOW["on"] = "on=1" in self.path; self.send_response(204); self.end_headers(); return
        if SLOW["on"]: time.sleep(4)
        if "split" in self.path and self.path.split("?")[0] in ("/", "/index.html"):
            body = open(os.path.join(ROOT, "index.html"), "rb").read(); i = body.index(b"<script>", body.index(b'id="splash"') + 3000)
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8"); self.send_header("Content-Length", str(len(body))); self.end_headers()
            self.wfile.write(body[:i]); self.wfile.flush(); time.sleep(0.9); self.wfile.write(body[i:]); return
        return super().do_GET()
class S(http.server.ThreadingHTTPServer): daemon_threads = True
S(("", 8768), H).serve_forever()
