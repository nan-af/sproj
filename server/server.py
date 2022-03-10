import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from http import HTTPStatus

PORT = 8000


class GETHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(
            f'GET request! {parse_qs(urlparse(self.path).query)}'.encode('utf-8'))


Handler = GETHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()
