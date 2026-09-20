# 構成

React UI → src/api.ts → Tauri IPC → Rust workspace → Python CLI。

- `App.tsx`: プロジェクト操作と画面の組み立て。`components/`: 時間軸と項目編集。`editing.ts` / `useEdits.ts`: 修正データとUndo/Redo。
- `workspace.rs`: ネイティブ選択、許可済みパス、ワーカー起動・中止、ログ。MLライブラリをRust/UIへ直接持ち込まない。
- `analysis/storage.py`: プロジェクト形式、原本コピー、修正履歴、書き出し。MLを読み込まず操作可能。
- `pipeline.py`: 段階実行、チェックポイント、部分失敗。`engines.py`: 学習済みモデル。`dsp.py`: 信号処理。`lyrics.py`: ASR・既知歌詞照合・時刻合わせ。
- `prepare.py`: オンラインモデル準備専用。解析とは別プロセス。
- `vocal_events.py`: 原曲と分離ボーカルの多ラベル音声分類。歌詞データに依存せず、候補範囲・根拠・未校正スコアを返す。`scope=vocal-events` の解析は既存の自動結果をコピーしてこのトラックだけ更新する。
- `tests/ui/`: ブラウザー専用の注入ハーネス。本番のViteエントリには含めない。

原本・解析ごとのruns・手修正editsを分離し、再解析時に手修正を上書きしない。修正はトラック単位の上書きであり、区間再解析の結果を見るには「自動結果を比較」を使う。

- 再生音量: `components/VolumeControl.tsx` が音声要素の音量・ミュートとUI設定の永続化を担当する。音源・解析値を変更せず、設定保存が使えなくても試聴を継続する。
