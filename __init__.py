import threading
import logging
from flask import Flask, request, jsonify
from aqt import mw
from aqt.qt import QAction
from aqt.utils import showInfo
from flask_cors import CORS  # Import CORS

# Disable colorama logging for Werkzeug
logging.getLogger('werkzeug').disabled = True

app = Flask(__name__)
CORS(app, resources={r"/add_card": {"origins": ["https://www.netflix.com", "https://www.youtube.com"]}})

@app.route('/add_card', methods=['POST'])
def add_card():
    
    data = request.json
    if 'front' not in data or 'back' not in data or 'deck' not in data:
        return jsonify({'error': 'Invalid data'}), 400

    deck_name = data['deck']
    deck_id = mw.col.decks.id(deck_name)
    mw.col.decks.select(deck_id)
    
    note = mw.col.newNote()
    note["Front"] = data['front']
    note["Back"] = data['back']
    note.model()['did'] = deck_id  # Set the deck ID for the note
    
    mw.col.addNote(note)
    return jsonify({'status': 'Card added', 'deck': data['deck']}), 200
    

def run_server():
    try:
        app.run(port=5123, use_reloader=False, debug=True)
    except Exception:
        print("Exiting...")
        exit()

def start_server():
    server_thread = threading.Thread(target=run_server)
    server_thread.setDaemon(True)
    server_thread.start()

def show_message():
    showInfo("Local server is running at http://localhost:5123")

# Start the server when Anki starts
start_server()

# Add a menu item to display server status
action = QAction("Show Server Status", mw)
action.triggered.connect(show_message)
mw.form.menuTools.addAction(action)
