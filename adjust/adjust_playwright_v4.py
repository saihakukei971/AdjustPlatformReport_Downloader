#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Decompiled with PyLingual (https://pylingual.io)
# Internal filename: adjust_playwright_v3.py
# Bytecode version: 3.11a7e (3495)
# Source timestamp: 1970-01-01 00:00:00 UTC (0)

"""\n※ 本コードは Selenium 版の処理内容を Playwright に置き換え、\n    各アカウント毎に新規のブラウザセッションを作成して作業を行う例です。\n"""
from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError
import os
import sys
import pandas as pd
import glob
import shutil
import logging
import json
import traceback
import random
import datetime
import argparse
import configparser
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
import csv
from typing import Dict, List, Any, Optional

def move_and_rename_latest_csv(destination_folder, new_file_name):
    """\n    （※Playwrightではダウンロードイベントで直接保存可能なため、必ずしも使用しなくてもよい）\n    デフォルトのダウンロードフォルダから最新の CSV ファイルを指定フォルダに移動し、名前を変更する。\n    """
    if os.name == 'nt':
        download_folder = os.path.expanduser('~\\Downloads')
    else:
        download_folder = os.path.expanduser('~/Downloads')
    list_of_files = glob.glob(os.path.join(download_folder, '*.csv'))
    if not list_of_files:
        print('ダウンロードフォルダにCSVファイルが見つかりません。')
        return
    latest_file = max(list_of_files, key=os.path.getctime)
    new_file_path = os.path.join(destination_folder, new_file_name)
    try:
        shutil.move(latest_file, new_file_path)
        print(f'ファイルを {new_file_path} に移動し、名前を変更しました。')
    except Exception as e:
        print(f'ファイルの移動中にエラーが発生しました: {e}')

class AdjustReportDownloader:
    def __init__(self, config_path='config.ini', target_date=None, headless=True):
        """初期化処理"""
        if getattr(sys, 'frozen', False):
            self.base_dir = os.path.dirname(sys.executable)
        else:
            self.base_dir = os.path.dirname(os.path.abspath(__file__))

        print('プログラムが開始しました。')

        # 設定の読み込み
        self.config = self._load_config(config_path)

        # 日付処理
        self.target_date = target_date or datetime.date.today()
        self.target_date_str = self.target_date.strftime('%Y%m%d')

        # ログ設定
        self._setup_logging()

        # 実行設定
        self.headless = headless
        self.timeout = int(self.config.get('Settings', 'timeout', fallback='60'))
        self.long_timeout = int(self.config.get('Settings', 'long_timeout', fallback='180'))
        self.sleep_time_short = int(self.config.get('Settings', 'sleep_time_short', fallback='3'))
        self.sleep_time_long = int(self.config.get('Settings', 'sleep_time_long', fallback='5'))

        # 失敗記録用
        self.error = False
        self.failed_accounts = []
        self.success_count = 0
        self.failed_count = 0

    def _load_config(self, config_path):
        """設定ファイルを読み込む"""
        config = configparser.ConfigParser()
        config_file = os.path.join(self.base_dir, config_path)
        if not os.path.exists(config_file):
            # デフォルト設定を作成
            config['Settings'] = {
                'excel_path': 'GAC_adjust管理画面情報.xlsx',
                'output_path': 'output',
                'timeout': '60',
                'long_timeout': '180',
                'sleep_time_short': '3',
                'sleep_time_long': '5'
            }
            with open(config_file, 'w', encoding='utf-8') as f:
                config.write(f)
            self.logger.info(f'設定ファイルが存在しないため、デフォルト設定を作成しました: {config_file}')

        config.read(config_file, encoding='utf-8')
        return config

    def _setup_logging(self):
        """ログ設定を初期化する"""
        log_directory = 'log'
        log_file = f'bot_{self.target_date_str}.log'
        failed_log = f'failed_{self.target_date_str}.csv'

        log_directory_path = os.path.join(self.base_dir, log_directory)
        if not os.path.exists(log_directory_path):
            os.makedirs(log_directory_path)

        log_file_path = os.path.join(log_directory_path, log_file)
        failed_log_path = os.path.join(log_directory_path, failed_log)

        # JSONフォーマッタを設定
        class JsonFormatter(logging.Formatter):
            def format(self, record):
                log_data = {
                    'timestamp': self.formatTime(record),
                    'level': record.levelname,
                    'message': record.getMessage(),
                }
                if record.exc_info:
                    log_data['exception'] = self.formatException(record.exc_info)
                return json.dumps(log_data, ensure_ascii=False)

        # ルートロガーの設定
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.INFO)

        # 既存のハンドラをクリア
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)

        # ファイルハンドラ (JSON形式)
        json_handler = logging.FileHandler(log_file_path, encoding='utf-8')
        json_handler.setFormatter(JsonFormatter())
        self.logger.addHandler(json_handler)

        # コンソールハンドラ (通常形式)
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.logger.addHandler(console_handler)

        # 失敗CSVの準備
        self.failed_log_path = failed_log_path
        if not os.path.exists(self.failed_log_path):
            with open(self.failed_log_path, 'w', encoding='utf-8-sig', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['アカウント', 'エラー内容', '日時'])

    def _append_failed_account(self, account, error_message):
        """失敗したアカウント情報をCSVに追記する"""
        with open(self.failed_log_path, 'a', encoding='utf-8-sig', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                account,
                error_message,
                datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ])
        self.failed_accounts.append((account, error_message))
        self.failed_count += 1

    def run(self):
        """メイン処理を実行する"""
        self.logger.info(f'開始: {datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

        # Excelファイルの読み込み
        excel_path = os.path.join(self.base_dir, self.config.get('Settings', 'excel_path'))
        try:
            data = pd.read_excel(excel_path, sheet_name='リスト')
            output_path = self.config.get('Settings', 'output_path')
            self.logger.info('正常にExcelファイルが読み込まれました')
        except Exception as e:
            self.logger.error(f'Excelファイルの読み込みに失敗しました: {e}')
            self.logger.error(traceback.format_exc())
            return

        # 日付フォルダの作成
        date_folder = os.path.join(self.base_dir, output_path, self.target_date_str)
        os.makedirs(date_folder, exist_ok=True)

        # Playwrightでの処理
        with sync_playwright() as p:
            # 各アカウントの処理
            for index, row in data.iterrows():
                account = str(row['ID'])
                self.logger.info(f'アカウント処理開始: {account}')

                browser = None
                context = None
                try:
                    # ユーザーエージェントをランダムに選択
                    user_agents = [
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
                        'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
                    ]
                    ua = random.choice(user_agents)

                    # ブラウザを起動
                    browser = p.chromium.launch(
                        headless=self.headless,
                        args=[
                            '--disable-extensions',
                            '--disable-gpu',
                            '--blink-settings=imagesEnabled=false',
                            '--disable-blink-features=AutomationControlled'
                        ]
                    )

                    # コンテキストを作成
                    context = browser.new_context(user_agent=ua, accept_downloads=True)
                    page = context.new_page()

                    # ログイン処理
                    url = 'https://suite.adjust.com/login?'
                    page.goto(url)
                    page.wait_for_selector('input[name=\'email\']', timeout=self.long_timeout * 1000)
                    self.random_sleep(self.sleep_time_short, self.sleep_time_long)

                    page.fill('input[name=\'email\']', account)
                    page.fill('input[name=\'password\']', str(row['PASS']))
                    page.press('input[name=\'password\']', 'Enter')

                    # ダッシュボード表示を待機
                    page.wait_for_selector('[aria-label=\"sidepanel-account-action-btn\"]', timeout=self.long_timeout * 1000)
                    self.random_sleep(self.sleep_time_short, self.sleep_time_long)
                    self.logger.info(f'アカウント: {account} → ログイン成功')

                    # 広告主選択処理
                    if pd.notna(row['広告主']):
                        advertiser = str(row['広告主'])
                        self.logger.info(f'広告主選択: {advertiser} → 試行')

                        try:
                            page.click('[aria-label=\"sidepanel-account-action-btn\"]')
                            page.wait_for_selector('[role=\"menu\"] > li', timeout=1000)
                            self.random_sleep(self.sleep_time_short, self.sleep_time_long)

                            page.locator('[role=\"menu\"] > li').nth(1).click()
                            page.wait_for_selector('input.ComboBox__input', timeout=1000)
                            page.fill('input.ComboBox__input', advertiser)
                            self.random_sleep(self.sleep_time_short, self.sleep_time_long)

                            page.press('input.ComboBox__input', 'Enter')
                            self.random_sleep(self.sleep_time_short, self.sleep_time_long)

                            self.logger.info(f'広告主選択: {advertiser} → 成功')
                        except Exception as e:
                            error_message = f"広告主: {advertiser} が見つかりませんでした: {e}"
                            self.logger.error(error_message)
                            self.logger.error(traceback.format_exc())
                            self._append_failed_account(account, error_message)
                            continue

                    # レポート画面へ移動
                    page.click('[data-testid=\"navigate-to-my-reports\"]')
                    self.random_sleep(self.sleep_time_short, self.sleep_time_long)
                    page.wait_for_selector('div[role=\"table\"]', state='visible', timeout=5000)

                    # レポートタイプの決定
                    report_type = 'this-month_report' if row['取得期間'] == '今月' else 'last-month_report'
                    report_selector = f'xpath=//a[@data-testid=\'dash_exp-row_report_title\'][.//div[contains(text(), \'{report_type}\')]]'
                    self.logger.info(f'レポート {report_type} → 検索')

                    # レポートの検索とクリック
                    container = page.locator('div[role=\"table\"]')
                    scroll_attempts = 0
                    MAX_SCROLL_ATTEMPTS = 20
                    report_found = False

                    while scroll_attempts < MAX_SCROLL_ATTEMPTS:
                        try:
                            report_link = page.wait_for_selector(report_selector, state='visible', timeout=2000)
                            if report_link:
                                report_link.click()
                                report_found = True
                                self.logger.info(f'レポート {report_type} → クリック成功')
                                break
                        except Exception:
                            container.evaluate('element => { element.scrollTop += 500; }')
                            page.wait_for_timeout(1000)
                            scroll_attempts += 1

                    if not report_found:
                        error_message = f'20回スクロールしても要素 \'{report_type}\' が見つかりませんでした'
                        self.logger.error(error_message)
                        self._append_failed_account(account, error_message)
                        continue

                    self.random_sleep(self.sleep_time_short, self.sleep_time_long)

                    # ダウンロードボタンの待機
                    page.wait_for_selector('[data-testid=\"Download-icon-wrapper\"]', timeout=self.long_timeout * 1000)

                    # ファイルのダウンロード
                    max_retries = 3
                    download_success = False

                    for attempt in range(max_retries):
                        try:
                            with page.expect_download(timeout=30000) as download_info:
                                page.click('[data-testid=\"Download-icon-wrapper\"]')
                                self.random_sleep(self.sleep_time_short, self.sleep_time_long)

                                download = download_info.value
                                new_file_name = f"{row['ファイル名']}.csv"
                                new_file_path = os.path.join(date_folder, new_file_name)

                                # ダウンロードの保存
                                download.save_as(new_file_path)

                                # ファイルの存在確認
                                if os.path.exists(new_file_path):
                                    download_success = True
                                    self.logger.info(f'ファイル保存成功: {self.target_date_str}/{new_file_name}')
                                    self.success_count += 1
                                    break
                                else:
                                    self.logger.warning(f'ファイルが保存されませんでした: {new_file_path}')
                        except Exception as e:
                            self.logger.warning(f'ファイルのダウンロード試行中にエラー: {e} (試行回数: {attempt + 1})')
                            if attempt < max_retries - 1:
                                self.logger.info('5秒待機してからリトライします...')
                                self.random_sleep(5, 5)
                            else:
                                error_message = f'ファイルのダウンロードに失敗しました: {e}'
                                self.logger.error(error_message)
                                self.logger.error(traceback.format_exc())
                                self._append_failed_account(account, error_message)
                                self.error = True

                    if download_success:
                        self.logger.info(f'アカウント処理完了: {account}')

                except Exception as e:
                    error_message = f'アカウント処理中にエラーが発生しました: {e}'
                    self.logger.error(error_message)
                    self.logger.error(traceback.format_exc())
                    self._append_failed_account(account, error_message)
                    self.error = True

                finally:
                    # ブラウザの終了
                    try:
                        if context:
                            context.close()
                        if browser:
                            browser.close()
                    except Exception as close_err:
                        self.logger.error(f'ブラウザ終了中にエラーが発生しました: {close_err}')

        # 処理結果のサマリー
        self.logger.info(f'全体処理完了。成功: {self.success_count}件 / 失敗: {self.failed_count}件')

        if self.error:
            self.logger.info('動作が異常終了しました')
            print('動作が異常終了しました')
        else:
            self.logger.info('動作が正常に終了しました')
            print('動作が正常に終了しました')

    def random_sleep(self, min_seconds, max_seconds):
        """ランダムな時間だけ待機する"""
        sleep_time = random.uniform(min_seconds, max_seconds)
        from time import sleep
        sleep(sleep_time)


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(description='Adjust Platform Report Downloader')
    parser.add_argument('--config', default='config.ini', help='設定ファイルのパス')
    parser.add_argument('--date', help='処理対象日 (YYYYMMDD形式)')
    parser.add_argument('--headless', action='store_true', help='ヘッドレスモードで実行')

    args = parser.parse_args()

    # 日付の処理
    target_date = None
    if args.date:
        try:
            target_date = datetime.datetime.strptime(args.date, '%Y%m%d').date()
        except ValueError:
            print('日付の形式が正しくありません。YYYYMMDD形式で指定してください。')
            sys.exit(1)

    # ダウンローダーの実行
    downloader = AdjustReportDownloader(
        config_path=args.config,
        target_date=target_date,
        headless=args.headless
    )
    downloader.run()


if __name__ == "__main__":
    main()