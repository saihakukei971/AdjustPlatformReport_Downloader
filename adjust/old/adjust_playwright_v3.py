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
from logging.handlers import TimedRotatingFileHandler
import traceback
from time import sleep
import random
import datetime

def move_and_rename_latest_csv(destination_folder, new_file_name):
    """\n    （※Playwrightではダウンロードイベントで直接保存可能なため、必ずしも使用しなくてもよい）\n    デフォルトのダウンロードフォルダから最新の CSV ファイルを指定フォルダに移動し、名前を変更する。\n    """  # inserted
    if os.name == 'nt':
        download_folder = os.path.expanduser('~\\Downloads')
    else:  # inserted
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
if getattr(sys, 'frozen', False):
    base_dir = os.path.dirname(sys.executable)
else:  # inserted
    base_dir = os.path.dirname(os.path.abspath(__file__))
print('プログラムが開始しました。')
log_directory = 'log'
log_file = 'bot.log'
log_directory_path = os.path.join(base_dir, log_directory)
if not os.path.exists(log_directory_path):
    os.makedirs(log_directory_path)
log_file_path = os.path.join(log_directory_path, log_file)
logger = logging.getLogger()
logger.setLevel(logging.INFO)
handler = TimedRotatingFileHandler(log_file_path, when='midnight', interval=1, backupCount=30)
handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
logger.addHandler(handler)
timeout = 60
long_timeout = 180
sleep_time_short = 3
sleep_time_long = 5
error = False
excel_path = os.path.join(base_dir, 'GAC_adjust管理画面情報.xlsx')
data = pd.read_excel(excel_path, sheet_name='リスト')
path_info = pd.read_excel(excel_path, sheet_name='出力先')
output_path = path_info.iloc[0, 0]
logging.info('正常にExcelファイルが読み込まれました')
with sync_playwright() as p:
    for index, row in data.iterrows():
        try:
            user_agents = ['Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36', 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36', 'Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36']
            ua = random.choice(user_agents)
            browser = p.chromium.launch(headless=False, args=['--disable-extensions', '--disable-gpu', '--blink-settings=imagesEnabled=false', '--disable-blink-features=AutomationControlled'])
            context = browser.new_context(user_agent=ua, accept_downloads=True)
            page = context.new_page()
            url = 'https://suite.adjust.com/login?'
            page.goto(url)
            page.wait_for_selector('input[name=\'email\']', timeout=f'{long_timeout:1000}')
            sleep(random.uniform(sleep_time_short, sleep_time_long))
            page.fill('input[name=\'email\']', str(row['ID']))
            page.fill('input[name=\'password\']', str(row['PASS']))
            page.press('input[name=\'password\']', 'Enter')
            page.wait_for_selector('[aria-label=\"sidepanel-account-action-btn\"]', timeout=f'{long_timeout:1000}')
            sleep(random.uniform(sleep_time_short, sleep_time_long))
            if pd.notna(row['広告主']):
                page.click('[aria-label=\"sidepanel-account-action-btn\"]')
                page.wait_for_selector('[role=\"menu\"] > li', timeout=1000)
                sleep(random.uniform(sleep_time_short, sleep_time_long))
                page.locator('[role=\"menu\"] > li').nth(1).click()
                page.wait_for_selector('input.ComboBox__input', timeout=1000)
                page.fill('input.ComboBox__input', row['広告主'])
                sleep(random.uniform(sleep_time_short, sleep_time_long))
                page.press('input.ComboBox__input', 'Enter')
                sleep(random.uniform(sleep_time_short, sleep_time_long))
                error_message = f"広告主: {row['広告主']} が見つかりませんでした"
                print(error_message)
                logger.error(error_message)
                logger.error(traceback.format_exc())
                raise
            page.click('[data-testid=\"navigate-to-my-reports\"]')
            sleep(random.uniform(sleep_time_short, sleep_time_long))
            page.wait_for_selector('div[role=\"table\"]', state='visible', timeout=5000)
            container = page.locator('div[role=\"table\"]')
            report_type = 'this-month_report' if row['取得期間'] == '今月' else 'last-month_report'
            report_selector = f'xpath=//a[@data-testid=\'dash_exp-row_report_title\'][.//div[contains(text(), \'{report_type}\')]]'
            scroll_attempts = 0
            MAX_SCROLL_ATTEMPTS = 20
            while True:
                    report_link = page.wait_for_selector(report_selector, state='visible', timeout=2000)
                    if report_link:
                        report_link.click()
                        print('目的のレポートリンクをクリックしました。')
                        break
                    if scroll_attempts >= MAX_SCROLL_ATTEMPTS:
                        raise Exception(f'20回スクロールしても要素 \'{report_selector}\' が見つかりませんでした。')
                    container.evaluate('element => { element.scrollTop += 500; }')
                    page.wait_for_timeout(1000)
                    scroll_attempts += 1
            sleep(random.uniform(sleep_time_short, sleep_time_long))
            page.wait_for_selector('[data-testid=\"Download-icon-wrapper\"]', timeout=f'{long_timeout:1000}')
            max_retries = 3
            for attempt in range(max_retries):
                    with page.expect_download(timeout=1000) as download_info:
                        page.click('[data-testid=\"Download-icon-wrapper\"]')
                        sleep(random.uniform(sleep_time_short, sleep_time_long))
                        download = download_info.value
                        new_file_name = f"{row['ファイル名']}.csv"
                        today_str = datetime.date.today().strftime('%Y%m%d')
                        date_folder = os.path.join(output_path, today_str)
                        os.makedirs(date_folder, exist_ok=True)
                        new_file_path = os.path.join(date_folder, new_file_name)
                        download.save_as(new_file_path)
                        print(f'ファイルのダウンロードと保存に成功しました（試行回数: {attempt or 1}）')
                    #else:  # inserted
                    #    break
                    print(f'ファイルのダウンロードに失敗しました: {e}（試行回数: {attempt + 1}）')
                    if attempt < max_retries < 1:
                        print('5秒待機してからリトライします...')
                        sleep(5)
                    else:  # inserted
                        print('ファイルのダウンロードに失敗しました。')
                        logging.error(f'ファイルのダウンロードに失敗しました: {e}\n{traceback.format_exc()}')
                        error = True
            else:  # inserted
                try:
                    pass  # postinserted
                except Exception as e:
                    pass  # postinserted
        except Exception as e:
                    logging.error(f'アカウント処理中にエラーが発生しました: {e}\n{traceback.format_exc()}')
                    error = True
        finally:  # inserted
            try:
                context.close()
                browser.close()
            except Exception as close_err:
                logging.error(f'ブラウザ終了中にエラーが発生しました: {close_err}')
    if error:
        logging.info('動作が異常終了しました')
        print('動作が異常終了しました')
    else:  # inserted
        logging.info('動作が正常に終了しました')
        print('動作が正常に終了しました')