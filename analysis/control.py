"""Application operations consumed by headless and MCP adapters, without GUI imports."""
from pathlib import Path
from control_errors import ControlError
from jobs import Jobs
from project_library import canonical, default_projects, default_registry, list_projects, registered, remember
import storage


class Control:
    def __init__(self, runtime, projects=None, registry=None, allowed_roots=()):
        self.runtime = canonical(runtime)
        self.projects = canonical(projects or default_projects())
        self.registry = canonical(registry or default_registry())
        self.allowed = [self.projects, *(canonical(p) for p in allowed_roots)]
        self.jobs = Jobs(self.runtime)

    def root(self, value):
        root = canonical(value)
        if root not in registered(self.registry) and not any(root.is_relative_to(p) for p in self.allowed):
            raise ControlError('ACCESS_DENIED', '許可したフォルダー内か、アプリに登録済みのプロジェクトを指定してください。')
        storage.manifest(root)
        return root

    def dispatch(self, operation, args):
        if not isinstance(args, dict):
            raise ValueError('argsはJSONオブジェクトで指定してください。')
        if operation == 'list_projects':
            return {'projects': list_projects(self.projects, self.registry)}
        if operation == 'capture_app':
            from screenshots import capture
            return capture(self.runtime, **args)
        if operation == 'import_audio':
            source = canonical(args['source'])
            if not any(source.is_relative_to(p) for p in self.allowed):
                raise ControlError('ACCESS_DENIED', '音源のフォルダーを--allow-rootで許可してください。')
            self.projects.mkdir(parents=True, exist_ok=True)
            value = storage.create(source, self.projects)
            remember(self.registry, value['root'])
            return self.summary(value['root'])
        if operation == 'get_project':
            return self.summary(self.root(args['root']))
        if operation == 'start_analysis':
            return self.jobs.start(self.root(args['root']), args.get('options', {'mode': 'japanese'}))
        if operation in ('get_job', 'cancel_job'):
            value = self.jobs.get(args['jobId'], args.get('includeLog', False))
            self.root(value['root'])
            return self.jobs.cancel(args['jobId']) if operation == 'cancel_job' else value
        if operation == 'export_project':
            from artifacts import Artifacts
            root = self.root(args['root'])
            value = storage.export(root)
            artifacts = Artifacts(self.runtime)
            value['artifacts'] = [artifacts.register(root, Path(value['path']) / name, mime)
                                  for name, mime in [('analysis.json', 'application/json'), ('timeline.csv', 'text/csv'), ('lyrics.srt', 'text/plain')]]
            return value
        if operation == 'get_timeline':
            from timeline_api import get_timeline
            return get_timeline(self.root(args['root']), **{k: v for k, v in args.items() if k != 'root'})
        if operation == 'update_segments':
            from timeline_api import update_segments
            return update_segments(self.root(args['root']), **{k: v for k, v in args.items() if k != 'root'})
        if operation == 'extract_audio_clip':
            from audio_clips import extract_clip
            from artifacts import Artifacts
            root = self.root(args['root'])
            clip = extract_clip(root, **{k: v for k, v in args.items() if k != 'root'})
            clip['artifact'] = Artifacts(self.runtime).register(root, clip['path'], 'audio/wav')
            return clip
        if operation == 'read_artifact':
            from artifacts import Artifacts
            return Artifacts(self.runtime).read(args['artifactId'], self.root)
        if operation == 'show_in_app':
            from ui_requests import UiRequests
            return UiRequests(self.runtime).enqueue(self.root(args['root']), **{k: v for k, v in args.items() if k != 'root'})
        if operation == 'get_ui_request':
            from ui_requests import UiRequests
            value = UiRequests(self.runtime).get(args['requestId'])
            self.root(value['root'])
            return value
        raise ControlError('UNKNOWN_OPERATION', '不明な操作です: ' + str(operation))

    def summary(self, root):
        value = storage.snapshot(root)
        tracks = storage.effective_tracks(value)
        return dict(root=str(canonical(root)), project=value['project'], revision=value['edits']['revision'],
                    status=value['status'], engines=value['result'].get('engines', {}),
                    tracks={name: {'count': len(rows), 'unreviewed': sum(not row.get('reviewed', False) for row in rows)} for name, rows in tracks.items()},
                    stems=list(value['result'].get('stems', {})))
