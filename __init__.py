import threading
import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from aqt import mw

class AddCardRequestHandler(BaseHTTPRequestHandler):
    ROUTES = {
        "/add_card": "handle_add_card",
        "/get_known_core_words": "handle_get_known_core_words",
    }

    def log_message(self, format, *args):
        return

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        handler_name = self.ROUTES.get(self.path)
        if not handler_name:
            self.send_response(404)
            self._send_cors_headers()
            self.end_headers()
            return

        handler = getattr(self, handler_name)
        try:
            handler()
        except Exception as e:
            self.send_response(500)
            self._send_cors_headers()
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
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid data"}).encode())
                return

            try:
                did = mw.col.decks.id(deck_name)
            except Exception:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Error selecting the deck"}).encode())
                return

            note = mw.col.newNote()
            note.model()['did'] = did
            note['Front'] = front
            note['Back'] = back
            mw.col.add_note(note, did)

            self.send_response(200)
            self._send_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Card added successfully')

        except Exception as e:
            self.send_response(500)
            self._send_cors_headers()
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            error_msg = f'Error: {e}'.encode('utf-8')
            self.wfile.write(error_msg)

    def handle_get_known_core_words(self):
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8')
        try:
            data = json.loads(body)
            deck_name = data.get('deck', '')
            word_field = data.get('wordField', '')
    
            if not deck_name or not word_field:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Invalid data"}).encode("utf-8"))
                return
    
            try:
                did = mw.col.decks.id(deck_name)
                mw.col.decks.select(did)
            except Exception:
                self.send_response(400)
                self._send_cors_headers()
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": "Error selecting the deck"}).encode("utf-8"))
                return
    
            note_ids = mw.col.findNotes(f'deck:"{deck_name}" -is:new')
            words = []
            for nid in note_ids:
                note = mw.col.getNote(nid)
                if word_field in note:
                    words.append(note[word_field])
    
            self.send_response(200)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"words": words}).encode("utf-8"))

        except Exception as e:
            self.send_response(500)
            self._send_cors_headers()
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))


def start_server():
    server = HTTPServer(('localhost', 5123), AddCardRequestHandler)
    server.serve_forever()

threading.Thread(target=start_server, daemon=True).start()
