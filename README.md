# Adjust Platform Report Downloader

## 概要
このツールは、Adjust管理画面から自動的にレポートをダウンロードするバッチ処理プログラムです。
複数アカウントの処理、ヘッドレス実行、詳細なロギング、および設定の外部化に対応しています。
ネットワークドライブに配置され、タスクスケジューラによって毎日自動実行される環境を想定しています。

## ディレクトリ構成

adjust_batch/
├── adjust_playwright_batch.py  ← メインスクリプト
├── config.ini                  ← 設定ファイル
├── README.md                   ← このファイル
├── requirements.txt            ← 依存ライブラリリスト
├── GAC_adjust管理画面情報.xlsx  ← アカウント情報とレポート設定
└── log/                        ← ログディレクトリ
    ├── bot_20250505.log        ← 実行ログ（JSON形式）
    └── failed_20250505.csv     ← 失敗した行一覧


## 前提条件
- Python 3.10 以上
- Playwright
- pandas, openpyxl, configparser などの依存ライブラリ
- ネットワークドライブへのアクセス権限

## インストール

# 依存ライブラリのインストール
pip install -r requirements.txt

# Playwright のインストール
playwright install chromium


requirements.txt には以下のライブラリが含まれています：

playwright==1.39.0
pandas==2.0.3
openpyxl==3.1.2
configparser==5.3.0
python-dateutil==2.8.2
pytz==2023.3


## 使用方法

### 基本的な実行
python adjust_playwright_v4.py


### 引数オプション
- `--config`: 設定ファイルのパス（デフォルト: config.ini）
- `--date`: 処理対象日（YYYYMMDD形式、デフォルト: 本日）
- `--headless`: ヘッドレスモードで実行（デフォルト: True）


# 例: 特定の日付でヘッドレス実行
adjust_playwright_v4.py --date 20250501

# 例: 別の設定ファイルを使用
adjust_playwright_v4.py --config my_config.ini

# 例: ヘッドレスモードを無効にして実行（デバッグ時）
adjust_playwright_v4.py --headless False


### 設定ファイル（config.ini）
- `excel_path`: Excelファイルのパス（ベースディレクトリからの相対パス）
- `output_path`: 出力先ディレクトリ（ベースディレクトリからの相対パス）
- `timeout`: 通常のタイムアウト設定（秒）
- `long_timeout`: 長いタイムアウト設定（秒）
- `sleep_time_short`: 短い待機時間（秒）
- `sleep_time_long`: 長い待機時間（秒）

### Excelファイル形式
GAC_adjust管理画面情報.xlsx には以下のシートが必要です：
- `リスト`: アカウント情報を含むシート
  - 必要なカラム: `ID`, `PASS`, `広告主`, `取得期間`, `ファイル名`
  - `取得期間` には「今月」または他の値を指定（「今月」の場合は this-month_report、それ以外は last-month_report を選択）

## ログ出力
- JSON形式のログファイル: `log/bot_YYYYMMDD.log`
- 失敗したアカウント一覧: `log/failed_YYYYMMDD.csv`

## ログ出力例

{"timestamp": "2025-05-05 06:00:00,123", "level": "INFO", "message": "開始: 2025-05-05 06:00:00"}
{"timestamp": "2025-05-05 06:00:10,456", "level": "INFO", "message": "アカウント: test1@example.com → ログイン成功"}
{"timestamp": "2025-05-05 06:00:20,789", "level": "INFO", "message": "広告主選択: AAA_Corp → 成功"}
{"timestamp": "2025-05-05 06:00:30,012", "level": "INFO", "message": "レポート this-month_report → クリック成功"}
{"timestamp": "2025-05-05 06:00:40,345", "level": "INFO", "message": "ファイル保存成功: 20250505/AAA_Corp.csv"}
{"timestamp": "2025-05-05 06:00:50,678", "level": "ERROR", "message": "アカウント: test2@example.com → ログイン失敗（Invalid credentials）"}
{"timestamp": "2025-05-05 06:01:00,901", "level": "INFO", "message": "全体処理完了。成功: 4件 / 失敗: 1件"}


## 自動実行の設定例（ネットワークドライブ環境）

### Windows (タスクスケジューラ)
1. タスクスケジューラを開く
2. 「基本タスクの作成」をクリック
3. タスク名に「Adjust Report Downloader」などを入力
4. トリガーに「毎日」を選択し、実行時間を設定（例: 午前6:00）
5. アクションに「プログラムの開始」を選択
6. 以下の設定を行う:
   - プログラム: `C:\path\to\Python\python.exe`
   - 引数: `\\NetworkDrive\path\to\adjust_batch\adjust_playwright_batch.py --headless`
   - 開始: `\\NetworkDrive\path\to\adjust_batch`
7. 「OK」をクリックしてタスクを保存


## トラブルシューティング

### よくある問題と解決策

1. **ネットワークドライブアクセスエラー**
   - タスクスケジューラの実行アカウントに適切なアクセス権があることを確認
   - UNCパス（\\server\share\）を使用してアクセス
   - net use コマンドを使用してドライブをマッピング

2. **Playwrightのブラウザ起動エラー**
   - `playwright install chromium` が実行されていることを確認
   - サービスアカウントでの実行時には、システムアカウントにブラウザがインストールされていることを確認

3. **タイムアウトエラーが頻発する場合**
   - config.ini のタイムアウト値を増加
   - ネットワーク接続を確認
   - 対象サイトの応答時間が遅い可能性を検討

4. **CSVファイルが正常にダウンロードされない**
   - ダウンロード先のフォルダに書き込み権限があることを確認
   - download.save_as() 呼び出し後にファイルの存在確認を追加

## メンテナンス

- ログファイルは自動的に日付ごとに作成されますが、定期的に古いログファイルを削除することを推奨します
- Playwrightのバージョンアップにより、セレクタが変更される可能性があります。その場合はスクリプトを更新してください
- 定期的にExcelファイル内のアカウント情報を確認し、必要に応じて更新してください

## 注意事項
- ヘッドレスモードではブラウザUIが表示されません。デバッグ時はヘッドレスモードを無効にしてください。
- アカウント情報や出力ファイルパスは適切に管理してください。
- 一部の処理では、サイトの仕様変更によって調整が必要になる場合があります。
- ネットワークドライブでの運用時は、ネットワーク遅延を考慮したタイムアウト設定を行ってください。
