# 出力JSONとプロジェクト形式

[READMEへ戻る](../README.md) · [使い方](usage.md) · [CLI・MCP](automation.md)

## プロジェクト形式

`project.json` に原本SHA256と現在のrunを記録。`source/` に原本コピー、`audio.wav` に再生・解析用PCM、`runs/<id>/` に自動結果・状態・分離音声、`edits.json` に手修正、`history/` に保存リビジョン、`exports/` に書き出しを格納します。移動時にはプロジェクトフォルダー全体をコピーしてください。過去runのステムを再利用するので、runsの一部だけを削除しないでください。

## 書き出すJSONの形式

「書き出し」またはCLI/MCPの `export_project` を実行すると、プロジェクト内の `exports/<日時>-<識別子>/analysis.json` にUTF-8のJSONを書き出します。同じフォルダーに `timeline.csv` と `lyrics.srt` も生成します。JSONは2スペースのインデント付きで、日本語はそのまま保存します。音声データ自体は埋め込みません。

### 最上位のフィールド

| フィールド | 内容 |
| --- | --- |
| `root` | 書き出し元プロジェクトの絶対パス |
| `project` | プロジェクト情報。`schemaVersion: 1`、`kind: "hodomia"`、`id`、`name`、`createdAt`（UTCのISO 8601）、`duration`（秒）、`source`、`audio`、`currentRun`を含む |
| `project.source` | `path`はプロジェクト内の原本コピーへの相対パス、`sha256`は原本のSHA-256 |
| `project.audio` / `project.currentRun` | 再生用音声の相対パス / 現在の解析runのID。未解析なら`currentRun`は`null` |
| `result` | 現在のrunの自動解析結果。未解析なら`{}`。手修正は含まない |
| `edits` | 保存済みの手修正。`revision`は保存リビジョン、`tracks`はトラック単位の上書き。自動操作後は`lastMutation`が付く場合もある |
| `tracks` | 自動結果へ保存済みの手修正を反映したトラック。外部ツールで編集後の内容を使う場合はここを読む |
| `bpm` | `tracks.beats`の時刻を昇順にし、正の拍間隔の中央値から再計算したBPM。計算できなければ`null` |
| `status` | 解析状態。`state`、`stage`（表示文言）、`errors`を含む。解析後は`progress`（0～1）や`elapsed`（秒）も入る |
| `notice` | 自動推定に未確認情報が含まれることを伝える文言 |

手修正は**トラック全体の置換**です。たとえば `edits.tracks.lyrics` があれば、`result.tracks.lyrics` の行に個別マージせず、その配列全体を `tracks.lyrics` に採用します。空配列 `[]` も有効な上書きです。まだ保存していない修正は、直接CLI/MCPから書き出したJSONには入りません。

`status.state` は `idle`（未解析）、`running`、`complete`、`partial`（一部失敗）、`failed`、`cancelled`。`errors` は `{ "stage": "段階名", "message": "エラー内容" }` の配列です。部分失敗や未解析でも書き出せるため、必要なトラックがあるか確認してください。CLI/MCP経由では解析中の書き出しは `BUSY` になります。

### トラックと行

`tracks`、`result.tracks`、`edits.tracks` は同じ行形式を使います。未実行・失敗・旧データではキー自体がない場合があるため、全キーの存在を前提にしないでください。

| キー | 内容 |
| --- | --- |
| `beats` | 拍。`start == end`の点。小節頭は`label: "1"`、通常の拍は`"拍"` |
| `sections` | ヴァース、サビなどの曲構成候補 |
| `lyrics` | 歌詞行 |
| `words` | 単語相当の区間。日本語では文字相当の場合もある |
| `vocalEvents` | ラップ、語り、ビートボックス、ブレスなどの候補 |
| `chords` | コード。BTCの元ラベル（例：`A:min7`）。`N`は和音なし、`X`は判定不能 |
| `key` | 調性候補（例：`C minor`） |

各行の基本フィールドは `id`（同じトラック内で一意な文字列）、`start`、`end`、`label`。時刻は**原曲の先頭からの秒数**で、小数を含みます。拍以外は開始より終了が後です。歌詞・単語の時刻が未確定なら、`start`と`end`はともに`null`になります。行IDの接頭辞や配列順に意味を固定せず、並べ替えが必要なら`null`を分けて時刻でソートしてください。

`reviewed` は試聴・確認済みかどうか。自動結果は `false`、旧データ等で省略されていても未確認として扱います。`warning`（注意文）、`language`（言語コード）、`parentId`（対応する歌詞行のID）、`uncertain`などは任意です。

`vocalEvents` には次のフィールドも入ります。

| フィールド | 内容 |
| --- | --- |
| `category` | `rap` / `spoken` / `beatbox` / `breath` / `humming` / `other` |
| `detectedCategory` | 元のモデル分類。手修正後の`category`とは異なる場合がある |
| `score` | ASTの未校正モデルスコア。正解率ではない。補助検出や手入力にはない場合がある |
| `method` | 補助検出では`"vocal-percussion"`。全行にあるわけではない |
| `evidenceSources` / `evidenceLabels` | 根拠となった音声（`original` / `vocals`）とAudioSetラベルの配列 |
| `timingUncertainty` | 窓幅などに基づく時刻の不確かさの目安（秒）。厳密な誤差保証ではない |

### 自動解析結果と時系列

`result` は `runId`、`mode`（`japanese` / `multilingual` / `instrumental`）、`sourceHash`、`tracks`、`series`、`stems`、`engines`、推定できた場合の `bpm` を含みます。`result.bpm` は自動解析時の値なので、拍を修正した後の最上位 `bpm` と異なる場合があります。段階的に保存するため、これらのフィールドも欠ける場合があります。

| `result.series` のキー | 形式・単位 |
| --- | --- |
| `waveform` | 曲全体を分割した各ブロックのピーク振幅配列。最大4000点。音声サンプル列ではない |
| `energy` | `{ "time": 秒, "value": 0～1 }`の配列。平滑化した音量の相対値 |
| `tempo` | `{ "time": 秒, "value": BPM }`の配列 |
| `pitch` | `{ "points": [{ "time": 秒, "value": MIDI音高またはnull }], "warning": "説明" }`。MIDI音高は小数を含み、Hzではない |
| `vocals` / `drums` / `bass` / `other` | `{ "regions": [区間行], "levels": [{ "time": 秒, "value": 0～1 }] }`。分離音声の出入りと相対音量 |
| `peak` / `silence` | 原曲のピーク振幅 / 無音判定の真偽値 |

`result.stems` はパート名から音声ファイルへの相対パスの対応表です。パスの基準は `root` で、JSONのある `exports/` ではありません。過去runの分離音声を再利用する場合もあります。`result.engines` は使用モデル・設定・来歴を記録し、値はエンジンによって文字列またはオブジェクトになります。旧runから引き継いだ追加情報が含まれることもあります。

### JSONの例

次は構造を示す架空の例です。自動解析には時刻不明の歌詞があり、保存済みの手修正で時刻を付けた状態です。ID・ハッシュは例示用で、時系列やモデル来歴の詳細は省略しています。

```json
{
  "root": "D:/songs/example-project",
  "project": {
    "schemaVersion": 1,
    "kind": "hodomia",
    "id": "example-project-id",
    "name": "サンプル曲",
    "createdAt": "2026-01-01T00:00:00+00:00",
    "duration": 60.0,
    "source": { "path": "source/example.mp3", "sha256": "<原本のSHA-256・64桁>" },
    "audio": "audio.wav",
    "currentRun": "example-run"
  },
  "edits": {
    "revision": 1,
    "tracks": {
      "lyrics": [
        { "id": "line-0", "start": 2.0, "end": 4.5, "label": "サンプルの歌詞", "reviewed": true }
      ]
    }
  },
  "result": {
    "runId": "example-run",
    "mode": "japanese",
    "sourceHash": "<原本のSHA-256・64桁>",
    "tracks": {
      "lyrics": [
        { "id": "line-0", "start": null, "end": null, "label": "サンプルの歌詞", "reviewed": false }
      ]
    },
    "series": {},
    "stems": { "vocals": "runs/example-run/stems/vocals.wav" },
    "engines": {}
  },
  "status": { "state": "partial", "stage": "一部の解析に失敗しました", "progress": 1, "elapsed": 30.0, "errors": [{ "stage": "拍・BPM", "message": "例示用のエラー" }] },
  "tracks": {
    "lyrics": [
      { "id": "line-0", "start": 2.0, "end": 4.5, "label": "サンプルの歌詞", "reviewed": true }
    ]
  },
  "bpm": null,
  "notice": "自動推定には未確認の情報を含みます。"
}
```

`analysis.json` の最上位には `schemaVersion` がありません。`project.schemaVersion` はプロジェクト形式の版です。CLIの標準出力にある `{ "schemaVersion": 1, "ok": true, "value": ... }` は別の応答形式で、`export_project` の `value` は保存先などを返します。CLI/MCPの形式は [自動操作](automation.md) を参照してください。

共有する際は、`root`の絶対パス、曲名、原本ファイル名、歌詞・手入力、エラー内のパス、モデル来歴を確認してください。書き出し時の匿名化は行いません。JSONだけを渡しても、参照先の音声は再生できません。
