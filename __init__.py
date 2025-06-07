import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from aqt import mw

class AddCardRequestHandler(BaseHTTPRequestHandler):
    ROUTES = {
        "/add_card": "handle_add_card",
    }


    def log_message(self, format, *args):
        return

    def do_POST(self):
        handler_name = self.ROUTES.get(self.path)
        if not handler_name:
            self.send_response(404)
            self.end_headers()
            return

        handler = getattr(self, handler_name)
        try:
            handler()
        except Exception as e:
            # catch any unexpected errors
            self.send_response(500)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode())


    def handle_add_card(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        try:
            data = json.loads(body)
            front = data.get('front', '')
            back = data.get('back', '')
            deck_name = data.get('deck', '')
            if not all(k in data for k in ("front", "back", "deck")):
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid data"}).encode())
                return

            # Determine deck ID; fallback to current deck if not provided or invalid
            try:
                did = mw.col.decks.id(deck_name)
            except Exception:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Error selecting the deck"}).encode())
                return

            # Create and populate note
            note = mw.col.newNote()
            note.model()['did'] = did
            note['Front'] = front
            note['Back'] = back

            # Add note to specified deck
            mw.col.add_note(note, did)

            self.send_response(200)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Card added successfully')
        except Exception as e:
            self.send_response(500)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            error_msg = f'Error: {e}'.encode('utf-8')
            self.wfile.write(error_msg)


def start_server():
    server = HTTPServer(('localhost', 5123), AddCardRequestHandler)
    server.serve_forever()

# Launch server in a background thread when Anki starts
threading.Thread(target=start_server, daemon=True).start()
