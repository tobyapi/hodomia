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
## MCP接続

Node.js 20以上で `node automation/mcp-server.mjs` を起動します。標準入出力はMCP専用です。クライアントのcommandにnpmを指定せず、Node実行ファイルとスクリプトの絶対パスを指定してください。

接続設定は次で生成できます（ユーザーのMCP設定を自動上書きしません）。

```powershell
node scripts/mcp-config.mjs --allow-root "$env:USERPROFILE\Downloads"
```

出力された `mcpServers` 設定を利用するクライアントに登録します。`--runtime`、`--projects`、`--registry` も指定でき、許可フォルダーは `--allow-root` の繰り返しで追加します。登録済みプロジェクトは読み書き可能ですが、新規音源の取り込みには音源フォルダーの明示的な許可が必要です。

MCPツールは `list_projects`、`import_audio`、`get_project`、`start_analysis`、`get_job`、`cancel_job`、`get_timeline`、`update_segments`、`extract_audio_clip`、`export_project`。JSONの構造化結果とエラーコードを返します。削除ツールや任意コマンド実行ツールはありません。

クリップ・書き出しの戻り値にある `music-sweeper://artifact/<id>` はMCPリソースとして読み取れます。生成物として登録したファイルだけが対象で、任意のファイルパスは受け付けません。1リソース16MiBまでです。解析は `start_analysis` → `get_job` で追跡し、完了してから時間範囲・トラックを指定して読み出します。スコアは正解率に変換せず、未確認フラグも保持します。

接続テストは `npm run test:automation`。公式SDKクライアントから別プロセスのサーバーへ接続し、取り込み・範囲取得・編集の再送と競合・音声リソース・CSV・許可範囲を確認します。

## デスクトップとの連携

`show_in_app` はroot、start/end（秒）、stem、trackを受け取り、表示リクエストのrequestIdを返します。アプリが起動中なら指定した曲・区間ループ・トラックを表示し、前面に出します。自動再生はしません。アプリが閉じていれば次回起動時に処理します（10分で期限切れ）。この操作自体は実行ファイルを起動しません。

`get_ui_request` にrequestIdを渡すとqueued/applied/failed/expiredを確認できます。queuedは表示完了を意味しません。アプリで処理中、解析中、手修正が未保存、詳細欄に未適用の入力がある場合は待機します。

GUIも同じ永続ジョブを起動・監視・取消します。**アプリやMCPクライアントを閉じても解析は継続します。** 止めたい場合は「処理を中止」またはcancel_jobを使って完了を待ってください。解析器が処理の区切りに到達するまで中止待ちになることがあります。モデルのセットアップは従来どおりGUI所有の処理で、アプリ終了時に停止します。セットアップと解析の重複は同じOSロックで防ぎます。

AIによる保存済みの変更は、未保存の作業がなければGUIへ反映します。手元の変更がある場合は保持し、競合を表示します。「最新の保存内容を読み込む」を押すと、手元の未保存変更を破棄するか確認して読み直せます。保存リビジョンを勝手に更新して競合を回避することはありません。

範囲取得と書き出しも解析中はBUSYになります。結果をページングする場合は解析の完了を待ち、revision/runIdを渡してください。中断された過去の解析はget_jobでinterrupted、過去の完了ジョブはそのジョブ固有のrunIdと進捗を返します。

実モデルを含む検証は `node scripts/verify-automation.mjs <検証用プロジェクトフォルダー> ...`。指定したプロジェクトにBTCの新しいrunを作り、MCP経由の完了追跡、コード取得、音源・手修正・対象外トラックの保持を確認します。通常の `npm run check` はモデル推論を実行しません。

声の比較は `start_analysis` のscope=vocal-comparisonで実行し、`get_vocal_comparison` で範囲取得できます。[AST / YAMNet比較](vocal-comparison.md)を参照してください。検証スクリプトは `--scope vocal-comparison` を先頭に指定すると両モデルの実行と既存結果の保持を確認します。
