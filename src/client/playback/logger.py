import os
import json
from datetime import datetime

class VideoLogger:
    def __init__(self, log_dir):
        """
        Initialize the VideoLogger.

        Args:
            log_dir (str): Base directory to save log files.
        """
        self.log_dir = os.path.abspath(log_dir)  # 絶対パスを取得
        self.today = datetime.now().strftime("%Y-%m-%d")  # 現在の日付を取得
        self.daily_log_dir = os.path.join(self.log_dir, self.today)  # 日付ディレクトリ
        self.start_time = datetime.now().strftime("%H-%M-%S")  # 開始時刻を取得

        # 必要なディレクトリを作成
        try:
            os.makedirs(self.daily_log_dir, exist_ok=True)
        except Exception as e:
            print(f"Error creating log directory: {e}")
            raise

        # ログファイルパス
        self.log_file_path = os.path.join(self.daily_log_dir, f"{self.start_time}.txt")

        # ログファイルの初期化
        try:
            with open(self.log_file_path, "w") as log_file:
                log_file.write(f"Video playback started at: {datetime.now().isoformat()}\n")
        except Exception as e:
            print(f"Error initializing log file: {e}")
            raise

    def log_event(self, event):
        """
        Log an event to the log file.

        Args:
            event (dict): Event data to log.
        """
        event_data = {
            "time": datetime.now().isoformat(),
            **event
        }
        try:
            with open(self.log_file_path, "a") as log_file:
                log_file.write(json.dumps(event_data) + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
            raise

    def log_gaze_position(self, gaze_x, gaze_y):
        """
        Log gaze position to the log file.

        Args:
            gaze_x (int): X-coordinate of the gaze.
            gaze_y (int): Y-coordinate of the gaze.
        """
        log_entry = f"{datetime.now().strftime('%H:%M:%S')} - Gaze Position: ({gaze_x}, {gaze_y})\n"
        try:
            with open(self.log_file_path, "a") as log_file:
                log_file.write(log_entry)
        except Exception as e:
            print(f"Error logging gaze position: {e}")
            raise