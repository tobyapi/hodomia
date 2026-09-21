# 構成

React UI → src/api.ts → Tauri IPC → Rust workspace → Python CLI。

自動操作はheadless.py → control.py → storage/jobs/pipeline。stdioの形式と業務操作を分離する。jobsは独立ワーカーと永続状態を所有し、lockingのOSファイルロックをGUI側の保存・解析にも適用する。project_libraryは既存のGUI登録ファイルを読み取る。

MCPはautomation/mcp-server.mjs → worker-client.mjs → headless.py。公式SDKはstdio・スキーマを扱い、業務ロジックを持たない。timeline_apiは範囲取得とCAS・再送可能な修正、audio_clipsは試聴用切り出し、artifactsは生成物だけを公開する。ui_requestsはGUI表示要求を保存し、GUIが未保存入力を保護しながら応答する。GUIの解析もcli.py → Jobsを通り、終了時に解析ワーカーを殺さない。セットアップの子プロセスは従来どおりRustが所有する。

- `App.tsx`: プロジェクト操作と画面の組み立て。`components/`: 時間軸と項目編集。`editing.ts` / `useEdits.ts`: 修正データとUndo/Redo。
- `workspace.rs`: ネイティブ選択、許可済みパス、ワーカー起動・中止、ログ。MLライブラリをRust/UIへ直接持ち込まない。
- `analysis/storage.py`: プロジェクト形式、原本コピー、修正履歴、書き出し。MLを読み込まず操作可能。
- `pipeline.py`: 段階実行、チェックポイント、部分失敗。`engines.py`: 学習済みモデル。`dsp.py`: 信号処理。`lyrics.py`: ASR・既知歌詞照合・時刻合わせ。
- `prepare.py`: オンラインモデル準備専用。解析とは別プロセス。
- `vocal_events.py`: 原曲と分離ボーカルの多ラベル音声分類。歌詞データに依存せず、候補範囲・根拠・未校正スコアを返す。`scope=vocal-events` の解析は既存の自動結果をコピーしてこのトラックだけ更新する。
- `tests/ui/`: ブラウザー専用の注入ハーネス。本番のViteエントリには含めない。

原本・解析ごとのruns・手修正editsを分離し、再解析時に手修正を上書きしない。修正はトラック単位の上書きであり、区間再解析の結果を見るには「自動結果を比較」を使う。

- 再生音量: `components/VolumeControl.tsx` が音声要素の音量・ミュートとUI設定の永続化を担当する。音源・解析値を変更せず、設定保存が使えなくても試聴を継続する。
- `components/Player.tsx`: 再生操作とシークUI。音声要素と再生状態はAppが所有し、VolumeControlが音量設定を担当する。

- `src-tauri/src/library.rs`: OSの標準プロジェクト保存先とアプリデータ内の登録パスから保存曲一覧を構築する。音源/解析データは従来どおりPython storageが管理し、一覧は複製しない。
- `analysis/vocal_percussion.py`: 高感度の打撃音候補生成。意味分類や校正済み確率を返さず、声の分類結果と区別する。コード推定はBTCへ統一し、dspは伴奏からキーだけを推定する。
- `analysis/chordmini.py`: 学習済みコード推定のプロセス境界。インストール検証、取消、.lab検証、来歴保存を担当。`chordmini_runner.py`は分離venv内で固定した公式前処理・推論を呼び、厳密な重み読込と通信禁止を強制する。`chordmini_install.py`とsetup-chordmini.ps1が初回準備を担当する。
- `components/ChordControls.tsx`: BTC固定の再推定操作と旧解析結果の案内。方式選択はなく、pipelineは新しいコード解析でchordComparisonsを生成しない。旧runsと手修正は保持し、コード解析に失敗しても従来方式へフォールバックしない。
