import time
from src.client.hls_client import serve_hls

class VideoPlayback:
    def __init__(self, hls_dir):
        # Directory containing the HLS files (e.g., playlist.m3u8 and .ts files)
        self.output_dir = hls_dir
        # Path to save the HTML file
        self.html_file = f"{hls_dir}/live-stream.html"
        # URL to the HLS playlist
        self.m3u8_playlist_url = "http://localhost:8080/master.m3u8"

    def run(self, duration):
        """
        Run the HLS playback for the specified duration.
        Args:
            duration (float): Time in seconds to keep the playback running.
        """
        start_time = time.time()
        while time.time() - start_time < duration:
            serve_hls(
                output_directory=self.output_dir,
                html_template_path="src/client/playback/hls_template.html",
                html_file_path=self.html_file,
                m3u8_url=self.m3u8_playlist_url
            )
        print("Playback duration completed. Stopping the server.")

def start_video_playback(hls_dir, fps, input_frame):
    """
    Start video playback for a duration based on the input frames and FPS.
    Args:
        hls_dir (str): Path to the HLS directory containing the .m3u8 files.
        fps (int): Frames per second of the video.
        input_frame (int): Total number of frames in the video.
    """
    duration = input_frame / fps  # Calculate the playback duration in seconds
    print(f"Starting video playback for {duration:.2f} seconds...")
    client_operator = VideoPlayback(hls_dir)
    client_operator.run(duration)
