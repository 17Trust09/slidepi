from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory, send_file, jsonify
import os
import json
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'raspberry'  # Passwort für Login

UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Hilfsfunktionen
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_json(filename, default):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return default
    return default

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f, indent=4)

def write_status(status, current_media, time_left):
    with open("state.json", "w") as f:
        json.dump({
            "status": status,
            "current_media": current_media,
            "time_left": time_left
        }, f)

@app.route('/media/<filename>')
def media(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == 'admin':
            session['logged_in'] = True
            return redirect(url_for('index'))
        else:
            return render_template('login.html', error='Falsches Passwort!')
    return render_template('login.html')

@app.route('/toggle_playlist', methods=['POST'])
def toggle_playlist():
    filename = request.form['filename']
    tab = request.args.get('tab') or 'medien'

    # Lade aktuelle Playlist
    playlist = load_json('playlist.json', [])
    playlist_filenames = [item['filename'] for item in playlist]

    if filename in playlist_filenames:
        playlist = [item for item in playlist if item['filename'] != filename]
    else:
        playlist.append({'filename': filename, 'duration': 10})  # Standarddauer 10 Sekunden

    save_json('playlist.json', playlist)

    return redirect(url_for('index', tab=tab))

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

@app.route('/', methods=['GET'])
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    tab = request.args.get('tab', 'info')

    uploaded_files = os.listdir(UPLOAD_FOLDER)
    media_files = [
        {
            "filename": f,
            "path": url_for('media', filename=f)
        }
        for f in uploaded_files
        if allowed_file(f)
    ]

    playlist = load_json('playlist.json', [])
    durations = load_json('durations.json', {})

    playlist_filenames = [item["filename"] for item in playlist]

    presentation_files = [
        {
            "filename": item["filename"],
            "duration": durations.get(item["filename"], 10),
            "path": url_for('media', filename=item["filename"])
        }
        for item in playlist
        if any(item["filename"] == f["filename"] for f in media_files)
    ]

    return render_template('dashboard.html',
                           tab=tab,
                           media_files=media_files,
                           playlist=presentation_files,
                           playlist_filenames=playlist_filenames)

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(url_for('index', tab='medien'))

    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index', tab='medien'))

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        save_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(save_path)

    return redirect(url_for('index', tab='medien'))

@app.route('/delete', methods=['POST'])
def delete_file():
    filename = request.form.get('filename')
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

    if os.path.exists(file_path):
        os.remove(file_path)

    # Playlist aktualisieren
    playlist = load_json('playlist.json', [])
    playlist = [item for item in playlist if item["filename"] != filename]
    save_json('playlist.json', playlist)

    return redirect(url_for('index', tab='medien'))

@app.route('/save_playlist', methods=['POST'])
def save_playlist():
    filenames = request.form.getlist('playlist[]')
    durations = load_json('durations.json', {})
    playlist = [{"filename": f, "duration": durations.get(f, 10)} for f in filenames]
    save_json('playlist.json', playlist)
    return '', 204

@app.route('/save_durations', methods=['POST'])
def save_durations():
    data = request.json
    save_json('durations.json', data)
    return '', 204

@app.route('/playlist.json')
def serve_playlist():
    return send_file('playlist.json', mimetype='application/json')

@app.route('/durations.json')
def serve_durations():
    return send_file('durations.json', mimetype='application/json')

@app.route('/play')
def play():
    playlist = load_json('playlist.json', [])
    durations = load_json('durations.json', {})

    media_files = [
        {
            "filename": item["filename"],
            "duration": durations.get(item["filename"], 10),
            "path": url_for('media', filename=item["filename"])
        }
        for item in playlist
    ]

    return render_template('play.html', media_files=media_files)

@app.route('/status')
def get_status():
    try:
        with open("state.json", "r") as f:
            return jsonify(json.load(f))
    except:
        return jsonify({"status": "Unbekannt", "current_media": "-", "time_left": "-"})

@app.route('/update_status', methods=['POST'])
def update_status():
    try:
        data = request.json
        save_json("state.json", data)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/save_state', methods=['POST'])
def save_state():
    data = request.json
    save_json('state.json', data)
    return '', 204


if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(debug=False, host='0.0.0.0', port=5000)
