"""
セグメントが独立してデコードできるため、用意する動画のフレームはIフレームのみにし、P,Bフレームは取り扱わないのが
最も好ましい。しかし、現在は全てのフレームを参照するようになっている。
"""

import cv2
import os
import random
import numpy as np
from src.server.foveated_compression import merge_frame, calculate_segment_bitrate
from src.server.server_function import frame_segmented
from src.server.hls_server import get_video_bitrate
from src.server.gaze_prediction import GazeEstimator
from src.client.playback.logger import VideoLogger
from src.bar_making import ProgressBar

class VideoStreaming:
    def __init__(self, input_video, input_frame, low_res_path, med_res_path, high_res_path, window_width, window_height):
        self.low_cap = cv2.VideoCapture(low_res_path)
        self.med_cap = cv2.VideoCapture(med_res_path)
        self.high_cap = cv2.VideoCapture(high_res_path)
        self.input_frame = input_frame
        self.gaze_log = VideoLogger(log_dir="logs/gaze_prediction")
        self.progress_bar = ProgressBar(input_frame=self.input_frame)

        self.window_width = window_width
        self.window_height = window_height

        self.segment_dir = os.path.abspath("segments/segmented_video")
        os.makedirs(self.segment_dir, exist_ok=True)

        self.fps = 30
        self.frame_counter = 0

        self.gaze_estimator = GazeEstimator(self.window_width, self.window_height)
        self.boundary_points = [
            (50, 50), 
            (self.window_width - 50, 50), 
            (50, self.window_height - 50), 
            (self.window_width - 50, self.window_height - 50)
        ]
        self.obstacle_points = self.generate_random_obstacles()
        self.current_vector = (1, 0)
        self.last_gaze_position = (self.window_width // 2, self.window_height // 2)
    
    def generate_random_obstacles(self):
        """ランダムに障害物のポイントを生成"""
        num_obstacles = 3
        return [
            (
                random.randint(100, self.window_width - 100),
                random.randint(100, self.window_height - 100)
            )
            for _ in range(num_obstacles)
        ]
    
    def run(self):
        while self.frame_counter < self.input_frame:
            ret_low, frame_low = self.low_cap.read()
            ret_med, frame_med = self.med_cap.read()
            ret_high, frame_high = self.high_cap.read()

            if not (ret_low and ret_med and ret_high):
                break


            # フレームごとに障害物を更新（適切な頻度で更新）
            if self.frame_counter % 10 == 0:
                self.obstacle_points = self.generate_random_obstacles()

            # 視線予測
            gaze_x, gaze_y = self.gaze_estimator.generate_gaze_position(
                self.last_gaze_position, 
                self.boundary_points, 
                self.obstacle_points, 
                self.current_vector
            )

            self.last_gaze_position = (gaze_x, gaze_y)
            self.gaze_log.log_gaze_position(gaze_x, gaze_y)

            try:
                combined_frame = merge_frame(frame_low, frame_med, frame_high, gaze_x, gaze_y)
            except Exception as e:
                print(f"Error during frame merging: {e}\n")
                break
            
            if self.frame_counter == 0:
                self.video_bitrate = calculate_segment_bitrate(self.window_width, self.window_height)
                
            frame_segmented(combined_frame, self.input_frame, self.video_bitrate, self.fps, self.segment_dir)

            self.frame_counter += 1
            #self.progress_bar.update(self.frame_counter)

        self.low_cap.release()
        self.med_cap.release()
        self.high_cap.release()


def start_video_streaming(input_video, input_flame, low_res_path, med_res_path, high_res_path, window_width, window_height):
    """
    VideoStreaming の実行
    """
    video_streaming = VideoStreaming(input_video, input_flame, low_res_path, med_res_path, high_res_path, window_width, window_height)
    video_streaming.run()