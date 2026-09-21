# ローカル自動操作

GUIを開かず、同じプロジェクト形式と解析器を使用できます。初回セットアップはGUIまたは`npm run setup:analysis`で済ませてください。解析はオフラインで実行します。

## ヘッドレスCLI

```powershell
npm run headless -- list_projects
```

機械処理ではnpmのバナーを避けて `node scripts/headless.mjs` を直接使います。引数の引用が複雑になる操作は、UTF-8のJSONを標準入力へ渡してください。

```json
{"operation":"start_analysis","args":{"root":"D:/songs/project","options":{"mode":"japanese","scope":"harmony"}}}
```

`--runtime`、`--projects`、`--registry`で環境を指定できます。標準プロジェクト保存先とGUI登録済みプロジェクトを扱い、追加の音源・プロジェクトフォルダーは `--allow-root D:/songs` で許可します。ファイル選択ダイアログは開きません。

出力は1件のJSON、`schemaVersion:1`。成功は`{ok:true,value:...}`、失敗は`{ok:false,error:{code,message}}`と非ゼロ終了コードです。進捗やログは標準出力へ混ぜません。

| 操作 | 引数 |
| --- | --- |
| list_projects | なし |
| import_audio | source（コピー元。元音源は変更しない） |
| get_project | root（概要・件数・解析状態。波形配列は返さない） |
| start_analysis | root、options（mode、scope、lyrics等） |
| get_job | jobId、includeLog（任意） |
| cancel_job | jobId |
| export_project | root |

start_analysisはjobIdを返し、解析は独立プロセスで継続します。get_jobでqueued/running/cancelling/complete/partial/failed/cancelled/interruptedを確認します。中止は協調方式で、解析段階や各解析器の中断ポイントまで待つ場合があります。要求元のCLI終了はジョブの中止を意味しません。状態とログはruntime/control/jobsへ保存します。

同じruntimeでは解析1件、同じプロジェクトも同時解析1件です。プロセス終了時にOSがロックを解放します。手修正保存はリビジョンとプロセス間ロックで競合を検出します。BUSYは処理完了後、CONFLICTはデータを再取得してから再試行してください。音源や解析データの削除は自動操作APIには公開しません。

## 必要な区間だけを取得・修正する

- `get_timeline`: root、tracks（配列）、start/end（秒）、view（effective/automatic/manual）、offset/limit、includeUntimed。既定100件、最大500件。時間範囲に重なる行を返し、行の元時刻は変更しない。拍は開始を含み終了を含まない区間で判定する。次ページには返されたrevision/runIdをexpectedRevision/expectedRunIdとして渡すと、ページ間の変更を検出できる。
- `extract_audio_clip`: root、start、end、stem（original/vocals/bass/drums/other）。最大30秒のWAVをプロジェクトのexports/clipsへ生成し、パスと実際のサンプル境界、artifactIdを返す。元音源は変更しない。
- `read_artifact`: artifactId。生成済みの許可されたファイルだけを取得する。WAVはbase64、テキストはUTF-8。最大16MB。切り出しだけではAIによる音声理解を保証しないため、音声対応クライアントで使用する。
- `update_segments`: root、expectedRevision、expectedRunId（未解析ならnull）、requestId、operations、dryRun。operationsは最大100件のadd/update/delete。各操作にtrack、既存行のid、変更フィールドchangesを指定する。addのIDは自動生成。変更フィールドはstart/end/label/reviewed/language/category。

```json
{"operation":"update_segments","args":{"root":"D:/songs/project","expectedRevision":0,"expectedRunId":"保存済みrunId","requestId":"beatbox-fix-001","dryRun":true,"operations":[{"op":"update","track":"vocalEvents","id":"対象行ID","changes":{"category":"beatbox","label":"ビートボックス"}}]}}
```

dryRunでは差分だけを返す。実際に適用する場合はfalseにし、同じrequestIdの同じ要求を再送しても二重適用しない。別内容で同じrequestIdを再利用するとCONFLICT。変更前後の行は応答とhistory/operationsへ、適用後の全手修正は従来のhistory/edits-N.jsonへ保存する。解析中の行単位変更・音声切り出しはBUSYになる。自動結果や未指定トラックは書き換えない。
