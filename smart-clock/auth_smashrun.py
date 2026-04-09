#!/usr/bin/env python3
"""
One-time OAuth2 authorization for SmashRun.
Uses the implicit flow with the built-in 'client' client_id.
Run this to get a fresh access token, then paste it into .env.
"""

import threading
import webbrowser
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

AUTH_URL = "https://secure.smashrun.com/oauth2/authenticate"
REDIRECT_URI = "http://localhost:8080"

_token = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _token
        # Implicit flow returns token as a URL fragment (#access_token=...)
        # Fragments aren't sent to the server, so we serve a page that
        # extracts it with JS and sends it back as a query param.
        if "access_token" in self.path:
            # Second request with token in query string
            query = parse_qs(urlparse(self.path).query)
            _token = query.get("access_token", [None])[0]
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(
                b"<html><body><h2>Authorization successful!</h2>"
                b"<p>You can close this tab. Check your terminal for the token.</p>"
                b"</body></html>"
            )
        else:
            # First request — serve JS that extracts the fragment
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(b"""<html><body>
<script>
var hash = window.location.hash.substring(1);
var params = new URLSearchParams(hash);
var token = params.get('access_token');
if (token) {
    window.location = '/callback?access_token=' + token;
} else {
    document.body.innerHTML = '<h2>No token received. Try again.</h2>';
}
</script>
<p>Processing authorization...</p>
</body></html>""")

    def log_message(self, format, *args):
        pass


def main():
    HTTPServer.allow_reuse_address = True
    server = HTTPServer(("localhost", 8080), CallbackHandler)

    def serve_until_token():
        while _token is None:
            server.handle_request()

    server_thread = threading.Thread(target=serve_until_token)
    server_thread.daemon = True
    server_thread.start()

    auth_url = (
        f"{AUTH_URL}?response_type=token"
        f"&client_id=client"
        f"&redirect_uri={REDIRECT_URI}"
    )

    print("Opening browser for SmashRun sign-in...")
    webbrowser.open(auth_url)
    print("Waiting for authorization...")

    server_thread.join(timeout=120)
    server.server_close()

    if not _token:
        print("Error: No token received. Try again.")
        return

    print(f"\nYour fresh access token:\n{_token}")
    print(f"\nUpdate your .env file with:")
    print(f"SMASHRUN_TOKEN={_token}")

    # Auto-update .env
    try:
        env_lines = []
        found = False
        try:
            with open(".env") as f:
                env_lines = f.readlines()
        except FileNotFoundError:
            pass

        with open(".env", "w") as f:
            for line in env_lines:
                if line.startswith("SMASHRUN_TOKEN="):
                    f.write(f"SMASHRUN_TOKEN={_token}\n")
                    found = True
                else:
                    f.write(line)
            if not found:
                f.write(f"SMASHRUN_TOKEN={_token}\n")

        print("\n.env file updated automatically!")
    except Exception as e:
        print(f"\nCouldn't auto-update .env: {e}")
        print("Please update it manually.")


if __name__ == "__main__":
    main()
