使うOSに合わせて、下のAssetsからファイルをダウンロードしてください。

| ファイル | 対象 |
| --- | --- |
| `*x64-setup.exe` | Windows x64、NSISインストーラー |
| `*aarch64.dmg` | macOS、Apple Silicon |
| `*x64.dmg` | macOS、Intel |
| `*amd64.deb` | Linux x64、Debian / Ubuntu |
| `*amd64.AppImage` | Linux x64、AppImage |

Apple Silicon搭載Macで解析環境のセットアップと音源解析を利用できるようにしました。Mac上でPython依存のインストールと解析コードのテストを確認しています。Intel MacとLinux版は実験的なUIビルドで、解析は利用できません。

WindowsとApple Silicon搭載Macではインストール後にhodomiaを起動し、「初回セットアップ」を実行してください。
事前にコマンドとして呼び出せるuvとGitを用意し、ネット接続と数十GBの空き容量を確保してください。
モデルはこのセットアップ時に取得し、その後の解析はローカルで実行します。[セットアップの手順](https://github.com/tobyapi/hodomia/blob/main/docs/development.md#開発環境の準備)

LinuxのAppImageは、ダウンロード後に実行権限を付けて起動してください。

Windows版は署名なし、macOS版はad-hoc署名のみでAppleの公証は行っていません。
OSによる発行元の確認はできず、起動時に警告が出る場合があります。

配布ファイルのSHA-256は `SHA256SUMS` に記載しています。
[使い方](https://github.com/tobyapi/hodomia/blob/main/docs/usage.md)と[配布版の制限](https://github.com/tobyapi/hodomia/blob/main/docs/releases.md)も確認してください。
