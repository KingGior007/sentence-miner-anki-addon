import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from aqt import mw

class AddCardRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        return

    def do_POST(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        try:
            data = json.loads(body)
            front = data.get('front', '')
            back = data.get('back', '')
            deck_name = data.get('deck', '')

            # Determine deck ID; fallback to current deck if not provided or invalid
            try:
                did = mw.col.decks.id(deck_name) if deck_name else mw.col.decks.current()['id']
            except Exception:
                did = mw.col.decks.current()['id']

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
