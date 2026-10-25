"""Write a comparison result as JSON for tools and Markdown for listening notes."""
import json

COLUMNS = (
    ('モデル', 'id'), ('ライセンス', 'license'), ('処理秒', 'elapsedSeconds'), ('実時間比', 'realtimeFactor'),
    ('GPUピークMiB', 'peakGpuMemoryMiB'), ('GPU確保MiB', 'peakGpuReservedMiB'), ('4ステム', 'fourStems'),
    ('ボーカルdBFS', 'vocalsLevelDb'), ('伴奏dBFS', 'instrumentalLevelDb'),
    ('SDRボーカル', 'sdrVocals'), ('SDR伴奏', 'sdrInstrumental'),
)


def cell(value):
    if value is None:
        return '-'
    if isinstance(value, bool):
        return 'あり' if value else 'なし'
    return f'{value:.2f}' if isinstance(value, float) else str(value)


def markdown(report):
    excerpt = report['excerpt']
    span = f"{excerpt['start']:.1f}秒から{excerpt['seconds']:.1f}秒間"
    lines = [
        f"# 分離の比較：{report['input']}", '',
        f"- 区間：{span}", f"- 実行環境：{report['device']} / torch {report['torch']}",
        f"- MSST：{report['msstCommit']}", '',
        '| ' + ' | '.join(title for title, _ in COLUMNS) + ' |',
        '|' + '---|' * len(COLUMNS),
    ]
    lines += ['| ' + ' | '.join(cell(row.get(key)) for _, key in COLUMNS) + ' |' for row in report['models']]
    lines += [
        '', '伴奏はミックスからボーカルを引いた音です。',
        '4ステムが「あり」のモデルは stems/ にbass・drums・other・vocalsを保存します。'
        'otherを出さないモデルと組み合わせでは、ミックスから他の3つを引いた残りをotherにします。',
        '組み合わせの処理秒は2つのモデルの合計、GPUの値は大きいほうです。',
        'SDRは参照ボーカルを指定したときだけ計算し、伴奏の参照はミックスから参照ボーカルを引いて作ります。',
        '各モデルのフォルダーにある vocals.wav と instrumental.wav を聴き比べてください。',
    ]
    return '\n'.join(lines) + '\n'


def write(folder, report):
    (folder / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    (folder / 'report.md').write_text(markdown(report), encoding='utf-8')
