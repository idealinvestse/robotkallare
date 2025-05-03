
from flask import Flask, send_from_directory, render_template_string
import os

app = Flask(__name__)

# Directory to serve files from
FILES_DIR = '.'

@app.route('/')
def index():
    files = os.listdir(FILES_DIR)
    # Generate simple HTML to list files with links
    html = '<h1>Files</h1><ul>'
    for file in files:
        if os.path.isfile(os.path.join(FILES_DIR, file)):
            html += f'<li><a href="/files/{file}">{file}</a></li>'
    html += '</ul>'
    return render_template_string(html)

@app.route('/files/<path:filename>')
def serve_file(filename):
    return send_from_directory(FILES_DIR, filename)

if __name__ == '__main__':
    app.run(debug=True, use_reloader=False)
