
import cv2
import os
import subprocess
import traceback
from src.server.foveated_compression import merge_frame, calculate_segment_bitrate
from src.server.server_function import frame_segmented
from src.server.hls_server import get_video_bitrate
from src.server.gaze_prediction import GazeEstimator
from src.client.playback.logger import VideoLogger
from src.bar_making import ProgressBar
    
frame_buffer = []
segment_index = 0

def mp4_create(input_video, input_frame, video_bitrate, low_res_path, med_res_path, high_res_path, window_width, window_height):
    low_cap = cv2.VideoCapture(low_res_path)
    med_cap = cv2.VideoCapture(med_res_path)
    high_cap = cv2.VideoCapture(high_res_path)
    input_frame = input_frame
    gaze_log = VideoLogger(log_dir="logs/gaze_prediction")
    progress_bar = ProgressBar(input_frame=input_frame)

    window_width = window_width
    window_height = window_height

    segment_dir = os.path.abspath("segments/segmented_video")
    os.makedirs(segment_dir, exist_ok=True)

    fps = 30
    frame_counter = 0

    gaze_estimator = GazeEstimator(window_width, window_height)
    boundary_points = [
        (50, 50), 
        (window_width - 50, 50), 
        (50, window_height - 50), 
        (window_width - 50, window_height - 50)
    ]
    obstacle_points = gaze_estimator.generate_random_obstacles()
    current_vector = (1, 0)
    last_gaze_position = (window_width // 2, window_height // 2)

    while frame_counter < input_frame:
        ret_low, frame_low = low_cap.read()
        ret_med, frame_med = med_cap.read()
        ret_high, frame_high = high_cap.read()

        if not (ret_low and ret_med and ret_high):
            break


        # フレームごとに障害物を更新（適切な頻度で更新）
        if frame_counter % 10 == 0:
            obstacle_points = gaze_estimator.generate_random_obstacles()

        # 視線予測
        gaze_x, gaze_y = gaze_estimator.generate_gaze_position(
            last_gaze_position, 
            boundary_points, 
            obstacle_points, 
            current_vector
        )

        last_gaze_position = (gaze_x, gaze_y)
        gaze_log.log_gaze_position(gaze_x, gaze_y)

        try:
            combined_frame = merge_frame(frame_low, frame_med, frame_high, gaze_x, gaze_y)
        except Exception as e:
            print(f"Error during frame merging: {e}\n")
            break
        
        if frame_counter == 0:
            video_bitrate = calculate_segment_bitrate(window_width, window_height)
            
        mp4_create_frame_segmented(combined_frame, input_frame, video_bitrate, fps, segment_dir)

        frame_counter += 1
        progress_bar.update(frame_counter)

    low_cap.release()
    med_cap.release()
    high_cap.release()

def mp4_create_frame_segmented(combined_frame, input_frame, video_bitrate, fps, segment_dir="segments/segmented_video", segment_duration=6):
    """
    合成フレームをセグメント化します。

    Args:
        combined_frame (np.ndarray): 合成されたフレーム。
        input_frame (int): 1セグメントあたりのフレーム数。
        video_bitrate (str): ビットレート（例: "3000k"）。
        fps (int): 動画のフレームレート。
        segment_dir (str): セグメントファイルを保存するディレクトリ。
        segment_duration (int): セグメントの長さ（秒単位）。
    """
    global frame_buffer, segment_index

    # セグメントディレクトリを作成
    segment_dir = os.path.abspath(segment_dir)
    os.makedirs(segment_dir, exist_ok=True)

    thirty_sec = fps * 30

    frame_buffer.append(combined_frame)

    # フレームが規定数に達したらセグメントを保存
    if len(frame_buffer) >= thirty_sec:
        segment_path = os.path.join(segment_dir, f"segment_{segment_index:04d}.mp4")
        temp_raw_file = os.path.join(segment_dir, f"segment_{segment_index:04d}_raw.mp4")

        try:
            # OpenCVを使用して一時ファイルを作成
            height, width, _ = frame_buffer[0].shape
            out = cv2.VideoWriter(temp_raw_file, cv2.VideoWriter_fourcc(*"mp4v"), fps, (width, height))
            for frame in frame_buffer:
                out.write(frame)
            out.release()

            print(f"未エンコードセグメントを保存しました: {temp_raw_file}")

            # FFmpegを使用してエンコード
            video_bitrate_str = f"{video_bitrate}k" if isinstance(video_bitrate, int) else video_bitrate
            ffmpeg_command = [
                "ffmpeg", "-y", "-i", temp_raw_file,
                "-c:v", "libx264", "-preset", "fast",
                "-b:v", video_bitrate_str, "-maxrate", video_bitrate_str,
                "-bufsize", "3M", segment_path
            ]
            subprocess.run(ffmpeg_command, check=True)

            print(f"セグメントを保存しました: {segment_path}")

            # 一時ファイルを削除
            os.remove(temp_raw_file)

        except Exception as e:
            print(f"セグメント保存エラー: {segment_path}")
            print(traceback.format_exc())
            frame_buffer.clear()
            return False

        # フレームバッファをクリアし、次のセグメントの準備
        frame_buffer.clear()
        segment_index += 1
        return True

    return False
