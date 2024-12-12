import http.server
import socketserver
import webbrowser
import os
import json
from src.client.playback.logger import VideoLogger

def serve_hls(output_directory, html_template_path, html_file_path, m3u8_url):
    """
    Serve HLS video and open it in Chrome, with real-time logging.

    Args:
        output_directory (str): Directory containing the HLS files.
        html_template_path (str): Path to the HTML template file.
        html_file_path (str): Path to save the final HTML file.
        m3u8_url (str): URL to the playlist file (playlist.m3u8).
    """
    # Initialize the logger
    logger = VideoLogger(log_dir="logs/video_streaming")

    # Load HTML template
    with open(html_template_path, "r") as template_file:
        html_content = template_file.read()

    # Replace placeholder with dynamic values
    html_content = html_content.replace("{m3u8_url}", m3u8_url)

    # Save the final HTML file
    os.makedirs(os.path.dirname(html_file_path), exist_ok=True)
    with open(html_file_path, "w") as html_file:
        html_file.write(html_content)

    # Start HTTP server with custom handler
    os.chdir(output_directory)
    port = 8080

    class LoggingHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            try:
                super().do_GET()
            except ConnectionAbortedError:
                print("Connection was aborted by the client.")
            except Exception as e:
                print(f"Unexpected error in GET request: {e}")

        def do_POST(self):
            try:
                if self.path == "/log_event":
                    try:
                        content_length = int(self.headers['Content-Length'])
                        post_data = self.rfile.read(content_length)
                        event_data = json.loads(post_data)
                        logger.log_event(event_data)
                        self.send_response(200)
                        self.end_headers()
                    except Exception as e:
                        print(f"Error handling POST request: {e}")
                        self.send_response(500)
                        self.end_headers()
            except ConnectionResetError:
                print("Connection reset by the client.")
            except Exception as e:
                print(f"Error in POST request: {e}")

    try:
        server_url = f"http://localhost:{port}/{os.path.basename(html_file_path)}"
        print(f"Serving at {server_url}")
        webbrowser.open(server_url)

        with socketserver.TCPServer(("", port), LoggingHTTPRequestHandler) as httpd:
            print(f"Serving HLS files at port {port}")
            print("Press Ctrl+C to stop the server.")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("Server stopped.")
