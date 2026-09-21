"""Update lyric tracks while preserving rows outside the requested region."""


def analyze_lyrics(paths, models, device, options, duration, folder, region, run_id, result):
    from lyrics import transcribe
    vocal = paths.get('vocals')
    if vocal is None:
        raise ValueError('歌詞解析の前にボーカル分離を完了してください。')
    tracks, engine = transcribe(vocal, models, device, options['mode'], options.get('lyrics', ''),
                                duration, folder, region)
    if region:
        for track, rows in tracks.items():
            kept = [r for r in result['tracks'].get(track, []) if r.get('start') is None or r['end'] <= region['start'] or r['start'] >= region['end']]
            # IDs include run so old and new rows cannot collide.
            for row in rows:
                row['id'] = run_id + '-' + row['id']
                if row.get('parentId'):
                    row['parentId'] = run_id + '-' + row['parentId']
            result['tracks'][track] = kept + rows
    else:
        result['tracks'].update(tracks)
    result['engines']['lyrics'] = engine
