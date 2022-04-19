import http.server
import json
import random
import socketserver
import string
import sys
from http import HTTPStatus
from urllib.parse import parse_qs, urlparse

PORT = int(sys.argv[1])

out = []


def random_str(id, size) -> str:
    random.seed(id[0])
    return ''.join(random.choices(string.digits+string.ascii_letters, k=int(size[0])))


class GETHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        self.send_response(HTTPStatus.OK)
        self.end_headers()
        self.wfile.write(
            random_str(**parse_qs(urlparse(self.path).query))
            .encode('utf-8'))

    def log_message(self, format: str, *args) -> None:
        out.append("%s - - [%s] %s" %
                   (self.address_string(),
                    self.log_date_time_string(),
                    format % args))


Handler = GETHandler

with socketserver.TCPServer(("", PORT), Handler) as httpd:
    print("Serving at port", PORT)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(json.dumps(out, indent=4))
