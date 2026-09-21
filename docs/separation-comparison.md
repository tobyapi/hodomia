# DemucsとMel-Bandの比較

「編集トラック」を「声の表現」にして、「Mel-Bandで分離して比較」を押す。このPCではモデルを準備済み。別のPCでは同じ欄の「Mel-Bandをセットアップ」と、下の「YAMNetをセットアップ」を先に実行する。開発環境では `npm run setup:melband` / `npm run setup:yamnet`。

原曲からMel-Bandのボーカル・伴奏を別に作り、原曲／Demucsボーカル／Mel-BandボーカルをAST・YAMNetで検出する。Demucsが未実行なら4ステム分離も行う。6通りの分類スコアと候補帯を表示する。

4つの音声ボタンは現在位置とループ区間を保って切り替える。切り替え後は再生ボタンを押す。Mel-Bandボーカルで弱くなった音は伴奏側も確認する。スコアや候補数だけで分離品質・検出精度の優劣は判断できない。

## 保存と既存データ

通常のDemucsの4ステム、解析トラック、手修正は保持する。通常の歌詞認識・声の表現検出の入力は自動変更しない。BTCの原曲入力も維持する。

`result.json` の `separationComparison.stems` に `melband_vocals` / `melband_instrumental`、`engine` に来歴を保存する。既存の `stems` へ混ぜず、別モデルの音を4ステムの一組として合成しない。分類比較は `vocalComparisons` と `vocal-comparison.csv` に入る。その後の「AST / YAMNet を比較」でも保存済みMel-Bandボーカルが対象になる。

音声は `runs/<id>/melband/` に保存する。同じ入力音声ハッシュ・重み・設定・実装・依存バージョンなら再利用し、出力のハッシュも検証する。過去runを消すと再利用音声を失うので、プロジェクト単位で保存する。全体再分析は新しい通常解析を作るため、Mel-Band比較は必要に応じて再実行する。過去のrunは残る。

## モデルと条件

- [Kimberley Jensen公開モデル](https://huggingface.co/KimberleyJSN/melbandroformer)、固定リビジョン `ac9b0614ab3cd7f77219e18ba494dfd93956c348`。配布ページのライセンス表記はMIT。取得元をinstallation.jsonに記録。
- 重みSHA-256 `87201f4d31afb5bc79993230fc49446918425574db48c01c405e44f365c7559e`。ローカル名 `vocals_mel_band_roformer.ckpt`。
- 対応YAMLは[audio-separator 0.47.0](https://github.com/nomadkaraoke/python-audio-separator/tree/v0.47.0)の定義にある `vocals_mel_band_roformer.yaml`。SHA-256 `b958b29c8f7195f0d86bee6759a33980db675c4ecaf2fcaa80fa125828e6cd38`。
- `.runtime/melband/venv` にPython3.11 / audio-separator0.47.0 / torch2.8.0+cu128。全依存は `analysis/melband-requirements.lock.txt`。GPU非対応時はCPU。ONNX Runtimeはインポート用で、このモデルはPyTorchのCUDAを使う。
- 入力は原曲の44.1kHzステレオPCM。分類器向け16kHzモノラルは分離後に作る。
- segment_size=801（8秒窓）、overlap=4、autocast有効、pitch_shift=0。CUDAメモリー不足時だけ別プロセスで401（4秒窓）を再試行し、実効設定とfallbackを記録。
- ノイズゲート・デノイズ・デリバーブは追加しない。ライブラリー側のピーク正規化は上限1.0、増幅無効。出力WAVは入力PCMのビット深度を引き継ぐ。モデル間の絶対音量が同一とは仮定しない。

セットアップで重み・設定と通信禁止の試験推論を検証する。推論は固定ローカルファイルを直接参照し、オンラインのモデル一覧も使わない。破損・出力時刻不一致・NaNは失敗扱い。中止時は子プロセスも終了する。処理時間上限2時間、入力は15分以内。CPU全曲と実際のGPUメモリー不足時の品質は未評価。

## MCP / ヘッドレス

`start_analysis` の `options: {mode: "japanese", scope: "separation-comparison"}` で開始し、`get_job` で完了を待つ。未準備なら `MODEL_NOT_READY`。この操作ではモデルを取得しない。

`get_vocal_comparison` のvariantIdに `ast-melband_vocals` / `yamnet-melband_vocals` を指定できる。`get_project` は追加音声名を返す。`extract_audio_clip` / `show_in_app` のstemには `melband_vocals` / `melband_instrumental` を指定する。

実曲検証（指定プロジェクトへ新runを作成）:

```powershell
node scripts/verify-automation.mjs --scope separation-comparison "test-results/検証曲A-05eb9e1b" "test-results/検証曲B-ce1ef4c8"
```
