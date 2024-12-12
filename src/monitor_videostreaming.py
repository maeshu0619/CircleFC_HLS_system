import os
import time
import datetime
import psutil
import matplotlib.pyplot as plt
from queue import Queue
import requests


class NetworkMonitor:
    def __init__(self, url, interface, queue):
        self.url = url
        self.interface = interface
        self.queue = queue
        self.timestamp = None  # ログとプロットの統一タイムスタンプ
        self.current_log_dir = None
        self.start_time = time.time()
        self.prev_sent = psutil.net_io_counters().bytes_sent
        self.prev_recv = psutil.net_io_counters().bytes_recv
        self.prev_time = time.time()

    def get_total_bandwidth(self):
        """総帯域幅を計測"""
        current_counters = psutil.net_io_counters()
        current_sent = current_counters.bytes_sent
        current_recv = current_counters.bytes_recv
        current_time = time.time()

        # 送信および受信データ量の変化
        sent_diff = current_sent - self.prev_sent
        recv_diff = current_recv - self.prev_recv
        time_diff = current_time - self.prev_time

        # 帯域幅 (バイト/秒) の計算
        if time_diff > 0:
            bandwidth = (sent_diff + recv_diff) / time_diff
        else:
            bandwidth = 0

        # 前回の状態を更新
        self.prev_sent = current_sent
        self.prev_recv = current_recv
        self.prev_time = current_time

        return bandwidth

    def get_latency(self):
        """レイテンシを計測"""
        try:
            start_time = time.time()
            response = requests.get(self.url, timeout=2)
            end_time = time.time()
            latency = (end_time - start_time) * 1000  # ミリ秒に変換
            return latency
        except requests.exceptions.RequestException:
            return float('inf')  # タイムアウトなどのエラーの場合

    def get_packet_loss(self):
        """仮想的にパケットロスをシミュレート (実際のロジックは環境に依存)"""
        return 0.0  # 必要に応じてリアルな測定ロジックに置き換え

    def log_network(self):
        """ネットワークの使用状況をログに記録"""
        if not self.timestamp:
            self.timestamp = datetime.datetime.now().strftime("%y-%m-%d/%H-%M-%S")
            self.current_log_dir = os.path.join("logs/network_plot", self.timestamp)
            os.makedirs(self.current_log_dir, exist_ok=True)

        log_file = os.path.join(self.current_log_dir, "network_monitoring.txt")
        while True:
            try:
                used_bandwidth = self.get_total_bandwidth()
                jitter = abs(time.time() - self.prev_time)
                latency = self.get_latency()
                packet_loss = self.get_packet_loss()

                log_entry = (
                    f"{datetime.datetime.now()}: "
                    f"Bandwidth: {used_bandwidth / 1024:.2f} KB/s, "
                    f"Jitter: {jitter:.2f}s, "
                    f"Latency: {latency:.2f}ms, "
                    f"Packet Loss: {packet_loss:.2f}%\n"
                )
                with open(log_file, "a") as f:
                    f.write(log_entry)

                # データをqueueに送信
                self.queue.put((time.time() - self.start_time, used_bandwidth / 1024, jitter, latency, packet_loss))
                time.sleep(1)
            except Exception as e:
                print(f"Error in log_network: {e}")
                time.sleep(1)

    def plot_network(self):
        """ネットワーク使用状況をプロット"""
        elapsed_times = []
        metrics = {
            "Bandwidth (kB/s)": [],
            "Jitter (s)": [],
            "Latency (ms)": [],
            "Packet Loss (%)": []
        }

        while True:
            try:
                data = self.queue.get()
                if data is None:
                    break

                elapsed_time, used_bandwidth, jitter, latency, packet_loss = data

                elapsed_times.append(elapsed_time)
                metrics["Bandwidth (kB/s)"].append(used_bandwidth)
                metrics["Jitter (s)"].append(jitter)
                metrics["Latency (ms)"].append(latency)
                metrics["Packet Loss (%)"].append(packet_loss)

                # 各メトリックのプロットを保存
                for metric, values in metrics.items():
                    plt.figure()
                    plt.plot(elapsed_times, values, label=metric)
                    plt.xlabel("Time (s)")
                    plt.ylabel(metric)
                    plt.title(f"{metric} Over Time")
                    plt.legend()
                    plt.savefig(os.path.join(self.current_log_dir, f"{metric.split(' ')[0].lower()}.png"))
                    plt.close()

            except Exception as e:
                print(f"Error in plot_network: {e}")

    def start(self):
        """ログとプロットを並行実行"""
        from threading import Thread

        log_thread = Thread(target=self.log_network)
        plot_thread = Thread(target=self.plot_network)

        log_thread.start()
        plot_thread.start()

        log_thread.join()
        plot_thread.join()


def start_monitor_network(url, interface, queue):
    monitor = NetworkMonitor(url, interface, queue)
    monitor.start()
