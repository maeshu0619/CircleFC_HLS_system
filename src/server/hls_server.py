import os
import subprocess

# グローバル変数でセグメント番号を追跡
segment_indices = {}

def get_video_bitrate(input_file):
    """
    FFmpegを使用して元動画のビットレートを取得する関数。
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

def get_next_segment_index(output_dir, level):
    """
    次のセグメント番号を取得。
    """
    if level not in segment_indices:
        segment_files = [
            f for f in os.listdir(os.path.join(output_dir, level))
            if f.startswith(f"segment-{level}-") and f.endswith(".ts")
        ]
        if segment_files:
            max_index = max(
                int(f.split('-')[-1].split('.')[0]) for f in segment_files
            )
        else:
            max_index = -1
        segment_indices[level] = max_index + 1
    return segment_indices[level]

def update_segment_index(level, count):
    """
    セグメント番号を更新。
    """
    segment_indices[level] += count

def append_to_m3u8(output_dir, level, target_duration=10):
    """
    m3u8ファイルを全セグメント情報を記述。
    """
    m3u8_path = os.path.join(output_dir, level, f"{level}.m3u8")
    segment_files = sorted([
        f for f in os.listdir(os.path.join(output_dir, level))
        if f.startswith(f"segment-{level}-") and f.endswith(".ts")
    ])
    if not segment_files:
        print(f"No segments found for {level}. Skipping m3u8 generation.")
        return

    with open(m3u8_path, 'w') as f:
        f.write("#EXTM3U\n")
        f.write("#EXT-X-VERSION:3\n")
        f.write(f"#EXT-X-TARGETDURATION:{target_duration}\n")
        f.write("#EXT-X-MEDIA-SEQUENCE:0\n")
        f.write("#EXT-X-PLAYLIST-TYPE:VOD\n")
        for segment in segment_files:
            f.write(f"#EXTINF:{target_duration}.000000,\n")
            f.write(f"{segment}\n")
        f.write("#EXT-X-ENDLIST\n")

def create_master_m3u8(output_dir):
    """
    master.m3u8ファイルを生成。
    """
    master_path = os.path.join(output_dir, "master.m3u8")
    print(f"Creating master playlist: {master_path}")

    bitrates = {
        "low": 300000,
        "medium": 800000,
        "high": 1500000
    }
    resolutions = {
        "low": "640x360",
        "medium": "1280x720",
        "high": "1920x1080"
    }
    with open(master_path, 'w') as f:
        f.write("#EXTM3U\n")
        for level, bitrate in bitrates.items():
            playlist_path = os.path.join(level, f"{level}.m3u8")
            f.write(f"#EXT-X-STREAM-INF:BANDWIDTH={bitrate},RESOLUTION={resolutions[level]}\n")
            f.write(f"{playlist_path}\n")

def create_hls_with_dynamic_bitrate(input_file, output_dir, resolutions, base_bitrate, segment_time=10):
    """
    動的に元動画のビットレートを反映したHLSストリーミングファイルを作成。

    Args:
        input_file (str): 入力動画ファイルのパス。
        output_dir (str): 出力ディレクトリ。
        resolutions (list): 解像度のリスト (width, height)。
        base_bitrate (int): 元動画の総ビットレート（kbps）。
        segment_time (int): 各セグメントの時間（秒）。
    """
    os.makedirs(output_dir, exist_ok=True)

    bitrates = {
        "low": max(100, base_bitrate // 3),
        "medium": max(300, base_bitrate),
        "high": max(600, base_bitrate * 3)
    }

    for (width, height), (level, bitrate) in zip(resolutions, bitrates.items()):
        subdir = os.path.join(output_dir, level).replace("\\", "/")
        os.makedirs(subdir, exist_ok=True)

        next_index = get_next_segment_index(output_dir, level)
        segment_pattern = os.path.join(subdir, f"segment-{level}-%03d.ts").replace("\\", "/")
        playlist_path = os.path.join(subdir, f"{level}.m3u8").replace("\\", "/")

        command = [
            "ffmpeg",
            "-i", input_file,
            "-map", "0",
            "-an",
            "-s", f"{width}x{height}",
            "-b:v", f"{bitrate}k",
            "-maxrate", f"{bitrate}k",
            "-bufsize", "2M",
            "-f", "hls",
            "-hls_time", str(segment_time),
            "-hls_playlist_type", "vod",
            "-hls_segment_filename", segment_pattern,
            "-start_number", str(next_index),
            "-g", str(30 * segment_time),
            "-force_key_frames", f"expr:gte(t,n_forced*{segment_time})",
            playlist_path  # プレイリストの出力先
        ]

        try:
            subprocess.run(command, check=True)
            print(f"HLS segments created for resolution {width}x{height}, bitrate {bitrate}k.")

            # セグメント番号を更新
            update_segment_index(level, 3)

            # m3u8ファイルを全セグメントで書き直し
            append_to_m3u8(output_dir, level, target_duration=segment_time)

        except subprocess.CalledProcessError as e:
            print(f"Error during HLS creation for {level}: {e}")

    # master.m3u8を生成
    create_master_m3u8(output_dir)

