# リリース

[READMEへ戻る](../README.md) · [開発環境と検証](development.md)

`.github/workflows/release.yml`でOS別のインストーラーを作り、GitHub Releasesへ公開します。
通常のブランチへのpushでは公開しません。

## ビルド対象

| OS | アーキテクチャ | GitHub runner | 配布形式 |
| --- | --- | --- | --- |
| Windows | x64 | windows-2022 | NSIS `.exe` |
| macOS | Apple Silicon | macos-15 | `.dmg` |
| macOS | Intel | macos-15-intel | `.dmg` |
| Linux | x64 | ubuntu-22.04 | `.deb`、`.AppImage` |

Windows / LinuxのARM版、iOS、Androidはこのワークフローの対象外です。
macOSとLinuxにはOS別のTauri設定を用意し、macOS用のICNSは既存のPNGからTauri CLIで生成しています。

**解析機能はWindows向けです。** 現在のアプリはPowerShellによるセットアップとWindowsのPython配置を使用しています。
macOS・Linux版は実験的なUIビルドとして配布し、セットアップ・解析が未対応であることをリリース本文にも記載します。
全OSでの解析を提供するには、Python環境の作成・検出、モデル依存、プロセス識別、保存先の移植と実機検証が必要です。

## 公開せずに確認する

GitHubのActionsから `Release` → `Run workflow` を選び、対象ブランチを指定します。
全チェックと4種類のビルドを実行し、成功すると `verified-release-assets` にインストーラー5本と `SHA256SUMS` を保存します。
保存期間は14日間です。手動実行ではタグを選んだ場合もReleaseを公開しません。

ビルドは解析モデルやユーザーの音源を取得しません。
Windowsの共通チェックは `.github/workflows/check.yml` を呼び出し、合成音と軽量なPython依存で実行します。

## タグで公開する

1. `package.json`、`package-lock.json`のルート、`src-tauri/tauri.conf.json`、`src-tauri/Cargo.toml`のバージョンを揃えます。npmとCargoのlockも更新してください。
2. `docs/release-notes.md`をそのリリースの説明に更新し、変更をコミット・pushします。
3. 手動ビルドで配布物を確認した後、同じコミットにバージョンタグを付けてpushします。

例として、バージョンが `0.1.0` の場合は次の操作です。

```powershell
git tag -a v0.1.0 -m "hodomia v0.1.0"
git push origin v0.1.0
```

`v*`タグのpushで起動し、タグとnpm・Tauri・Cargoのバージョンが一致しなければビルド前に失敗します。
`v0.2.0-beta.1`のようなタグはGitHubのPre-releaseとして公開します。バージョンのbuild metadata（`+...`）は使用しません。

全チェックと全OSのビルドが成功してから、配布物の不足・空ファイル・名前の重複を検査し、SHA-256を計算します。
Releaseは下書きとして作り、全ファイルのアップロードが成功した後で公開します。
書き込み権限はこの公開ジョブだけに付与し、認証にはGitHubが発行する `GITHUB_TOKEN` を使います。独自のPATは不要です。

## 失敗時

チェックやビルドが失敗した場合、Releaseは作成しません。修正をコミットして新しいバージョンで再実行してください。
一時的なrunnerやダウンロードの失敗なら、同じ実行を再実行できます。
アップロード中に失敗した場合は下書きが残ることがあります。その下書きを確認・削除してから再実行してください。
公開済みのReleaseを同じタグで上書きする処理はありません。配布済みバイナリを変更する場合はバージョンを上げます。

## 署名

この構成は署名用シークレットを必要としません。Windowsは未署名、macOSはad-hoc署名で、公証は行いません。
一般配布向けの証明書署名を追加する場合は、証明書と必要なシークレットを準備してワークフローを拡張してください。
Appleの署名・公証設定は[Tauriの公式手順](https://v2.tauri.app/distribute/sign/macos/)を参照してください。

ワークフローの構成は[TauriのGitHub Actionsガイド](https://v2.tauri.app/distribute/pipelines/github/)と[GitHubのrunner一覧](https://docs.github.com/en/actions/reference/runners/github-hosted-runners)を参照しています。
