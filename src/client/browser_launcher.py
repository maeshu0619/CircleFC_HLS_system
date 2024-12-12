import webbrowser
import subprocess
import platform
import os
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

import time
# グローバル変数
driver = None

#global chrome_process

def open_chrome(url="http://localhost:8080/master.m3u8"):
    """
    Chrome ブラウザで指定された URL を自動的に開く関数。

    Args:
        url (str): 開く URL（デフォルトは MPEG-DASH プレイヤーの URL）。
    """
    global chrome_process
    chrome_path = ""

    if platform.system() == "Windows":
        chrome_path = "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
    elif platform.system() == "Darwin":
        chrome_path = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
    elif platform.system() == "Linux":
        chrome_path = "/usr/bin/google-chrome"

    if os.path.exists(chrome_path):
        print(f'Chrome起動中...\n')
        chrome_process = subprocess.Popen([chrome_path, "--enable-logging", "--v=1", url])
    else:
        print(f'Chromeが見つかりません')
        chrome_process = webbrowser.open(url)


def close_live_stream_tabs():
    """
    Chromeで開かれているすべての http://localhost:8080/live-stream.html タブを閉じる。
    """
    # Chromeの設定
    chrome_options = Options()
    chrome_options.add_argument("--remote-debugging-port=9222")  # デバッグモードで起動
    chrome_options.add_argument("--user-data-dir=selenium")  # ユーザーデータを保持

    # WebDriverのサービス設定（ChromeDriverのパスを指定）
    service = Service("path/to/chromedriver")  # ChromeDriverのパスに置き換えてください
    driver = webdriver.Chrome(service=service, options=chrome_options)

    try:
        # すべてのウィンドウを取得
        handles = driver.window_handles

        for handle in handles:
            driver.switch_to.window(handle)
            current_url = driver.current_url

            # 指定されたURLならタブを閉じる
            if "http://localhost:8080/live-stream.html" in current_url:
                print(f"Closing tab with URL: {current_url}")
                driver.close()

        print("All specified tabs have been closed.")
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

def handle_exit(signum, frame):
    """
    シグナル捕捉時にクリーンアップ処理を呼び出す。
    """
    print(f"終了シグナル({signum})を受信しました。クリーンアップを開始します...")
    close_live_stream_tabs()
    os._exit(0)