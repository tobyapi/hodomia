# 音源分離の比較

[開発環境と検証へ戻る](development.md)

アプリの分離（ボーカルはKim版Mel-Band RoFormer、ドラムとベースはZFTurbo版4分離BS-RoFormer ep_17）と、ほかのRoFormer系やSCNetの分離モデルを手元の曲で比べる開発用ツールです。比較用のPython環境は解析環境と分け、`<runtime>/separation-compare/` に作ります。

アプリは2026年10月まで htdemucs_ft を使っていました。重みが研究目的に限られている（[demucs#327](https://github.com/facebookresearch/demucs/issues/327)）ため置き換え、このツールからも外しました。置き換えを決めたときの比較は[検証記録](verification.md#分離モデルの置き換え)にあります。

分離結果を比べる `compare.py` と、その出力から曲構成と歌詞を推定し直して基準と比べる `downstream.py` の2段に分かれています。

## 準備

基準のアプリの分離は解析環境のモデルとPythonをそのまま使うので、先に `npm run setup:analysis` を済ませておきます。続けて次を実行します。ネット接続が必要なのはこの手順だけです。

```powershell
uv run --no-project --python 3.11 scripts/separation/prepare.py
```

このコマンドはPython 3.11の別環境を作り、[MSST](https://github.com/ZFTurbo/Music-Source-Separation-Training) を固定コミットで取得し、候補モデルの重みをダウンロードします。重みはSHA-256で照合し、一致しないファイルは残しません。MVSep 53分離の重みは1.4 GBあります。

ライセンスの記載も作者の表明もない重み（viperx版のBS-RoFormer）は、`--include-unlicensed` を付けたときだけ取得します。付けた場合も、手元での評価に使う前提です。

## 分離の比較

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
| `--batch-size` | RoFormerとSCNetの推論バッチ数。GPUメモリが足りないときに下げる |
| `--out` | 出力先。既定は `test-results/separation/<曲名>-<日時>/` |

出力先には、比べた区間の `mix.wav`、モデルごとのフォルダーにある `vocals.wav` と `instrumental.wav`、結果表の `report.md` と `report.json` が入ります。伴奏はどのモデルでもミックスからボーカルを引いて作ります。

アプリの分離と4分離できるモデル（ZFTurbo版BS-RoFormer、SCNet XL IHF、MVSep 53分離）は、解析と同じ名前のbass・drums・other・vocalsを `stems/` に保存します。MVSep 53分離にはotherがないので、ミックスからほかの3つを引いた残りをotherにします。

ボーカル専用のKim版Mel-Band RoFormerとSCNet XL IHFを両方選ぶと、組み合わせの行（kim_scnet）も作ります。ボーカルはKim版、ドラムとベースはSCNet XL IHFのものを使い、otherはミックスから3つを引いた残りです。Kim版とZFTurbo版4分離の組み合わせはアプリの分離と同じなので、行を作りません。処理秒は2つのモデルの合計、GPUメモリは大きいほうを載せます。

## 曲構成と歌詞への影響

`compare.py` の出力フォルダーを渡すと、各モデルのステムでAll-In-Oneの曲構成推定とWhisperの書き起こしをやり直し、アプリの分離の結果と比べます。All-In-OneとWhisperは解析環境にあるので、解析環境のPythonで実行します。

```powershell
.runtime/venv/Scripts/python.exe scripts/separation/downstream.py "test-results/separation/<曲名>-<日時>"
```

| 引数 | 内容 |
| --- | --- |
| フォルダー | `compare.py` の出力先 |
| `--mode` | 歌詞解析のモード。`japanese`（既定）か `multilingual` |

結果は同じフォルダーの `downstream.md` と `downstream.json` に入ります。モデルごとのフォルダーには、Whisperの `transcript.json` と時刻合わせの `alignment.json` が残ります。ボーカルの音声が同じもの（Kim版単体とKim版を使う組み合わせ）は、書き起こしを一度だけ行います。

| 列 | 内容 |
| --- | --- |
| 境界F | 区間の始まりと終わりが、基準と±0.5秒または±3秒以内で一致した割合 |
| 区間名の一致率 | 曲の長さのうち、基準と同じ区間名（サビ、ヴァースなど）が付いた時間の割合 |
| 歌詞CER | 基準の書き起こしに対する文字誤り率。NFKC正規化と記号の除去をしてから数える |
| 発話なし警告 | Whisperの発話なしの確率が0.6を超えた行の数 |
| 活動IoU | 分離音声の相対音量から判定した、ステムが鳴っている時間の重なり |

どの値も基準とのずれで、正しさは示しません。Whisperは確信度が低い区間を温度を上げて再試行するので、同じボーカルでも書き起こしが変わることがあります。差の大きさは、基準を2回実行したときのずれと比べて読んでください。歌詞CERが大きいときは、どちらの書き起こしが歌詞に近いかを `transcript.json` で読み比べてください。

## 結果の見方

正解のボーカルがない曲では、数値だけでは優劣を決められません。`vocals.wav` ではハイハットやギターの残り、`instrumental.wav` ではボーカルの消え残りを聴いてください。処理秒数とGPUメモリは、15分以内の解析に収まるかを判断するために記録しています。処理秒数にはモデルの読み込みを含み、CUDAの初期化は含みません。数十秒の区間では読み込みが処理秒の大半を占めるので、速さは曲全体で比べてください。

GPUピークはテンソルが使った量、GPU確保はPyTorchがGPUから確保した量です。Windowsでは確保量がGPUの実メモリを超えても止まらず、共有メモリ（メインメモリ）にあふれて処理が何倍も遅くなります。RTX 2080（8 GB）では、SCNet XL IHFは配布設定のバッチ数4だと確保量が7〜9 GBになり、バッチ数1より遅くなりました。`--batch-size 1` で比べてください。MVSep 53分離はバッチ数1でも12〜13 GBを確保し、8 GBのGPUには収まりません。曲全体と足し合わせ用のバッファもGPUに置くので、確保量は曲が長いほど増えます（15分の曲でKim版3.2 GB、ZFTurbo版4分離4.8 GB）。

SDRはMVSEPやMSSTと同じ式で計算します。参照には、ミックスを作ったときのボーカルトラックを同じ長さの44.1 kHzステレオWAVで書き出したものを使ってください。マスタリング後の2mixと組み合わせると参照と一致しないので、値が低く出ます。

結果は `test-results/` に出力します。実曲の結果や分離した音声はGitに追加しないでください。

## ライセンス

2026年10月25日に配布元で確認した内容です。

| 対象 | 配布元 | 確認できた内容 |
| --- | --- | --- |
| htdemucs_ft（2026年10月までの解析） | facebookresearch/demucs | コードはMIT。重みは研究目的でのみ提供していると作者が回答（[demucs#327](https://github.com/facebookresearch/demucs/issues/327)） |
| MSSTのコード | ZFTurbo/Music-Source-Separation-Training | MIT |
| BS-RoFormer ZFTurbo 4分離 ep_17 | MSSTのリリース v1.0.12 | 作者がMITで公開したと回答（[MSST#254](https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/254)）。学習データはMUSDB18HQだけ |
| SCNet XL IHF ep_36 | MSSTのリリース v1.0.15 | 作者が自作の重みはMITと回答（[MSST#245](https://github.com/ZFTurbo/Music-Source-Separation-Training/issues/245)）。このファイルを名指しした確認依頼（10月12日）には回答がない。学習データはMUSDB18だけ |
| MVSep Mega 53分離 v1 | MSSTのリリース v1.0.21 | 作者がMITで公開したと回答（MSST#245）。学習音源の著作権は持っていないと明記 |
| Mel-Band RoFormer Kimberley Jensen | Hugging Face KimberleyJSN/melbandroformer | モデルカードに license: mit。GitHub側のリポジトリにはLICENSEファイルがない |
| MUSDB18-HQ（学習データ） | Zenodo | 教育目的での提供。商用利用には各曲の権利者の許可が必要。一部はCC BY-NC-SA |
| BS-RoFormer viperx ep_317、ep_368、aufr33とviperxのカラオケ用Mel-Band | TRvlvr/model_repo のリリース | LICENSEファイルがなく、リリースにも記載がない |
| becruily版Mel-Band、unwa版Kim改良、Gabox版 | Hugging Face | ライセンスのタグもREADMEもない |
| anvuew版の残響除去Mel-Band | Hugging Face | GPL-3.0 |
| python-audio-separator、lucidrains/BS-RoFormer | GitHub | MIT（コードのみ。重みは含まない） |

ZFTurboは、どの回答でも学習データの権利までは保証できないと書いています。MUSDB18だけで学習した重みを商用で使ってよいかは、重みのライセンスとは別に利用者が判断することになります。

ライセンスの記載も作者の表明もない重みは、インストーラーへの同梱やアプリの初回セットアップでの自動取得には使いません。
