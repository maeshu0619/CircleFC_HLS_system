"""
αブレンドによる高解像度エリアの合成は、動画の合成数が増加するにつれて
輝度が高くなるバグを修正することができるが、計算コストが高いため、推奨されない。
result=src1×α+src2×β+γ

    # 高解像度エリアの合成（アルファブレンド）
    high_alpha = high_mask / 255.0
    med_alpha = med_mask / 255.0 * (1.0 - high_alpha)
    low_alpha = 1.0 - high_alpha - med_alpha

    # 合成フレームの計算
    combined_frame = (
        frame_high * high_alpha +
        frame_med * med_alpha +
        frame_low * low_alpha
    ).astype(np.uint8)

よって現在は、条件分岐を使って合成を行っている。
"""
import cv2
import numpy as np

low_res_output = "h264_outputs/low_res.mp4"
med_res_output = "h264_outputs/med_res.mp4"
high_res_output = "h264_outputs/high_res.mp4"

low_res_bitrate = "700k"
med_res_bitrate = "1500k"
high_res_bitrate = "3000k"

med_radius = 400
high_radius = 200

def merge_frame(frame_low, frame_med, frame_high, gaze_x, gaze_y):
    global low_res_output, med_res_output, high_res_output
    global low_res_bitrate, med_res_bitrate, high_res_bitrate
    global med_radius, high_radius

    # フレームサイズ確認
    height, width, _ = frame_low.shape
    assert frame_med.shape == frame_high.shape == frame_low.shape, "Frame sizes must match!"

    # マスクの初期化
    med_mask = np.zeros((height, width), dtype=np.uint8)
    high_mask = np.zeros((height, width), dtype=np.uint8)

    # マスクの作成（円形）
    cv2.circle(med_mask, (gaze_x, gaze_y), med_radius, 255, -1)
    cv2.circle(high_mask, (gaze_x, gaze_y), high_radius, 255, -1)

    # 条件分岐を使って合成
    combined_frame = np.where(
        high_mask[..., np.newaxis] > 0,
        frame_high,
        np.where(med_mask[..., np.newaxis] > 0, frame_med, frame_low)
    )

    return combined_frame


def calculate_segment_bitrate(frame_width, frame_height):
    global low_res_output, med_res_output, high_res_output
    global low_res_bitrate, med_res_bitrate, high_res_bitrate
    global med_radius, high_radius

    # フレーム全体の面積
    frame_area = frame_width * frame_height

    # 各円の面積
    high_area = np.pi * high_radius**2
    med_area = np.pi * med_radius**2

    # 各領域の割合
    high_ratio = high_area / frame_area
    med_ratio = (med_area - high_area) / frame_area
    low_ratio = 1 - high_ratio - med_ratio

    # ビットレートを数値に変換（'k'を除外して数値に変換）
    low_res_bitrate_num = int(low_res_bitrate.replace("k", ""))
    med_res_bitrate_num = int(med_res_bitrate.replace("k", ""))
    high_res_bitrate_num = int(high_res_bitrate.replace("k", ""))

    # 全体ビットレートを計算
    total_bitrate = (
        low_ratio * low_res_bitrate_num +
        med_ratio * med_res_bitrate_num +
        high_ratio * high_res_bitrate_num
    )

    return f"{int(total_bitrate)}k"
