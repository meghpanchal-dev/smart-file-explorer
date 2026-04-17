from flask import Flask, render_template_string, redirect, url_for, request
from collections import deque

app = Flask(__name__)

# ------- Data -------

tree = {
    "Root": {
        "Documents": {"Resume.docx": "file", "Notes.txt": "file"},
        "Pictures":  {"Vacation.jpg": "file", "Family.png": "file"},
        "Music":     {"Song1.mp3": "file",  "Song2.mp3": "file"}
    }
}

where = ["Root"]      # tracks which folder we're currently in
back  = []            # stack for back button
fwd   = []            # stack for forward button
clipboard = []        # files waiting to be pasted
recent = deque(maxlen=5)   # last 5 opened files


# ------- Helpers -------

def cur_folder():
    folder = tree
    for step in where:
        folder = folder[step]
    return folder

def cur_path():
    return " / ".join(where)

def find_files(folder, query, path=""):
    hits = []
    for name, val in folder.items():
        if query.lower() in name.lower():
            hits.append(path + "/" + name)
        if isinstance(val, dict):
            hits += find_files(val, query, path + "/" + name)
    return hits


# ------- Templates -------

BASE_STYLE = """
<style>
    body { font-family: Arial; margin: 30px; background: #f4f6f9; }
    h2 { color: #333; }
    .file, .folder { margin: 5px 0; }
    a { text-decoration: none; color: #007bff; }
    a:hover { text-decoration: underline; }
    a.danger { color: #dc3545; }
    a.rename { color: #fd7e14; }
    .nav { margin-top: 20px; }
    .btn { margin-right: 15px; }
    .container { background: #fff; padding: 20px; border-radius: 10px;
                 box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
    .search-bar { margin-bottom: 15px; }
    .search-bar input { padding: 6px 10px; border: 1px solid #ccc;
                        border-radius: 5px; width: 220px; }
    .search-bar button { padding: 6px 12px; background: #007bff;
                         color: #fff; border: none; border-radius: 5px;
                         cursor: pointer; }
    .search-bar button:hover { background: #0056b3; }
</style>
"""

MAIN_PAGE = BASE_STYLE + """
<div class="container">
  <h2>📁 Current Folder: {{ path }}</h2>

  <div class="search-bar">
    <form action="{{ url_for('search') }}" method="get">
      <input type="text" name="q" placeholder="Search files...">
      <button type="submit">🔍 Search</button>
    </form>
  </div>

  <hr>

  {% if folder %}
    <ul>
    {% for name, val in folder.items() %}
      {% if val == 'file' %}
        <li class="file">📄 {{ name }}
          &nbsp;<a href="{{ url_for('copy_file', name=name) }}">[Copy]</a>
          &nbsp;<a href="{{ url_for('open_file', name=name) }}">[Open]</a>
          &nbsp;<a class="rename" href="{{ url_for('rename_file', name=name) }}">[Rename]</a>
          &nbsp;<a class="danger" href="{{ url_for('delete_file', name=name) }}"
                  onclick="return confirm('Delete {{ name }}?')">[Delete]</a>
        </li>
      {% else %}
        <li class="folder">📂 <a href="{{ url_for('enter_folder', name=name) }}">{{ name }}</a></li>
      {% endif %}
    {% endfor %}
    </ul>
  {% else %}
    <p><i>Empty folder</i></p>
  {% endif %}

  <div class="nav">
    <a class="btn" href="{{ url_for('go_back') }}">⬅️ Back</a>
    <a class="btn" href="{{ url_for('go_fwd') }}">➡️ Forward</a>
    <a class="btn" href="{{ url_for('paste') }}">📋 Paste</a>
    <a class="btn" href="{{ url_for('show_recent') }}">🕘 Recent Files</a>
  </div>
</div>
"""


# ------- Routes -------

@app.route("/")
def index():
    return render_template_string(MAIN_PAGE, folder=cur_folder(), path=cur_path())


@app.route("/enter/<name>")
def enter_folder(name):
    folder = cur_folder()
    if name in folder and folder[name] != "file":
        back.append(list(where))
        where.append(name)
        fwd.clear()
    return redirect(url_for("index"))


@app.route("/back")
def go_back():
    if back:
        fwd.append(list(where))
        where[:] = back.pop()
    return redirect(url_for("index"))


@app.route("/fwd")
def go_fwd():
    if fwd:
        back.append(list(where))
        where[:] = fwd.pop()
    return redirect(url_for("index"))


@app.route("/open/<name>")
def open_file(name):
    recent.append(name)
    return render_template_string(BASE_STYLE + """
        <h2>📄 {{ name }}</h2>
        <p><a href="{{ url_for('index') }}">← Back</a></p>
    """, name=name)


@app.route("/copy/<name>")
def copy_file(name):
    folder = cur_folder()
    if name in folder and folder[name] == "file":
        clipboard.append(name)
    return redirect(url_for("index"))


@app.route("/paste")
def paste():
    folder = cur_folder()
    for f in clipboard:
        if "." in f:
            name, ext = f.rsplit(".", 1)
            folder[name + "_copy." + ext] = "file"
        else:
            folder[f + "_copy"] = "file"
    clipboard.clear()
    return redirect(url_for("index"))


@app.route("/delete/<name>")
def delete_file(name):
    folder = cur_folder()
    if name in folder and folder[name] == "file":
        del folder[name]
    return redirect(url_for("index"))


@app.route("/rename/<name>", methods=["GET", "POST"])
def rename_file(name):
    folder = cur_folder()
    if request.method == "POST":
        new = request.form.get("new_name", "").strip()
        if new and new not in folder and name in folder:
            folder[new] = folder.pop(name)
        return redirect(url_for("index"))

    return render_template_string(BASE_STYLE + """
        <h2>✏️ Rename: {{ name }}</h2>
        <form method="post">
          <input type="text" name="new_name" value="{{ name }}" required>
          <button type="submit">Rename</button>
        </form>
        <p><a href="{{ url_for('index') }}">Cancel</a></p>
    """, name=name)


@app.route("/recent")
def show_recent():
    return render_template_string(BASE_STYLE + """
        <h2>🕘 Recently Opened</h2>
        {% if files %}
          <ul>{% for f in files %}<li>📄 {{ f }}</li>{% endfor %}</ul>
        {% else %}
          <p>Nothing opened yet.</p>
        {% endif %}
        <p><a href="{{ url_for('index') }}">← Back</a></p>
    """, files=list(recent))


@app.route("/search")
def search():
    q = request.args.get("q", "")
    results = find_files(tree, q) if q else []
    return render_template_string(BASE_STYLE + """
        <h2>Search: "{{ q }}"</h2>
        {% if results %}
          <ul>{% for r in results %}<li>📄 {{ r }}</li>{% endfor %}</ul>
        {% else %}
          <p>No matches found.</p>
        {% endif %}
        <p><a href="{{ url_for('index') }}">← Back</a></p>
    """, q=q, results=results)


if __name__ == "__main__":
    app.run(debug=True)
