"""
analyzer.py — 영상에서 관절 좌표 추출 + 각도 계산 (메모리 최적화)

농구: 측면 영상 1개 → 팔꿈치, 무릎, 상체 기울기
넷볼: 측면 영상 + 정면 영상 → 위 3개 + 슛높이, 슛방향, 좌우정렬, 어깨수평
"""

import gc
import math
import os
import tempfile

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

# ---------------------------------------------------------------------------
# 모델 로드 (지연 로드)
# ---------------------------------------------------------------------------
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_full.task")
_MODEL_BYTES = None

def _get_model_bytes():
    global _MODEL_BYTES
    if _MODEL_BYTES is None:
        with open(_MODEL_PATH, "rb") as f:
            _MODEL_BYTES = f.read()
    return _MODEL_BYTES

# ---------------------------------------------------------------------------
# 랜드마크 인덱스
# ---------------------------------------------------------------------------
LANDMARKS = {
    "right": {
        "shoulder": 12, "elbow": 14, "wrist": 16,
        "hip": 24, "knee": 26, "ankle": 28,
    },
    "left": {
        "shoulder": 11, "elbow": 13, "wrist": 15,
        "hip": 23, "knee": 25, "ankle": 27,
    },
}

FACE = {"nose": 0, "left_eye": 2, "right_eye": 5}

REQUIRED_KEYS = ["shoulder", "elbow", "wrist", "hip", "knee", "ankle"]
MIN_VISIBILITY = 0.5
SAMPLE_FPS = 5


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------
def _calc_angle(a, b, c):
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosine = np.clip(cosine, -1.0, 1.0)
    return math.degrees(math.acos(cosine))


def _calc_lean(shoulder, hip):
    dx = abs(shoulder[0] - hip[0])
    dy = abs(shoulder[1] - hip[1]) + 1e-8
    return math.degrees(math.atan2(dx, dy))


def _estimate_head_top_y(nose_y, eye_y):
    return eye_y - (nose_y - eye_y) * 2


def _open_video(video_bytes):
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(video_bytes)
    tmp.close()
    cap = cv2.VideoCapture(tmp.name)
    return cap, tmp.name


def _create_landmarker():
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_buffer=_get_model_bytes()),
        running_mode=vision.RunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(options)


def _read_frame_at(video_bytes, frame_idx):
    """특정 프레임만 읽어 반환 (메모리 절약)."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(video_bytes)
    tmp.close()
    cap = cv2.VideoCapture(tmp.name)
    cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
    ret, frame = cap.read()
    cap.release()
    os.unlink(tmp.name)
    return frame if ret else None


# ---------------------------------------------------------------------------
# 측면 영상 분석 (메모리 최적화: 랜드마크만 저장, 프레임은 나중에 읽기)
# ---------------------------------------------------------------------------
def analyze_side_video(video_bytes: bytes):
    result = {
        "elbow_angle": 0.0, "knee_angle": 0.0, "lean_angle": 0.0,
        "release_frame": None, "setup_frame": None,
        "release_landmarks": None, "setup_landmarks": None,
        "shot_height_above_head": False, "shot_direction_angle": 90.0,
        "error": None,
    }

    cap, tmp_path = _open_video(video_bytes)
    if not cap.isOpened():
        result["error"] = "영상 파일을 열 수 없습니다."
        os.unlink(tmp_path)
        return result

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

    if total_frames < fps:
        result["error"] = "영상이 너무 짧습니다. 슛 동작이 포함된 2~10초 영상을 올려주세요."
        cap.release()
        os.unlink(tmp_path)
        return result

    interval = max(1, int(fps / SAMPLE_FPS))
    landmarker = _create_landmarker()

    # --- 1단계: 랜드마크만 수집 (프레임은 저장하지 않음) ---
    lm_data = []  # (frame_idx, raw_landmarks)
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = int(frame_idx * 1000 / fps)
            res = landmarker.detect_for_video(mp_image, ts)
            raw_lms = None
            if res.pose_landmarks and len(res.pose_landmarks) > 0:
                raw_lms = res.pose_landmarks[0]
            if raw_lms is not None:
                lm_data.append((frame_idx, raw_lms, h, w))
        frame_idx += 1

    cap.release()
    landmarker.close()
    os.unlink(tmp_path)
    gc.collect()

    if len(lm_data) < 3:
        result["error"] = "영상에서 자세를 감지할 수 없습니다. 측면에서 한 사람만 촬영된 영상을 올려주세요."
        return result

    # --- 2단계: 슛 팔/하체 결정 ---
    best_wrist_y = float("inf")
    arm_side_key = "right"
    for _, raw_lms, _, _ in lm_data:
        r_y = raw_lms[LANDMARKS["right"]["wrist"]].y
        l_y = raw_lms[LANDMARKS["left"]["wrist"]].y
        min_y = min(r_y, l_y)
        if min_y < best_wrist_y:
            best_wrist_y = min_y
            arm_side_key = "right" if r_y <= l_y else "left"

    arm_side = LANDMARKS[arm_side_key]
    leg_votes = {"right": 0, "left": 0}
    for _, raw_lms, _, _ in lm_data:
        for sk in ("right", "left"):
            vis = sum(raw_lms[LANDMARKS[sk][k]].visibility for k in ["hip", "knee", "ankle"])
            leg_votes[sk] += vis
    leg_side = LANDMARKS["right" if leg_votes["right"] >= leg_votes["left"] else "left"]

    # --- 3단계: 좌표 추출 ---
    arm_keys = ["shoulder", "elbow", "wrist"]
    leg_keys = ["hip", "knee", "ankle"]
    valid = []

    for fi, raw_lms, h, w in lm_data:
        all_visible = (
            all(raw_lms[arm_side[k]].visibility >= MIN_VISIBILITY for k in arm_keys)
            and all(raw_lms[leg_side[k]].visibility >= MIN_VISIBILITY for k in leg_keys)
        )
        if not all_visible:
            continue
        lm_dict = {}
        for k in arm_keys:
            lm = raw_lms[arm_side[k]]
            lm_dict[k] = (lm.x * w, lm.y * h)
        for k in leg_keys:
            lm = raw_lms[leg_side[k]]
            lm_dict[k] = (lm.x * w, lm.y * h)
        lm_dict["nose"] = (raw_lms[FACE["nose"]].x * w, raw_lms[FACE["nose"]].y * h)
        eye_y = min(raw_lms[FACE["left_eye"]].y, raw_lms[FACE["right_eye"]].y) * h
        lm_dict["eye_y"] = eye_y
        lm_dict["head_top_y"] = _estimate_head_top_y(lm_dict["nose"][1], eye_y)
        valid.append((fi, lm_dict))

    if len(valid) < 3:
        result["error"] = "영상에서 자세를 감지할 수 없습니다. 측면에서 한 사람만 촬영된 영상을 올려주세요."
        return result

    # --- 4단계: 릴리스/셋업 프레임 결정 ---
    release_candidates = []
    for i, (_, ld) in enumerate(valid):
        elbow_ang = _calc_angle(ld["shoulder"], ld["elbow"], ld["wrist"])
        if ld["wrist"][1] < ld["shoulder"][1]:
            release_candidates.append((i, elbow_ang))

    if release_candidates:
        release_idx = max(release_candidates, key=lambda x: x[1])[0]
    else:
        release_idx = min(range(len(valid)), key=lambda i: valid[i][1]["wrist"][1])

    setup_idx = min(
        range(len(valid)),
        key=lambda i: _calc_angle(valid[i][1]["hip"], valid[i][1]["knee"], valid[i][1]["ankle"]),
    )

    release_ld = valid[release_idx][1]
    setup_ld = valid[setup_idx][1]
    release_frame_idx = valid[release_idx][0]
    setup_frame_idx = valid[setup_idx][0]

    # --- 5단계: 필요한 프레임만 읽기 ---
    result["release_frame"] = _read_frame_at(video_bytes, release_frame_idx)
    result["setup_frame"] = _read_frame_at(video_bytes, setup_frame_idx)

    result["elbow_angle"] = round(_calc_angle(release_ld["shoulder"], release_ld["elbow"], release_ld["wrist"]), 1)
    result["knee_angle"] = round(_calc_angle(setup_ld["hip"], setup_ld["knee"], setup_ld["ankle"]), 1)
    result["lean_angle"] = round(_calc_lean(release_ld["shoulder"], release_ld["hip"]), 1)
    result["release_landmarks"] = release_ld
    result["setup_landmarks"] = setup_ld

    # 넷볼 추가 지표
    # 슛 시작 높이: 높이(y) + 위치(x) 모두 체크
    # - y: 손목이 머리 위에 있는가
    # - x: 손목이 코 x좌표에서 크게 벗어나지 않는가 (앞으로 나가면 ❌)
    # 허용 x 편차: 머리 크기(코~눈 거리 × 3) 이내면 "위", 넘으면 "앞"
    shot_height_above = False  # 높이 OK
    shot_height_position = False  # 위치(앞/위) OK
    for _, ld in valid:
        elbow_ang = _calc_angle(ld["shoulder"], ld["elbow"], ld["wrist"])
        if elbow_ang < 140:
            # 높이 체크
            if ld["wrist"][1] < ld["head_top_y"]:
                shot_height_above = True
                # 위치 체크: 손목 x가 코 x에서 머리 크기 이내인가
                head_size = abs(ld["nose"][1] - ld["eye_y"]) * 3
                x_diff = abs(ld["wrist"][0] - ld["nose"][0])
                if x_diff < head_size:
                    shot_height_position = True
                    break
    result["shot_height_above_head"] = shot_height_above and shot_height_position
    result["shot_height_in_front"] = shot_height_above and not shot_height_position

    # 슛 방향: 어깨→손목 벡터가 수평선과 이루는 각도
    # 90° = 수직, 0° = 수평(앞으로)
    dx = release_ld["wrist"][0] - release_ld["shoulder"][0]
    dy = release_ld["shoulder"][1] - release_ld["wrist"][1]  # y 반전 (위가 +)
    if abs(dx) + abs(dy) > 1e-3:
        direction_angle = math.degrees(math.atan2(dy, abs(dx)))
        result["shot_direction_angle"] = round(max(0, min(90, direction_angle)), 1)

    # 메모리 정리
    del lm_data, valid
    gc.collect()

    return result


# ---------------------------------------------------------------------------
# 정면 영상 분석
# ---------------------------------------------------------------------------
def analyze_front_video(video_bytes: bytes):
    result = {
        "alignment_angle": 0.0, "shoulder_level_angle": 0.0,
        "finger_direction_angle": 0.0,
        "front_frame": None, "front_landmarks": None, "error": None,
    }

    cap, tmp_path = _open_video(video_bytes)
    if not cap.isOpened():
        result["error"] = "정면 영상 파일을 열 수 없습니다."
        os.unlink(tmp_path)
        return result

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    interval = max(1, int(fps / SAMPLE_FPS))
    landmarker = _create_landmarker()

    # 랜드마크만 수집
    lm_data = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            h, w = frame.shape[:2]
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = int(frame_idx * 1000 / fps)
            res = landmarker.detect_for_video(mp_image, ts)
            if res.pose_landmarks and len(res.pose_landmarks) > 0:
                raw_lms = res.pose_landmarks[0]
                keys_must = [11, 12]
                keys_soft = [13, 14, 15, 16]
                if (all(raw_lms[k].visibility >= MIN_VISIBILITY for k in keys_must)
                        and all(raw_lms[k].visibility >= 0.3 for k in keys_soft)):
                    ld = {
                        "r_shoulder": (raw_lms[12].x * w, raw_lms[12].y * h),
                        "l_shoulder": (raw_lms[11].x * w, raw_lms[11].y * h),
                        "r_elbow": (raw_lms[14].x * w, raw_lms[14].y * h),
                        "l_elbow": (raw_lms[13].x * w, raw_lms[13].y * h),
                        "r_wrist": (raw_lms[16].x * w, raw_lms[16].y * h),
                        "l_wrist": (raw_lms[15].x * w, raw_lms[15].y * h),
                        "r_index": (raw_lms[20].x * w, raw_lms[20].y * h),
                        "l_index": (raw_lms[19].x * w, raw_lms[19].y * h),
                    }
                    lm_data.append((frame_idx, ld))
        frame_idx += 1

    cap.release()
    landmarker.close()
    os.unlink(tmp_path)
    gc.collect()

    if len(lm_data) < 2:
        result["error"] = "정면 영상에서 자세를 감지할 수 없습니다. 정면에서 한 사람만 촬영된 영상을 올려주세요."
        return result

    # 릴리스 = 손목이 가장 높이 올라간 프레임
    release_idx = min(
        range(len(lm_data)),
        key=lambda i: min(lm_data[i][1]["r_wrist"][1], lm_data[i][1]["l_wrist"][1]),
    )
    ld = lm_data[release_idx][1]
    release_frame_idx = lm_data[release_idx][0]

    if ld["r_wrist"][1] <= ld["l_wrist"][1]:
        shot_shoulder, shot_elbow, shot_wrist = ld["r_shoulder"], ld["r_elbow"], ld["r_wrist"]
        shot_index = ld["r_index"]
    else:
        shot_shoulder, shot_elbow, shot_wrist = ld["l_shoulder"], ld["l_elbow"], ld["l_wrist"]
        shot_index = ld["l_index"]

    dx_elbow = abs(shot_elbow[0] - shot_shoulder[0])
    dy_elbow = abs(shot_shoulder[1] - shot_elbow[1]) + 1e-8
    result["alignment_angle"] = round(math.degrees(math.atan2(dx_elbow, dy_elbow)), 1)

    shoulder_dx = abs(ld["r_shoulder"][0] - ld["l_shoulder"][0]) + 1e-8
    shoulder_dy = abs(ld["r_shoulder"][1] - ld["l_shoulder"][1])
    result["shoulder_level_angle"] = round(math.degrees(math.atan2(shoulder_dy, shoulder_dx)), 1)

    finger_dx = abs(shot_index[0] - shot_wrist[0])
    finger_dy = abs(shot_wrist[1] - shot_index[1]) + 1e-8
    result["finger_direction_angle"] = round(math.degrees(math.atan2(finger_dx, finger_dy)), 1)

    # 필요한 프레임만 읽기
    result["front_frame"] = _read_frame_at(video_bytes, release_frame_idx)
    result["front_landmarks"] = ld

    # 메모리 정리
    del lm_data
    gc.collect()

    return result


# ---------------------------------------------------------------------------
# 시각화 함수들
# ---------------------------------------------------------------------------
def _rotate_point(origin, point, angle_deg):
    rad = math.radians(angle_deg)
    ox, oy = origin
    px, py = point
    dx, dy = px - ox, py - oy
    rx = dx * math.cos(rad) - dy * math.sin(rad)
    ry = dx * math.sin(rad) + dy * math.cos(rad)
    return (ox + rx, oy + ry)


def draw_angle_comparison(frame, point_a, point_b, point_c,
                          actual_angle, ideal_min, ideal_max, label=""):
    img = frame.copy()
    h, w = img.shape[:2]
    a = tuple(map(int, point_a))
    b = tuple(map(int, point_b))
    c = tuple(map(int, point_c))

    # 실제 각도 (빨강 = You)
    cv2.line(img, a, b, (60, 76, 255), 4, cv2.LINE_AA)
    cv2.line(img, b, c, (60, 76, 255), 4, cv2.LINE_AA)

    arc_radius = int(min(w, h) * 0.06)
    angle_ba = math.degrees(math.atan2(-(a[1] - b[1]), a[0] - b[0]))
    angle_bc = math.degrees(math.atan2(-(c[1] - b[1]), c[0] - b[0]))
    cv2.ellipse(img, b, (arc_radius, arc_radius), 0, -angle_ba, -angle_bc, (60, 76, 255), 3, cv2.LINE_AA)

    mid_angle_rad = math.radians((angle_ba + angle_bc) / 2)
    text_x = int(b[0] + (arc_radius + 25) * math.cos(mid_angle_rad))
    text_y = int(b[1] - (arc_radius + 25) * math.sin(mid_angle_rad))
    cv2.putText(img, f"{actual_angle}", (text_x - 20, text_y + 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (60, 76, 255), 2, cv2.LINE_AA)

    # 이상적 각도 (초록 = Ideal)
    # 범위 안이면 현재 각도 = 이상적 (차이 0)
    # 범위 밖이면 가장 가까운 경계를 목표로 표시
    if ideal_min <= actual_angle <= ideal_max:
        ideal_target = actual_angle  # 이미 이상적
    elif actual_angle < ideal_min:
        ideal_target = ideal_min  # 더 펴야 함
    else:
        ideal_target = ideal_max  # 더 접어야 함
    angle_diff = ideal_target - actual_angle
    ideal_c = _rotate_point(point_b, point_c, angle_diff)
    ideal_c_int = tuple(map(int, ideal_c))
    cv2.line(img, b, ideal_c_int, (0, 220, 100), 2, cv2.LINE_AA)

    angle_ideal_c = math.degrees(math.atan2(-(ideal_c[1] - b[1]), ideal_c[0] - b[0]))
    cv2.ellipse(img, b, (arc_radius + 8, arc_radius + 8), 0, -angle_ba, -angle_ideal_c, (0, 220, 100), 2, cv2.LINE_AA)

    for pt in [a, b, c]:
        cv2.circle(img, pt, 8, (255, 255, 255), -1, cv2.LINE_AA)
        cv2.circle(img, pt, 8, (0, 0, 0), 2, cv2.LINE_AA)
    cv2.circle(img, ideal_c_int, 6, (0, 220, 100), -1, cv2.LINE_AA)

    # 범례
    _draw_legend(img, label, f"You: {actual_angle}", f"Ideal: {ideal_min}-{ideal_max}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_lean_comparison(frame, shoulder, hip, actual_angle, ideal_max, label=""):
    img = frame.copy()
    sh = tuple(map(int, shoulder))
    hp = tuple(map(int, hip))

    cv2.line(img, hp, sh, (60, 76, 255), 4, cv2.LINE_AA)
    ideal_top = (hp[0], hp[1] - abs(sh[1] - hp[1]))
    cv2.line(img, hp, ideal_top, (0, 220, 100), 2, cv2.LINE_AA)
    cv2.circle(img, sh, 8, (255, 255, 255), -1)
    cv2.circle(img, hp, 8, (255, 255, 255), -1)

    _draw_legend(img, label, f"You: {actual_angle}", f"Ideal: 0-{ideal_max}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_shot_height_comparison(frame, landmarks, is_above_head):
    img = frame.copy()
    wrist = landmarks["wrist"]
    head_top_y = landmarks["head_top_y"]
    wr_pt = tuple(map(int, wrist))
    h, w = img.shape[:2]

    head_y = int(head_top_y)
    cv2.line(img, (0, head_y), (w, head_y), (0, 220, 100), 2, cv2.LINE_AA)
    cv2.putText(img, "HEAD TOP", (15, head_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 100), 2)

    color = (0, 220, 100) if is_above_head else (60, 76, 255)
    cv2.circle(img, wr_pt, 12, color, -1, cv2.LINE_AA)
    cv2.circle(img, wr_pt, 12, (255, 255, 255), 2, cv2.LINE_AA)
    cv2.putText(img, "WRIST", (wr_pt[0] + 15, wr_pt[1] + 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

    status = "Above head" if is_above_head else "Below head"
    _draw_legend(img, "SHOT HEIGHT", f"You: {status}", "Ideal: Above head")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_shot_direction_comparison(frame, landmarks, direction_angle):
    img = frame.copy()
    shoulder = landmarks["shoulder"]
    sh_pt = tuple(map(int, shoulder))
    wrist = landmarks["wrist"]
    wr_pt = tuple(map(int, wrist))
    h, w = img.shape[:2]
    line_len = int(min(w, h) * 0.2)

    # 슛 방향 감지: 손목이 어깨보다 왼쪽이면 -1, 오른쪽이면 +1
    x_dir = -1 if wrist[0] < shoulder[0] else 1

    # --- 90° 수직선 (회색 — 기준) ---
    vert_end = (sh_pt[0], sh_pt[1] - line_len)
    cv2.line(img, sh_pt, vert_end, (100, 100, 100), 1, cv2.LINE_AA)
    cv2.putText(img, "90", (vert_end[0] - 15, vert_end[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

    # --- 45° 기준선 (회색 — 너무 앞) ---
    rad_45 = math.radians(45)
    end_45 = (int(sh_pt[0] + x_dir * line_len * math.cos(rad_45)), int(sh_pt[1] - line_len * math.sin(rad_45)))
    cv2.line(img, sh_pt, end_45, (100, 100, 100), 1, cv2.LINE_AA)
    cv2.putText(img, "45", (end_45[0] + x_dir * 5, end_45[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 100, 100), 1)

    # --- 이상적 범위 (초록 부채꼴: 65°~80°) ---
    overlay = img.copy()
    pts = [sh_pt]
    for deg in range(65, 81):
        r = math.radians(deg)
        pts.append((int(sh_pt[0] + x_dir * line_len * math.cos(r)), int(sh_pt[1] - line_len * math.sin(r))))
    pts.append(sh_pt)
    cv2.fillPoly(overlay, [np.array(pts)], (0, 220, 100))
    cv2.addWeighted(overlay, 0.2, img, 0.8, 0, img)

    rad_65 = math.radians(65)
    rad_80 = math.radians(80)
    end_65 = (int(sh_pt[0] + x_dir * line_len * math.cos(rad_65)), int(sh_pt[1] - line_len * math.sin(rad_65)))
    end_80 = (int(sh_pt[0] + x_dir * line_len * math.cos(rad_80)), int(sh_pt[1] - line_len * math.sin(rad_80)))
    cv2.line(img, sh_pt, end_65, (0, 220, 100), 2, cv2.LINE_AA)
    cv2.line(img, sh_pt, end_80, (0, 220, 100), 2, cv2.LINE_AA)
    cv2.putText(img, "65", (end_65[0] + x_dir * 5, end_65[1] - 5),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 100), 2)
    cv2.putText(img, "80", (end_80[0] - x_dir * 30, end_80[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 220, 100), 2)

    # --- 실제 방향: 어깨→손목 (빨강 화살표) ---
    cv2.arrowedLine(img, sh_pt, wr_pt, (60, 76, 255), 4, cv2.LINE_AA, tipLength=0.15)
    cv2.putText(img, f"{direction_angle}", (wr_pt[0] + 10, wr_pt[1] - 10),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (60, 76, 255), 2)

    # 어깨 점
    cv2.circle(img, sh_pt, 10, (255, 255, 255), -1, cv2.LINE_AA)
    cv2.circle(img, sh_pt, 10, (0, 0, 0), 2, cv2.LINE_AA)

    _draw_legend(img, "DIRECTION", f"You: {direction_angle}", "Ideal: 65-80")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_skeleton(frame, landmarks, angles_text=None):
    img = frame.copy()
    connections = [("shoulder", "elbow"), ("elbow", "wrist"), ("shoulder", "hip"), ("hip", "knee"), ("knee", "ankle")]
    for a, b in connections:
        if a in landmarks and b in landmarks:
            cv2.line(img, tuple(map(int, landmarks[a])), tuple(map(int, landmarks[b])), (0, 255, 128), 3)
    for key in REQUIRED_KEYS:
        if key in landmarks:
            pt = tuple(map(int, landmarks[key]))
            cv2.circle(img, pt, 7, (0, 140, 255), -1)
            cv2.circle(img, pt, 7, (255, 255, 255), 2)
    if angles_text:
        for i, txt in enumerate(angles_text):
            cv2.putText(img, txt, (15, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_front_skeleton(frame, landmarks, angles_text=None):
    img = frame.copy()
    connections = [("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"), ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"), ("r_shoulder", "l_shoulder")]
    for a, b in connections:
        if a in landmarks and b in landmarks:
            cv2.line(img, tuple(map(int, landmarks[a])), tuple(map(int, landmarks[b])), (0, 255, 128), 3)
    for key in landmarks:
        pt = tuple(map(int, landmarks[key]))
        cv2.circle(img, pt, 7, (0, 140, 255), -1)
        cv2.circle(img, pt, 7, (255, 255, 255), 2)
    if angles_text:
        for i, txt in enumerate(angles_text):
            cv2.putText(img, txt, (15, 30 + i * 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_front_comparison(frame, landmarks, metric, actual_angle, ideal_max, label=""):
    img = frame.copy()
    if landmarks["r_wrist"][1] <= landmarks["l_wrist"][1]:
        sh, el, wr, idx = landmarks["r_shoulder"], landmarks["r_elbow"], landmarks["r_wrist"], landmarks["r_index"]
    else:
        sh, el, wr, idx = landmarks["l_shoulder"], landmarks["l_elbow"], landmarks["l_wrist"], landmarks["l_index"]

    if metric == "alignment":
        sh_pt, el_pt = tuple(map(int, sh)), tuple(map(int, el))
        cv2.line(img, sh_pt, el_pt, (60, 76, 255), 4, cv2.LINE_AA)
        cv2.circle(img, sh_pt, 8, (60, 76, 255), -1)
        cv2.circle(img, el_pt, 8, (60, 76, 255), -1)
        ideal_top = (sh_pt[0], sh_pt[1] - abs(el_pt[1] - sh_pt[1]))
        cv2.line(img, sh_pt, ideal_top, (0, 220, 100), 2, cv2.LINE_AA)
        cv2.circle(img, ideal_top, 6, (0, 220, 100), -1)
    elif metric == "shoulder_level":
        r_sh, l_sh = tuple(map(int, landmarks["r_shoulder"])), tuple(map(int, landmarks["l_shoulder"]))
        cv2.line(img, r_sh, l_sh, (60, 76, 255), 4, cv2.LINE_AA)
        cv2.circle(img, r_sh, 8, (60, 76, 255), -1)
        cv2.circle(img, l_sh, 8, (60, 76, 255), -1)
        mid_y = (r_sh[1] + l_sh[1]) // 2
        cv2.line(img, (r_sh[0], mid_y), (l_sh[0], mid_y), (0, 220, 100), 2, cv2.LINE_AA)
    elif metric == "finger_direction":
        wr_pt, idx_pt = tuple(map(int, wr)), tuple(map(int, idx))
        cv2.line(img, wr_pt, idx_pt, (60, 76, 255), 4, cv2.LINE_AA)
        cv2.circle(img, wr_pt, 8, (60, 76, 255), -1)
        cv2.circle(img, idx_pt, 8, (60, 76, 255), -1)
        ideal_top = (wr_pt[0], wr_pt[1] - abs(idx_pt[1] - wr_pt[1]))
        cv2.line(img, wr_pt, ideal_top, (0, 220, 100), 2, cv2.LINE_AA)
        cv2.circle(img, ideal_top, 6, (0, 220, 100), -1)

    _draw_legend(img, label, f"You: {actual_angle}", f"Ideal: 0-{ideal_max}")
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def _draw_legend(img, title, you_text, ideal_text):
    """공통 범례 (좌상단)."""
    y = 40
    cv2.putText(img, title, (15, y), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (255, 255, 255), 2, cv2.LINE_AA)
    y += 35
    cv2.rectangle(img, (15, y - 12), (35, y + 4), (60, 76, 255), -1)
    cv2.putText(img, you_text, (42, y + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (60, 76, 255), 2)
    y += 28
    cv2.rectangle(img, (15, y - 12), (35, y + 4), (0, 220, 100), -1)
    cv2.putText(img, ideal_text, (42, y + 2), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 220, 100), 2)
