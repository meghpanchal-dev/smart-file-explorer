from flask import Flask, render_template_string, redirect, url_for

app = Flask(__name__)

# ----- Folder Tree -----
folder_tree = {
    "Root": {
        "Documents": {"Resume.docx": "file", "Notes.txt": "file"},
        "Pictures": {"Vacation.jpg": "file", "Family.png": "file"},
        "Music": {"Song1.mp3": "file", "Song2.mp3": "file"}
    }
}


back_stack = []  
forward_stack = []
current_path = ["Root"]

file_queue = []      

class Node:
    def __init__(self, filename):
        self.filename = filename
        self.next = None


class RecentFilesLinkedList:
    def __init__(self, limit=5):
        self.head = None
        self.tail = None
        self.size = 0
        self.limit = limit

    def add_file(self, filename):
        """Insert a new file at the end of the linked list."""
        new_node = Node(filename)

        if self.head is None:
            self.head = self.tail = new_node
        else:
            self.tail.next = new_node
            self.tail = new_node

        self.size += 1

        if self.size > self.limit:
            self.remove_oldest()

    def remove_oldest(self):
        """Remove the first (oldest) file from the list."""
        if self.head:
            self.head = self.head.next
            self.size -= 1

    def get_all_files(self):
        """Return all filenames in the list as a Python list."""
        files = []
        current = self.head
        while current:
            files.append(current.filename)
            current = current.next
        return files


recent_files = RecentFilesLinkedList()


def get_current_folder():
    folder = folder_tree
    for p in current_path:
        folder = folder[p]
    return folder


def get_path_display():
    return " / ".join(current_path)


# ----- Flask Routes -----
@app.route("/")
def index():
    folder = get_current_folder()
    return render_template_string("""
    <html>
    <head>
        <title>Smart File Explorer</title>
        <style>
            body { font-family: Arial; margin: 30px; background: #f4f6f9; }
            h2 { color: #333; }
            .file, .folder { margin: 5px 0; }
            a { text-decoration: none; color: #007bff; }
            a:hover { text-decoration: underline; }
            .nav { margin-top: 20px; }
            .btn { margin-right: 15px; }
            .container { background: #fff; padding: 20px; border-radius: 10px;
                         box-shadow: 0 2px 6px rgba(0,0,0,0.1); }
        </style>
    </head>
    <body>
        <div class="container">
        <h2>📁 Current Folder: {{ path }}</h2>
        <hr>

        {% if folder %}
            <ul>
            {% for name, value in folder.items() %}
                {% if value == 'file' %}
                    <li class="file">📄 {{ name }}
                        <a href="{{ url_for('copy_file', name=name) }}">[Copy]</a>
                        <a href="{{ url_for('open_file', name=name) }}">[Open]</a>
                    </li>
                {% else %}
                    <li class="folder">📂 <a href="{{ url_for('open_item', name=name) }}">{{ name }}</a></li>
                {% endif %}
            {% endfor %}
            </ul>
        {% else %}
            <p><i>Empty folder</i></p>
        {% endif %}

        <div class="nav">
            <a class="btn" href="{{ url_for('go_back') }}">⬅️ Back</a>
            <a class="btn" href="{{ url_for('go_forward') }}">➡️ Forward</a>
            <a class="btn" href="{{ url_for('paste_files') }}">📋 Paste</a>
            <a class="btn" href="{{ url_for('show_recent_files') }}">🕘 Recent Files</a>
        </div>
        </div>
    </body>
    </html>
    """, folder=folder, path=get_path_display())


@app.route("/open/<name>")
def open_item(name):
    """Open a folder."""
    global current_path
    folder = get_current_folder()
    if name in folder and folder[name] != "file":
        back_stack.append(list(current_path))
        current_path.append(name)
        forward_stack.clear()
    return redirect(url_for('index'))


@app.route("/file/<name>")
def open_file(name):
    """Simulate opening a file and store it in the linked list."""
    recent_files.add_file(name)
    return render_template_string("""
        <h2>📄 Opened File: {{ name }}</h2>
        <p><a href="{{ url_for('index') }}">Back to Explorer</a></p>
    """, name=name)


@app.route("/copy/<name>")
def copy_file(name):
    """Copy file into the queue."""
    folder = get_current_folder()
    if name in folder and folder[name] == "file":
        file_queue.append(name)
    return redirect(url_for('index'))


@app.route("/paste")
def paste_files():
    """Paste copied files into the current folder."""
    folder = get_current_folder()
    if file_queue:
        for f in file_queue:
            folder[f + "_copy"] = "file"
        file_queue.clear()
    return redirect(url_for('index'))


@app.route("/back")
def go_back():
    """Go back using stack."""
    global current_path
    if back_stack:
        forward_stack.append(list(current_path))
        current_path = back_stack.pop()
    return redirect(url_for('index'))


@app.route("/forward")
def go_forward():
    """Go forward using stack."""
    global current_path
    if forward_stack:
        back_stack.append(list(current_path))
        current_path = forward_stack.pop()
    return redirect(url_for('index'))


@app.route("/recent")
def show_recent_files():
    """Display recent files using Linked List traversal."""
    files = recent_files.get_all_files()
    return render_template_string("""
        <h2>🕘 Recent Files</h2>
        {% if files %}
            <ul>
            {% for f in files %}
                <li>{{ f }}</li>
            {% endfor %}
            </ul>
        {% else %}
            <p>No recent files yet.</p>
        {% endif %}
        <p><a href="{{ url_for('index') }}">Back to Explorer</a></p>
    """, files=files)


if __name__ == "__main__":
    app.run(debug=True)
