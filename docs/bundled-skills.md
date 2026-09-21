# 同梱スキル

開発と文章の執筆・編集に使うスキルを `.agents/skills/` に実ファイルとして保存する。
サブモジュールや個人環境へのリンクは使わず、このリポジトリだけで参照できる。
文章スキルには実行コードや文章lintはなく、Gitフックで文体を自動採点する機能はない。
適用対象はAGENTS.mdで指定する。

| スキル | 取得元 | 固定コミット | ライセンス |
| --- | --- | --- | --- |
| stop-ai-slop-jp | https://github.com/iKora128/stop-ai-slop-jp | e09d32796f253a62693885757cea484c275d06f2 | MIT |
| stop-slop | https://github.com/hardikpandya/stop-slop | 8da1f030185bdfe8471220585162991eaeb970e9 | MIT |

文章スキルの取得日: 2026-09-21。各配布元のSKILL.md、references、README、CHANGELOG、LICENSEを保持している。
上流の本文は変更していない。著作権表示はそれぞれのLICENSEに含まれる。

更新時は上流コミットを指定して別の一時ディレクトリへ取得し、差分を確認する。
採用するファイルを同梱先へ反映し、この表のコミットを更新して一緒にコミットする。
参照ファイルが揃っていることと `npm run check` の成功を確認する。

## clean-code

2026-09-21にローカルの `$CODEX_HOME/skills/clean-code` からv3.0.0を同梱した。
`SKILL.md`、`references/`、`scripts/`、`assets/`を変更せず保存している。
取得元URLと上流コミットはローカル版に記録がなく、未確認。
`SKILL.md`のライセンス表記はMITだが、独立したLICENSEファイルは取得元に含まれていない。
同梱した各ファイルのSHA-256と取得情報は `.agents/skills/clean-code/provenance.json` に記録する。

補助PythonスクリプトとGitフックのサンプルは参照用に保持する。既存のGitフックと品質ゲートを継続して使い、同梱したフックの自動導入は行わない。
更新時は取得元・バージョン・差分を確認し、参照資料を含む一式とハッシュ記録を更新する。
ローカル版から更新する場合も、上流コミットが確認できなければ未確認と記録する。
