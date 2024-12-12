"""
ECHO: An Efficient Heuristic Viewpoint Determination Method on Frontier-Based Autonomous Exploration for Quadrotors

### 論文に基づく視線予測システムの概要

このシステムでは、以下のコスト計算式を使用して次の視点（視線）を予測します。

1. 境界コスト（Boundary Cost） compute_boundary_cost 
    目的: 視点が探索境界にどれだけ近いかを評価し、未探索領域を優先する。
    式:
        c_b = λ_bp * c_bp + λ_bl * c_bl
    - c_bp: 視点から境界点までの最短距離。
    - c_bl: 視点から境界線までの垂直距離。
    - λ_bp, λ_bl: 各距離に割り当てられる重み。

2. 環境構造コスト（Environment Structure Cost） compute_environment_structure_cost 
    目的: 視点が障害物に近い場合、追加の情報収集を評価。
    式:
        c_e = Σ(||P_i - P_f||^2) / n
    - P_i: 障害物周辺のサンプリング点。
    - P_f: 視点の位置。
    - n: サンプリング点の数。

3. 方向変更コスト（Direction Change Cost） compute_environment_structure_cost 
    目的: 視点までの移動で方向変更が少ない（効率的な移動）場合を優先。
    式:
        c_d = cos⁻¹(((P_uav - V_Pi) · v_uav) / (||P_uav - V_Pi|| * ||v_uav||))
    - P_uav: 現在の位置。
    - V_Pi: 候補視点。
    - v_uav: 現在の移動ベクトル。

4. 距離コスト（Distance Cost） compute_distance_cost 
    目的: 視点までの移動距離を最小化。
    式:
        c_dis = AstarPathLength(P_uav, V_Pi)
    - 現在のコードでは、A*アルゴリズムの代わりにユークリッド距離を使用しています。

5. 総コスト（Total Cost） compute_total_cost 
    目的: 各コスト項目を統合し、最も効率的な視点を選択。
    式:
        c_total = λ_b * c_b + λ_e * c_e + λ_d * c_d + λ_dis * c_dis
    - λ_b, λ_e, λ_d, λ_dis: 各コスト項目の重み（論文に基づき λ_b=0.4, λ_e=0.3, λ_d=0.2, λ_dis=0.1）。

### 改良点
- 滑らかな視線移動を実現するため、スムージング関数（smooth_position）を追加し、フレーム間の移動速度を制限しています。
- 視線の候補座標はウィンドウサイズ（window_width, window_height）全体にわたるグリッド上で評価されます。
- 現在のコードでは障害物や境界点は動的に設定可能で、視線の予測を柔軟にカスタマイズできます。
"""
import random
import numpy as np
from scipy.spatial.distance import euclidean
from math import acos, sqrt

class GazeEstimator:
    def __init__(self, window_width, window_height):
        self.window_width = window_width
        self.window_height = window_height
        # 重み設定
        self.lambda_b = 0.4
        self.lambda_e = 0.3
        self.lambda_d = 0.2
        self.lambda_dis = 0.1
        self.lambda_bp = 0.5
        self.lambda_bl = 0.5
        self.max_speed = 50  # 視線移動速度の最大値（ピクセル/フレーム）

    def compute_boundary_cost(self, target_position, boundary_points):
        c_bp = min(euclidean(target_position, bp) for bp in boundary_points)
        c_bl = min(abs(target_position[0] - bp[0]) for bp in boundary_points)
        return self.lambda_bp * c_bp + self.lambda_bl * c_bl

    def compute_environment_structure_cost(self, target_position, obstacle_points):
        if not obstacle_points:
            return 0
        distances = [euclidean(target_position, op) for op in obstacle_points]
        avg_distance = sum(distances) / len(distances)
        return avg_distance

    def compute_direction_change_cost(self, current_position, target_position, current_vector):
        vector_to_target = np.array(target_position) - np.array(current_position)

        # ノルムがゼロの場合を処理
        norm_vector_to_target = np.linalg.norm(vector_to_target)
        norm_current_vector = np.linalg.norm(current_vector)
        if norm_vector_to_target == 0 or norm_current_vector == 0:
            return 0  # 方向変更が無視される場合

        cos_angle = np.dot(vector_to_target, current_vector) / (norm_vector_to_target * norm_current_vector)
        cos_angle = max(min(cos_angle, 1.0), -1.0)  # 安全範囲に制限
        angle = acos(cos_angle)
        return angle

    def compute_distance_cost(self, current_position, target_position):
        return euclidean(current_position, target_position)

    def compute_total_cost(self, current_position, target_position, boundary_points, obstacle_points, current_vector):
        c_b = self.compute_boundary_cost(target_position, boundary_points)
        c_e = self.compute_environment_structure_cost(target_position, obstacle_points)
        c_d = self.compute_direction_change_cost(current_position, target_position, current_vector)
        c_dis = self.compute_distance_cost(current_position, target_position)
        return (
            self.lambda_b * c_b
            + self.lambda_e * c_e
            + self.lambda_d * c_d
            + self.lambda_dis * c_dis
        )

    def smooth_position(self, last_position, new_position):
        """視線を滑らかにするためのスムージング"""
        dx = new_position[0] - last_position[0]
        dy = new_position[1] - last_position[1]
        distance = sqrt(dx**2 + dy**2)
        if distance > self.max_speed:
            scale = self.max_speed / distance
            dx *= scale
            dy *= scale
        smoothed_x = int(last_position[0] + dx)
        smoothed_y = int(last_position[1] + dy)
        # 画面範囲内に制限
        smoothed_x = max(0, min(smoothed_x, self.window_width))
        smoothed_y = max(0, min(smoothed_y, self.window_height))
        return smoothed_x, smoothed_y

    def generate_gaze_position(self, last_gaze_position, boundary_points, obstacle_points, current_vector):
        # 候補座標を画面全体に分布
        possible_positions = [
            (x, y)
            for x in range(100, self.window_width - 100, 100)
            for y in range(100, self.window_height - 100, 100)
        ]

        min_cost = float("inf")
        best_position = None

        # コスト計算
        for position in possible_positions:
            cost = self.compute_total_cost(
                last_gaze_position, position, boundary_points, obstacle_points, current_vector
            )
            if cost < min_cost:
                min_cost = cost
                best_position = position

        # スムージング処理を強化（平均化で揺れを軽減）
        smoothed_position = self.smooth_position(last_gaze_position, best_position)

        # 画面範囲内に制限
        smoothed_x = max(0, min(smoothed_position[0], self.window_width))
        smoothed_y = max(0, min(smoothed_position[1], self.window_height))

        return smoothed_x, smoothed_y

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

        dx = new_position[0] - last_position[0]
        dy = new_position[1] - last_position[1]
        distance = sqrt(dx**2 + dy**2)
        if distance > self.max_speed:
            scale = self.max_speed / distance
            dx *= scale
            dy *= scale
        smoothed_x = int(last_position[0] + dx)
        smoothed_y = int(last_position[1] + dy)
        # 画面範囲内に制限
        smoothed_x = max(0, min(smoothed_x, self.window_width))
        smoothed_y = max(0, min(smoothed_y, self.window_height))
        return smoothed_x, smoothed_y

    def generate_gaze_position(self, last_gaze_position, boundary_points, obstacle_points, current_vector):
        # 候補座標を画面全体に分布
        possible_positions = [
            (x, y)
            for x in range(100, self.window_width - 100, 100)
            for y in range(100, self.window_height - 100, 100)
        ]

        min_cost = float("inf")
        best_position = None

        # コスト計算
        for position in possible_positions:
            cost = self.compute_total_cost(
                last_gaze_position, position, boundary_points, obstacle_points, current_vector
            )
            if cost < min_cost:
                min_cost = cost
                best_position = position

        # スムージング処理を強化（平均化で揺れを軽減）
        smoothed_position = self.smooth_position(last_gaze_position, best_position)

        # 画面範囲内に制限
        smoothed_x = max(0, min(smoothed_position[0], self.window_width))
        smoothed_y = max(0, min(smoothed_position[1], self.window_height))

        return smoothed_x, smoothed_y


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
