@echo off
REM ====================================================
REM Adjust Platform Report Downloader 自動実行スクリプト
REM ====================================================
REM 作成日: 2025/05/05
REM 
REM このバッチファイルは、ネットワークドライブ上のAdjust Platform
REM バッチ処理を自動実行するためのものです。
REM タスクスケジューラから呼び出すことを想定しています。
REM ====================================================

REM ログ出力の設定
set LOGFILE=%~dp0log\batch_execution_%date:~0,4%%date:~5,2%%date:~8,2%.log
set TIMESTAMP=%date% %time%

REM ログフォルダの作成（存在しない場合）
if not exist "%~dp0log" mkdir "%~dp0log"

REM ログファイルの初期メッセージ
echo %TIMESTAMP% - バッチ処理を開始します。 > "%LOGFILE%"

REM ============================================
REM ネットワークドライブへのアクセス
REM ============================================
echo %TIMESTAMP% - ネットワークドライブへの接続を試みます... >> "%LOGFILE%"

REM ネットワークドライブが既に接続されているかチェック
net use Z: 2>nul
if %ERRORLEVEL% EQU 0 (
    echo %TIMESTAMP% - 既にネットワークドライブZ:が接続されています。切断します... >> "%LOGFILE%"
    net use Z: /delete /y
    if %ERRORLEVEL% NEQ 0 (
        echo %TIMESTAMP% - エラー: ネットワークドライブZ:の切断に失敗しました。 >> "%LOGFILE%"
        goto ERROR_EXIT
    )
)

REM ネットワークドライブに接続
net use Z: \\server\share /user:domain\username password
if %ERRORLEVEL% NEQ 0 (
    echo %TIMESTAMP% - エラー: ネットワークドライブへの接続に失敗しました。(エラーコード: %ERRORLEVEL%) >> "%LOGFILE%"
    goto ERROR_EXIT
)
echo %TIMESTAMP% - ネットワークドライブへの接続に成功しました。 >> "%LOGFILE%"

REM ============================================
REM Pythonのパス確認
REM ============================================
echo %TIMESTAMP% - Pythonのパスを確認しています... >> "%LOGFILE%"
set PYTHON_PATH=C:\Path\to\Python\python.exe

REM Pythonの存在確認
if not exist "%PYTHON_PATH%" (
    echo %TIMESTAMP% - エラー: Python実行ファイルが見つかりません。パスを確認してください: %PYTHON_PATH% >> "%LOGFILE%"
    goto CLEANUP
)
echo %TIMESTAMP% - Python実行ファイルが見つかりました: %PYTHON_PATH% >> "%LOGFILE%"

REM ============================================
REM 実行環境の準備
REM ============================================
REM カレントディレクトリを変更
cd /d Z:\path\to\adjust_batch
if %ERRORLEVEL% NEQ 0 (
    echo %TIMESTAMP% - エラー: 作業ディレクトリへの移動に失敗しました。パスを確認してください。 >> "%LOGFILE%"
    goto CLEANUP
)
echo %TIMESTAMP% - 作業ディレクトリへの移動に成功しました: %CD% >> "%LOGFILE%"

REM 設定ファイルの存在確認
if not exist "config.ini" (
    echo %TIMESTAMP% - エラー: config.iniファイルが見つかりません。 >> "%LOGFILE%"
    goto CLEANUP
)

REM Excelファイルの存在確認
if not exist "GAC_adjust管理画面情報.xlsx" (
    echo %TIMESTAMP% - エラー: GAC_adjust管理画面情報.xlsxファイルが見つかりません。 >> "%LOGFILE%"
    goto CLEANUP
)

REM 出力ディレクトリの作成（存在しない場合）
set OUTPUT_DIR=output
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

echo %TIMESTAMP% - 実行環境の準備が完了しました。 >> "%LOGFILE%"

REM ============================================
REM スクリプトの実行
REM ============================================
echo %TIMESTAMP% - Adjust Platform Report Downloaderの実行を開始します... >> "%LOGFILE%"
echo %TIMESTAMP% - コマンド: %PYTHON_PATH% adjust_playwright_batch.py --headless --date %date:~0,4%%date:~5,2%%date:~8,2% >> "%LOGFILE%"

REM スクリプトの実行
%PYTHON_PATH% adjust_playwright_batch.py --headless --date %date:~0,4%%date:~5,2%%date:~8,2%

REM 実行結果の確認
set EXIT_CODE=%ERRORLEVEL%
if %EXIT_CODE% EQU 0 (
    echo %TIMESTAMP% - スクリプトの実行が成功しました。 >> "%LOGFILE%"
) else (
    echo %TIMESTAMP% - エラー: スクリプトの実行に失敗しました。(エラーコード: %EXIT_CODE%) >> "%LOGFILE%"
)

REM 結果の確認
echo %TIMESTAMP% - 終了コード: %EXIT_CODE% >> "%LOGFILE%"

REM 処理結果の確認：当日のCSVファイルが生成されているか
set TODAY=%date:~0,4%%date:~5,2%%date:~8,2%
set CSV_COUNT=0
for %%F in ("%OUTPUT_DIR%\%TODAY%\*.csv") do set /a CSV_COUNT+=1

echo %TIMESTAMP% - 本日(%TODAY%)生成されたCSVファイル数: %CSV_COUNT% >> "%LOGFILE%"

REM ============================================
REM クリーンアップ処理
REM ============================================
:CLEANUP
echo %TIMESTAMP% - クリーンアップ処理を実行します... >> "%LOGFILE%"

REM ネットワークドライブを切断
echo %TIMESTAMP% - ネットワークドライブの切断を試みます... >> "%LOGFILE%"
net use Z: /delete /y
if %ERRORLEVEL% NEQ 0 (
    echo %TIMESTAMP% - 警告: ネットワークドライブの切断に失敗しました。(エラーコード: %ERRORLEVEL%) >> "%LOGFILE%"
) else (
    echo %TIMESTAMP% - ネットワークドライブの切断に成功しました。 >> "%LOGFILE%"
)

REM 正常終了
echo %TIMESTAMP% - バッチ処理が完了しました。 >> "%LOGFILE%"
exit /b %EXIT_CODE%

REM ============================================
REM エラー終了処理
REM ============================================
:ERROR_EXIT
echo %TIMESTAMP% - エラーが発生したため、処理を中断します。 >> "%LOGFILE%"
exit /b 1