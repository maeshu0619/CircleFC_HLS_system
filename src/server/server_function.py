import cv2
import os
import subprocess
import traceback
import json
from src.server.hls_server import get_video_bitrate, create_hls_with_dynamic_bitrate

frame_buffer = []
segment_index = 0


def frame_segmented(combined_frame, input_frame, video_bitrate, fps, segment_dir="segments/segmented_video", segment_duration=6):
    """
    合成フレームをセグメント化し、H.264形式でエンコードして保存します。

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

            # HLS生成
            try:
                hls_output_dir = "segments/hls_file"
                resolutions = [(640, 360), (1280, 720), (1920, 1080)]  # 解像度リスト
                create_hls_with_dynamic_bitrate(segment_path, hls_output_dir, resolutions, video_bitrate)
                print(f"HLSファイルを生成しました: {hls_output_dir}")
            except Exception as e:
                print(f'Video Encoding for HLS failed: {e}')
                
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

def get_video_frame_count(input_video):
    """
    Get the total number of frames in a video file.

    Args:
        input_video (str): Path to the input video file.

    Returns:
        int: Total frame count.
    """
    try:
        # Use ffprobe to get video metadata
        command = [
            "ffprobe",
            "-v", "error",  # Suppress non-error messages
            "-select_streams", "v:0",  # Focus on video stream
            "-show_entries", "stream=nb_frames",  # Get total frame count
            "-of", "json",  # Output in JSON format
            input_video
        ]
        result = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True, text=True)
        metadata = json.loads(result.stdout)
        frame_count = int(metadata["streams"][0]["nb_frames"])
        return frame_count
    except Exception as e:
        print(f"Error occurred while retrieving frame count: {e}")
        return None
    
def save_frames_from_video(combined_frame, output_directory, frame_name_pattern="frame_%04d.jpg"):
    """
    Save frames from a video (or video-like object) to a directory.

    Args:
        combined_frame: A video capture object or a sequence of frames.
        output_directory (str): Directory where the frames will be saved.
        frame_name_pattern (str): Pattern for naming frame files (e.g., "frame_%04d.jpg").
    """
    # Ensure the output directory exists
    os.makedirs(output_directory, exist_ok=True)

    frame_index = 0

    while True:
        # Read a frame from the video source
        success, frame = combined_frame.read() if hasattr(combined_frame, 'read') else (frame_index < len(combined_frame), combined_frame[frame_index])
        
        if not success:
            break  # Break if no more frames are available

        # Construct the file path
        frame_file = os.path.join(output_directory, frame_name_pattern % frame_index)

        # Save the frame as an image
        cv2.imwrite(frame_file, frame)
        print(f"Saved: {frame_file}")

        frame_index += 1

    print(f"Total {frame_index} frames saved to {output_directory}.")


def get_video_bitrate(input_file):
    """
    FFmpegを使用して元動画のビットレートを取得する関数。

    Args:
        input_file (str): 入力動画ファイルのパス。

    Returns:
        int: 動画のビットレート（kbps）。
    """
    command = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=bit_rate",
        "-of", "default=noprint_wrappers=1:nokey=1",
        input_file
    ]
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        bitrate_bps = int(result.stdout.strip())
        return bitrate_bps // 1000  # kbps単位に変換
    except Exception as e:
        print(f"Error fetching bitrate: {e}")
        return None