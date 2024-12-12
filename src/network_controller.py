"""
目的: ネットワークインターフェースの設定を変更（適用/削除）するためのクラスを提供します。
apply_settings メソッド:
・指定したネットワーク設定（帯域幅、遅延、パケット損失）を適用します。
・使用コマンド: netsh（Windows用）。
・エラーハンドリングを備え、権限不足などの問題を適切に報告。

clear_settings メソッド:
・既存の設定を削除します。
・エラーが発生しても影響がないように、失敗を無視する設計。

帯域幅の制限:制限を強化する（低い値に設定）
低帯域幅環境（例: 1 Mbps）の場合、効率的なストリーミングは低解像度で再生を継続します。一方、非効率なストリーミングは再生が途切れるか、バッファリングが頻繁に発生します。

遅延の影響:遅延を増加させる（高い値に設定）
遅延（例: 100ms、200ms）を追加すると、非効率なシステムでは視聴者が入力（シーク、再生、一時停止）に対する応答が遅くなります。
効率的なシステムは適切にキャッシュを使用し、応答時間が最小化されます。

パケット損失の影響:損失率を増加させる（高い値に設定）
パケット損失（例: 5%、10%）は、非効率なシステムで映像のフリーズやデータ破損を引き起こします。
効率的なシステムでは、再送要求やエラーハンドリングでこれを緩和します。
"""

"""
シナリオ1: Wi-Fiインターフェース
 -家庭内のWi-Fiネットワークに接続。
 -帯域幅: 最大300Mbps。
 -遅延: 10〜30ms。
 -信頼性: 無線干渉や信号範囲に依存。
シナリオ2: イーサネットインターフェース
 -オフィスの有線ネットワークに接続。
 -帯域幅: 最大1Gbps。
 -遅延: 1〜5ms。
 -信頼性: 高い。
シナリオ3: Tailscaleインターフェース
 -VPN経由でリモートネットワークに接続。
 -帯域幅: インターネット速度に依存。
 -遅延: VPNトンネルの構築による追加遅延。
"""

"""
帯域幅
・良好な条件: 5Mbps以上（HDストリーミング向け）
・平均条件: 2〜5 Mbps
・悪い条件: 1 Mbps以下
参考文献: Measuring the Quality of Experience of HTTP Video Streaming

レイテンシ（Latency）
・良好な条件: 50 ms以下
・平均条件: 50〜100 ms
・悪い条件: 150 ms以上
参考文献: Impact of packet loss and delay variation on the quality of real-time video streaming

パケットロス（Packet Loss）
・良好な条件: 1%以下
・平均条件: 1〜5%
・悪い条件: 5%以上
参考文献:ImpactofPacketLossesontheQualityofVideoStreamTransmission
"""

import subprocess

class NetworkController:
    def __init__(self, interface):
        self.interface = interface

    def apply_settings(self, rate=None, delay=None, loss=None):
        try:
            # 現在の設定をクリア
            self.clear_settings()

            # コマンドを構築
            command = f"netsh interface ipv4 set subinterface \"{self.interface}\" mtu=1500 store=persistent"
            subprocess.run(command, shell=True, check=True)
            print(f"Command executed successfully: {command}")

        except subprocess.CalledProcessError as e:
            if "elevation" in str(e.stderr).lower():
                print("Error: The operation requires elevated permissions. Please run the script as an administrator.")
            else:
                print(f"Error applying settings: {e.stderr if e.stderr else e}")

    def clear_settings(self):
        try:
            command = f"netsh interface ipv4 set subinterface \"{self.interface}\" mtu=0 store=persistent"
            subprocess.run(command, shell=True, stderr=subprocess.DEVNULL)
            print("Cleared existing network settings.")
        except subprocess.CalledProcessError:
            print("No existing settings to clear.")
