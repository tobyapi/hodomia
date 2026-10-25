# ボーカル分離の比較

[開発環境と検証へ戻る](development.md)

解析で使っている htdemucs_ft と、BS-RoFormer系のボーカル分離モデルを手元の曲で聴き比べる開発用ツールです。アプリの解析には組み込んでいません。比較用のPython環境は解析環境と分け、`<runtime>/separation-compare/` に作ります。

## 準備

基準の htdemucs_ft は解析環境のモデルをそのまま使うので、先に `npm run setup:analysis` を済ませておきます。続けて次を実行します。ネット接続が必要なのはこの手順だけです。

```powershell
uv run --no-project --python 3.11 scripts/separation/prepare.py --include-unlicensed
```

このコマンドはPython 3.11の別環境を作り、[MSST](https://github.com/ZFTurbo/Music-Source-Separation-Training) を固定コミットで取得し、候補モデルの重みをダウンロードします。重みはSHA-256で照合し、一致しないファイルは残しません。

`--include-unlicensed` を付けない場合、ライセンスの記載がない重み（viperx版BS-RoFormer）は取得しません。付けた場合も、手元での評価に使う前提です。

## 比較

```powershell
.runtime/separation-compare/venv/Scripts/python.exe scripts/separation/compare.py "projects/<フォルダー>/<プロジェクト>" --start 45 --duration 30
```

Macでは `venv/bin/python` を使います。比較中はPythonのネット接続を禁止します。

| 引数 | 内容 |
| --- | --- |
| 曲 | 音源ファイル、またはhodomiaのプロジェクトフォルダー。プロジェクトなら解析と同じ `audio.wav` を使う |
| `--models` | 比べるモデル。既定は重みを準備済みのすべて |
| `--start` / `--duration` | 比べる区間（秒）。既定は曲全体 |
| `--reference-vocals` | 正解のボーカルWAV。指定するとSDRを計算する |
| `--batch-size` | RoFormerの推論バッチ数。GPUメモリが足りないときに下げる |
| `--out` | 出力先。既定は `test-results/separation/<曲名>-<日時>/` |

出力先には、比べた区間の `mix.wav`、モデルごとのフォルダーにある `vocals.wav` と `instrumental.wav`、結果表の `report.md` と `report.json` が入ります。伴奏はどのモデルでもミックスからボーカルを引いて作ります。htdemucs_ft の4分離は `htdemucs_ft/stems/` に残ります。

## 結果の見方

正解のボーカルがない曲では、数値だけでは優劣を決められません。`vocals.wav` ではハイハットやギターの残り、`instrumental.wav` ではボーカルの消え残りを聴いてください。処理秒数とGPUメモリのピークは、15分以内の解析に収まるかを判断するために記録しています。処理秒数にはモデルの読み込みを含み、CUDAの初期化は含みません。

SDRはMVSEPやMSSTと同じ式で計算します。参照には、ミックスを作ったときのボーカルトラックを同じ長さの44.1 kHzステレオWAVで書き出したものを使ってください。マスタリング後の2mixと組み合わせると参照と一致しないので、値が低く出ます。

結果は `test-results/` に出力します。実曲の結果や分離した音声はGitに追加しないでください。

## ライセンス

2026年10月25日に配布元で確認した内容です。

| 対象 | 配布元 | 確認できた内容 |
| --- | --- | --- |
| htdemucs_ft（基準） | facebookresearch/demucs | MIT |
| MSSTのコード | ZFTurbo/Music-Source-Separation-Training | MIT |
| BS-RoFormer viperx ep_317（比較対象） | TRvlvr/model_repo のリリース | LICENSEファイルがなく、リリースにも記載がない |
| Mel-Band RoFormer Kimberley Jensen（比較対象） | Hugging Face KimberleyJSN/melbandroformer | モデルカードに license: mit。GitHub側のリポジトリにはLICENSEファイルがない |
| BS-RoFormer viperx ep_368、aufr33とviperxのカラオケ用Mel-Band | TRvlvr/model_repo のリリース | 記載なし |
| becruily版Mel-Band、unwa版Kim改良、Gabox版 | Hugging Face | ライセンスのタグもREADMEもない |
| anvuew版の残響除去Mel-Band | Hugging Face | GPL-3.0 |
| ZFTurbo配布の重み（SCNet、BS-Mamba2、53分離など） | MSSTのリリース | リポジトリはMITだが、重みについての個別の記載はない |
| python-audio-separator、lucidrains/BS-RoFormer | GitHub | MIT（コードのみ。重みは含まない） |

ライセンスの記載がない重みは、作者の確認が取れるまで、インストーラーへの同梱やアプリの初回セットアップでの自動取得には使いません。
