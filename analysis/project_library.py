"""Shared saved-project discovery; accepts the existing desktop registry files."""
import hashlib
import os
import sys
from pathlib import Path
from storage import manifest, read_json, write_json


def canonical(path):
    text = str(path)
    if text.startswith('\\\\?\\UNC\\'):
        text = '\\\\' + text[8:]
    elif text.startswith('\\\\?\\'):
        text = text[4:]
    return Path(text).expanduser().resolve()


def default_projects():
    if os.name == 'nt':
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r'Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders') as key:
            documents = os.path.expandvars(winreg.QueryValueEx(key, 'Personal')[0])
    else:
        documents = Path.home() / 'Documents'
    return canonical(documents) / 'hodomia/Projects'


def default_registry():
    if sys.platform == 'darwin':
        return Path.home() / 'Library/Application Support/app.hodomia.desktop/library'
    return Path(os.environ.get('APPDATA', Path.home() / '.local/share')) / 'app.hodomia.desktop/library'


def registered(registry):
    roots = set()
    for entry in Path(registry).glob('*.json'):
        try:
            value = read_json(entry)
            if isinstance(value, str):
                roots.add(canonical(value))
        except (OSError, ValueError):
            continue
    return roots


def list_projects(parent, registry):
    parent = Path(parent)
    roots = registered(registry) | (set(parent.iterdir()) if parent.is_dir() else set())
    hidden = registered(Path(registry) / 'hidden')
    projects = []
    for root in sorted({canonical(p) for p in roots} - hidden):
        try:
            project = manifest(root)
            projects.append(dict(root=str(root), projectId=project['id'], name=project['name'],
                                 duration=project['duration'], createdAt=project.get('createdAt'),
                                 hasAnalysis=bool(project.get('currentRun'))))
        except (OSError, ValueError, KeyError, TypeError):
            continue
    return sorted(projects, key=lambda p: (p['createdAt'] or '', p['root']), reverse=True)


def remember(registry, root):
    registry, root = Path(registry), canonical(root)
    manifest(root)
    registry.mkdir(parents=True, exist_ok=True)
    key = hashlib.sha256(os.path.normcase(str(root)).encode()).hexdigest()
    write_json(registry / (key + '.json'), str(root))
