# 決定

- 2026-09-21: YAMNet v1を声の比較用に追加。通常分類はASTを継続し、scope=vocal-comparisonでAST/YAMNet×原曲/既存ボーカルを個別に比較する。YAMNetはTensorFlow 2.20 CPUの独立venv、アーカイブSHA-256固定、推論中通信禁止。しきい値は仮の基準であり実曲精度を保証しない。比較では通常トラック・手修正を上書きしない。

- 2026-09-21（更新）: ユーザー指定でコード推定をBTC・原曲入力・平滑化なしに統一。方式選択と比較UI、従来三和音推定、ChordNet実行経路を削除。キー推定は保持する。旧結果は自動移行せず、再推定で新runへ保存。以下の比較導入時の既定値方針を上書きする。

- 2026-09-21: ChordMini BTC/BTC弱平滑化/ChordNetを任意バックエンドとして追加。公式コードと重みを固定し、別venv・別プロセスで実行。元音源、50%重複、logit統合、min_segment_duration=0を基準とする。公式のstrict=False救済は禁止。実曲の正解率未評価のため既定値を従来方式から変更しない。キーは既存方式を維持する。

- 2026-09-20: Tauri 2 / React 19 / Vite 6 を採用。Vitest は既知の脆弱性を避けるため 4.1.11 以降へ更新。
- 開発ポートは 1430。参照元の 1420 と同時起動できる。
- ハーネスは Vitest + Testing Library + Tauri mockIPC、Rust テスト、統合 check、Windows CI、環境診断で構成。
- 2026-09-21: ローカルPython3.11ワーカーを追加。モデルはGPU上で順次読み込み、初回準備後はネット接続を禁止する。
- 日本語はlarge-v3の日本語固定・beam10と分離ボーカルのWhisperX alignment。多言語は言語自動判定・beam5。日本語/英語以外はASR時刻候補を明示する。
- 分離はhtdemucs_ft、拍はBeat This、構成はAll-In-One。コードはCQTの長短三和音候補と遷移抑制、主旋律はpYIN。複音・ラップ・ビートボックスは精度保証しない。
- 手修正はトラック単位の上書き＋保存リビジョン。過去の解析runsを保持し、同一音源・同一分離モデルのステムを再利用する。
- Windows の Rust テストにも Common Controls v6 マニフェストをリンクする。指定なしでは TaskDialogIndirect のロードが失敗したため、build.rs でアプリとテストに適用。
- 2026-09-21: 曲取り込みは音源選択1回のみ。保存先はOSのドキュメント/Music Sweeper/Projects。終了ハンドラーは保存後にdestroyを呼び、mainウィンドウだけにallow-destroyを付与する。TauriのonCloseRequestedは通常終了時にも内部でdestroyを使用するため、この権限を省かない。
- 声の表現はAST AudioSetのsigmoidスコアで独立検出し、ASRが認識できなかった箇所を非言語と見なさない。2秒窓・0.5秒hop、標準閾値0.15/候補多め0.06。分類窓の支持範囲を表示し、同種の重なる窓を結合する。スコアは未校正で、歌詞は自動削除しない。「その他」の自動対象はGroan/Grunt/Whimper/Laughterで、スキャットや無歌詞の母音歌唱は網羅しない。
- ラップ/語りは既存ASTのRapping/Narration, monologueを使用する実験的候補。一般Speechで語りを代用せず、実曲の未検出を閾値の恣意的引き下げで隠さない。手修正トラックへの新分類追加はUIで明示的に行い、修正保持と行IDの一意性を保証する。
