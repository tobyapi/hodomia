"""Set each model's sections, lyrics and stem activity against those from the baseline stems."""
import json

import agreement
from candidates import BASELINE, STEMS

COLUMNS = (
    ('モデル', 'id'), ('区間数', 'sections'), ('境界F ±0.5秒', 'boundaryF05'), ('境界F ±3秒', 'boundaryF3'),
    ('区間名の一致率', 'labelAgreement'), ('歌詞CER（基準比）', 'lyricsCer'), ('歌詞の行', 'lines'),
    ('時刻未確定の行', 'untimedLines'), ('発話なし警告', 'noSpeechLines'), ('平均logprob', 'meanAvgLogprob'),
) + tuple((f'{name}活動IoU', f'activity_{name}') for name in STEMS)


def against(baseline, result, duration):
    lyrics = result['lyrics']
    row = dict(id=result['id'], lines=lyrics['lines'], untimedLines=lyrics['untimedLines'],
               noSpeechLines=lyrics['noSpeechLines'], meanAvgLogprob=lyrics['meanAvgLogprob'],
               lyricsCer=agreement.character_error_rate(baseline['lyrics']['text'], lyrics['text']))
    if 'sections' not in result:
        return row
    reference = agreement.boundaries(baseline['sections'], duration)
    estimate = agreement.boundaries(result['sections'], duration)
    row.update(sections=len(result['sections']),
               boundaryF05=agreement.boundary_f(reference, estimate, .5),
               boundaryF3=agreement.boundary_f(reference, estimate, 3),
               labelAgreement=agreement.label_agreement(baseline['sections'], result['sections'], duration))
    for name in STEMS:
        row[f'activity_{name}'] = agreement.activity_overlap(baseline['activity'][name], result['activity'][name])
    return row


def cell(value):
    if value is None:
        return '-'
    return f'{value:.3f}' if isinstance(value, float) else str(value)


def markdown(report, rows):
    lines = [
        f"# 分離の違いによる曲構成・歌詞の変化：{report['input']}", '',
        f"基準は {BASELINE.id} のステムから得た推定です。一致の値は基準とのずれを示し、正しさは示しません。", '',
        '| ' + ' | '.join(title for title, _ in COLUMNS) + ' |',
        '|' + '---|' * len(COLUMNS),
    ]
    lines += ['| ' + ' | '.join(cell(row.get(key)) for _, key in COLUMNS) + ' |' for row in rows]
    lines += ['', '境界Fは区間の始まりと終わりが基準と許容幅以内で一致した割合です。'
              '歌詞CERは基準のWhisper出力に対する文字誤り率で、NFKC正規化と記号の除去をしてから数えます。',
              '活動IoUは分離音声の相対音量から判定した「鳴っている時間」の重なりです。']
    return '\n'.join(lines) + '\n'


def write(folder, report, results, duration):
    baseline = next(result for result in results if result['id'] == BASELINE.id)
    rows = [against(baseline, result, duration) for result in results]
    document = dict(input=report['input'], duration=duration, baseline=BASELINE.id, models=rows, results=results)
    (folder / 'downstream.json').write_text(json.dumps(document, ensure_ascii=False, indent=2), encoding='utf-8')
    (folder / 'downstream.md').write_text(markdown(report, rows), encoding='utf-8')
