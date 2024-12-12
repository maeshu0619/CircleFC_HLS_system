import os
import shutil

def clear_hls_segments(segment_dir):
    """
    指定されたディレクトリ内のすべてのHLSセグメントを削除。

    Args:
        segment_dir (str): セグメントを格納しているディレクトリのパス。
    """
    if os.path.exists(segment_dir):
        try:
            shutil.rmtree(segment_dir)
            print(f"Cleared all HLS segments in {segment_dir}.")
        except Exception as e:
            print(f"Error clearing HLS segments: {e}")
    else:
        print(f"No existing segments to clear in {segment_dir}.")
