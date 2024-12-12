import sys

class ProgressBar:
    def __init__(self, input_frame, bar_length=50):
        """
        Initialize the progress bar.

        Args:
            input_frame (int): Total number of frames to process.
            bar_length (int): Length of the progress bar in characters.
        """
        self.input_frame = input_frame
        self.bar_length = bar_length
        self.one_scale = input_frame / bar_length
        self.last_filled_length = 0

    def update(self, frame_counter):
        """
        Update the progress bar only when a new segment of the bar is filled.

        Args:
            frame_counter (int): Number of frames processed so far.
        """
        progress = frame_counter / self.input_frame
        filled_length = int(self.bar_length * progress)

        # Update the bar only when the filled length changes
        if filled_length > self.last_filled_length:
            self.last_filled_length = filled_length
            bar = '█' * filled_length + '-' * (self.bar_length - filled_length)
            sys.stdout.write("\033[F\033[K")  # Move cursor up and clear the line
            sys.stdout.write(f'\rProgress: |{bar}| {frame_counter}/{self.input_frame}')
            sys.stdout.flush()
