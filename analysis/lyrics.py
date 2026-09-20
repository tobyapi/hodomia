"""Singing transcription and evidence-based line/word alignment."""
from dataclasses import asdict
from difflib import SequenceMatcher
import unicodedata
from storage import row, write_json
from engines import release


def comparable(text):
    return ''.join(c for c in unicodedata.normalize('NFKC', text).lower() if c.isalnum())


def match_lines(text, segments, duration):
    units = []
    for segment in segments:
        units.extend({'text': word['word'], 'start': word['start'], 'end': word['end']}
                     for word in segment.get('words', []) if word.get('start') is not None)
        if not segment.get('words'):
            units.append(segment)
    cursor, windows = 0, []
    for line in filter(None, (s.strip() for s in text.splitlines())):
        target, best = comparable(line), None
        for start in range(cursor, len(units)):
            candidate = ''
            for end in range(start, len(units)):
                if units[end]['end'] - units[start]['start'] > 60:
                    break
                candidate += comparable(units[end]['text'])
                if len(candidate) > max(8, len(target) * 1.8):
                    break
                score = SequenceMatcher(None, target, candidate, autojunk=False).ratio()
                if best is None or score > best[0]:
                    best = (score, start, end)
        if not target or best is None or best[0] < .5:
            windows.append({'text': line, 'start': None, 'end': None, 'words': []})
        else:
            _, a, b = best
            windows.append({'text': line, 'start': max(0, units[a]['start'] - .25),
                            'end': min(duration, units[b]['end'] + .25), 'words': []})
            cursor = b + 1
    return windows


def transcribe(path, models, device, mode, supplied, duration, run, region=None):
    import librosa
    import nltk
    from faster_whisper import WhisperModel
    nltk.data.path.insert(0, str(models / 'nltk'))
    language = 'ja' if mode == 'japanese' else None
    offset = 0
    audio, _ = librosa.load(str(path), sr=16000, mono=True)
    if region:
        offset = region['start']
        audio = audio[round(region['start'] * 16000):round(region['end'] * 16000)]
        language = region['language']
    # CTranslate2 uses the CUDA DLLs already shipped by PyTorch.
    import torch
    import os
    dll_handles = []
    if os.name == 'nt':
        dll_handles.append(os.add_dll_directory(str(__import__('pathlib').Path(torch.__file__).parent / 'lib')))
    model = WhisperModel(str(models / 'large-v3'), device=device,
                         compute_type='int8_float16' if device == 'cuda' else 'int8',
                         local_files_only=True, cpu_threads=8)
    segments, info = model.transcribe(audio, language=language, beam_size=10 if mode == 'japanese' else 5,
                                     vad_filter=False, condition_on_previous_text=False,
                                     word_timestamps=True, no_repeat_ngram_size=4)
    raw = [{'text': s.text.strip(), 'start': s.start, 'end': s.end,
            'words': [asdict(w) for w in (s.words or [])]} for s in segments]
    language = language or info.language
    write_json(run / 'transcript.json', {'segments': raw, 'language': language, 'offset': offset})
    del model
    release()
    local_duration = len(audio) / 16000
    if region and supplied.strip():
        windows = [{'text': supplied.strip(), 'start': 0, 'end': local_duration, 'words': []}]
    else:
        windows = match_lines(supplied, raw, local_duration) if supplied.strip() else raw
    lines, words, aligner, metadata = [], [], None, None
    align_name = {'ja': 'japanese', 'en': 'english'}.get(language)
    if align_name:
        import whisperx
        aligner, metadata = whisperx.load_align_model(language, device, model_name=str(models / align_name), model_cache_only=True)
    for i, window in enumerate(windows):
        found = []
        if window['start'] is not None and aligner is not None:
            aligned = whisperx.align([window], aligner, metadata, audio, device,
                                     return_char_alignments=True, interpolate_method='ignore')
            found = [w for w in aligned.get('word_segments', []) if all(k in w for k in ('start', 'end', 'score'))
                     and 0 <= w['start'] < w['end'] <= local_duration]
        elif not supplied.strip():
            found = [dict(w, score=w.get('probability', 0)) for w in window.get('words', [])
                     if 0 <= w['start'] < w['end'] <= local_duration]
        start = min(w['start'] for w in found) + offset if found else None
        end = max(w['end'] for w in found) + offset if found else None
        warning = '自動推定・要確認'
        if not found:
            warning = '時刻は未確定。歌詞または探索区間を修正して再解析してください。'
        elif aligner is None:
            warning = 'この言語はASR時刻の候補です。専用アラインメントは未対応。'
        line = row('lyric', i, start, end, window['text'], language=language, warning=warning)
        lines.append(line)
        for word in found:
            words.append(row('word', len(words), float(word['start']) + offset, float(word['end']) + offset,
                             word.get('word', '').strip(), parentId=line['id'], language=language,
                             warning='日本語では文字相当の単位になる場合があります。' if language == 'ja' else '自動推定・要確認'))
    del aligner
    release()
    write_json(run / 'alignment.json', {'lyrics': lines, 'words': words, 'language': language})
    return {'lyrics': lines, 'words': words}, {'asr': 'large-v3', 'language': language,
                                               'alignment': align_name, 'device': device}
