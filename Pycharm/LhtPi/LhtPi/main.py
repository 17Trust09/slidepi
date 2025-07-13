from flask import Flask, request, redirect, url_for, send_from_directory, render_template, session
import os
import subprocess
import json

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4'}
PLAYLIST_FILE = 'playlist.json'
DURATION_FILE = 'durations.json'
ADMIN_PASSWORD = 'admin'  # Dein Passwort

app = Flask(__name__)
app.secret_key = 'dein_geheimer_schluessel'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Hilfsfunktionen
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def load_json(filename):
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            return json.load(f)
    return {}

def save_json(filename, data):
    with open(filename, 'w') as f:
        json.dump(data, f)

def get_media_files():
    return sorted([f for f in os.listdir(UPLOAD_FOLDER) if allowed_file(f)])

# Routen
@app.route('/')
def index():
    active_tab = request.args.get('tab', 'info')
    return render_template('dashboard.html',
                           media_files=get_media_files(),
                           playlist=load_json(PLAYLIST_FILE),
                           durations=load_json(DURATION_FILE),
                           active_tab=active_tab,
                           admin_logged_in=session.get('admin_logged_in', False))

@app.route('/login', methods=['GET', 'POST'])
def login():
    message = ''
    if request.method == 'POST':
        if request.form.get('password') == ADMIN_PASSWORD:
            session['admin_logged_in'] = True
            return redirect(url_for('index', tab='system'))
        else:
            message = 'Falsches Passwort!'
    return render_template('login.html', message=message)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file and allowed_file(file.filename):
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], file.filename))
    return redirect(url_for('index', tab='medien'))

@app.route('/delete', methods=['POST'])
def delete_file():
    filename = request.form.get('filename')
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    return redirect(url_for('index', tab='medien'))

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/update_playlist', methods=['POST'])
def update_playlist():
    playlist = request.form.getlist('playlist_files')
    save_json(PLAYLIST_FILE, playlist)
    return redirect(url_for('index', tab='praesentation'))

@app.route('/save_durations', methods=['POST'])
def save_durations():
    durations = {}
    for key, value in request.form.items():
        if key.startswith('duration_'):
            filename = key.replace('duration_', '')
            try:
                durations[filename] = int(value)
            except ValueError:
                durations[filename] = 10
    save_json(DURATION_FILE, durations)
    return redirect(url_for('index', tab='praesentation'))

@app.route('/ota_update', methods=['POST'])
def ota_update():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    result = subprocess.run(['git', 'pull'], capture_output=True, text=True)
    return f"<pre>{result.stdout or result.stderr}</pre><a href='/'>Zurück</a>"

@app.route('/restart', methods=['POST'])
def restart():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    subprocess.Popen(['sudo', 'reboot'])
    return 'System wird neu gestartet...'

@app.route('/disk_space')
def disk_space():
    if not session.get('admin_logged_in'):
        return redirect(url_for('login'))
    output = subprocess.check_output(['df', '-h']).decode()
    return f"<pre>{output}</pre><a href='/'>Zurück</a>"

if __name__ == '__main__':
    os.makedirs(UPLOAD_FOLDER, exist_ok=True)
    app.run(host='0.0.0.0', port=80)
