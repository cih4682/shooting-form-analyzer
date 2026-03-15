"""
analyzer.py — 영상에서 관절 좌표 추출 + 각도 계산

농구: 측면 영상 1개 → 팔꿈치, 무릎, 상체 기울기
넷볼: 측면 영상 + 정면 영상 → 위 3개 + 슛높이, 슛방향, 좌우정렬, 어깨수평
"""

import math
import os
import tempfile

import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

# ---------------------------------------------------------------------------
# 모델 로드
# ---------------------------------------------------------------------------
_MODEL_PATH = os.path.join(os.path.dirname(__file__), "pose_landmarker_full.task")
with open(_MODEL_PATH, "rb") as _f:
    _MODEL_BYTES = _f.read()

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

# 얼굴 랜드마크 (넷볼 슛 높이 판정용)
FACE = {"nose": 0, "left_eye": 2, "right_eye": 5}

REQUIRED_KEYS = ["shoulder", "elbow", "wrist", "hip", "knee", "ankle"]
MIN_VISIBILITY = 0.5
SAMPLE_FPS = 5


# ---------------------------------------------------------------------------
# 유틸
# ---------------------------------------------------------------------------
def _calc_angle(a, b, c):
    """세 점 A, B, C에서 B를 꼭짓점으로 하는 각도(°)."""
    ba = np.array([a[0] - b[0], a[1] - b[1]])
    bc = np.array([c[0] - b[0], c[1] - b[1]])
    cosine = np.dot(ba, bc) / (np.linalg.norm(ba) * np.linalg.norm(bc) + 1e-8)
    cosine = np.clip(cosine, -1.0, 1.0)
    return math.degrees(math.acos(cosine))


def _calc_lean(shoulder, hip):
    """어깨-엉덩이 벡터와 수직선 사이의 기울기(°)."""
    dx = abs(shoulder[0] - hip[0])
    dy = abs(shoulder[1] - hip[1]) + 1e-8
    return math.degrees(math.atan2(dx, dy))


def _estimate_head_top_y(nose_y, eye_y):
    """정수리 y좌표 추정: 눈y - (코y - 눈y) × 2."""
    return eye_y - (nose_y - eye_y) * 2


def _open_video(video_bytes):
    """bytes → 임시파일 → VideoCapture, 임시파일 경로 반환."""
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
    tmp.write(video_bytes)
    tmp.close()
    cap = cv2.VideoCapture(tmp.name)
    return cap, tmp.name


def _create_landmarker():
    """PoseLandmarker 인스턴스 생성."""
    options = vision.PoseLandmarkerOptions(
        base_options=BaseOptions(model_asset_buffer=_MODEL_BYTES),
        running_mode=vision.RunningMode.VIDEO,
        min_pose_detection_confidence=0.5,
        min_tracking_confidence=0.5,
    )
    return vision.PoseLandmarker.create_from_options(options)


def _extract_raw_frames(cap, landmarker, fps):
    """영상에서 샘플링된 프레임과 raw 랜드마크를 추출."""
    interval = max(1, int(fps / SAMPLE_FPS))
    raw_frames = []
    frame_idx = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frame_idx % interval == 0:
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
            ts = int(frame_idx * 1000 / fps)
            res = landmarker.detect_for_video(mp_image, ts)
            raw_lms = None
            if res.pose_landmarks and len(res.pose_landmarks) > 0:
                raw_lms = res.pose_landmarks[0]
            raw_frames.append((frame_idx, frame.copy(), raw_lms))
        frame_idx += 1
    return raw_frames


# ---------------------------------------------------------------------------
# 측면 영상 분석 (농구 + 넷볼 공통)
# ---------------------------------------------------------------------------
def analyze_side_video(video_bytes: bytes):
    """
    측면 영상 분석. 농구/넷볼 공통 지표 + 넷볼용 추가 데이터 반환.

    Returns dict:
        elbow_angle, knee_angle, lean_angle,
        release_frame, setup_frame,
        release_landmarks, setup_landmarks,
        shot_height_above_head (bool),
        shot_direction_angle (float),
        error
    """
    result = {
        "elbow_angle": 0.0, "knee_angle": 0.0, "lean_angle": 0.0,
        "release_frame": None, "setup_frame": None,
        "release_landmarks": None, "setup_landmarks": None,
        "shot_height_above_head": False,
        "shot_direction_angle": 90.0,
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

    landmarker = _create_landmarker()
    raw_frames = _extract_raw_frames(cap, landmarker, fps)
    cap.release()
    landmarker.close()
    os.unlink(tmp_path)

    # --- 슛 팔 결정 ---
    best_wrist_y = float("inf")
    arm_side_key = "right"
    for _, _, raw_lms in raw_frames:
        if raw_lms is None:
            continue
        r_y = raw_lms[LANDMARKS["right"]["wrist"]].y
        l_y = raw_lms[LANDMARKS["left"]["wrist"]].y
        min_y = min(r_y, l_y)
        if min_y < best_wrist_y:
            best_wrist_y = min_y
            arm_side_key = "right" if r_y <= l_y else "left"

    arm_side = LANDMARKS[arm_side_key]

    # 하체 결정
    leg_votes = {"right": 0, "left": 0}
    for _, _, raw_lms in raw_frames:
        if raw_lms is None:
            continue
        for sk in ("right", "left"):
            vis = sum(raw_lms[LANDMARKS[sk][k]].visibility for k in ["hip", "knee", "ankle"])
            leg_votes[sk] += vis
    leg_side = LANDMARKS["right" if leg_votes["right"] >= leg_votes["left"] else "left"]

    # --- 좌표 추출 (얼굴 포함) ---
    arm_keys = ["shoulder", "elbow", "wrist"]
    leg_keys = ["hip", "knee", "ankle"]
    valid = []

    for fi, frame, raw_lms in raw_frames:
        if raw_lms is None:
            continue
        all_visible = (
            all(raw_lms[arm_side[k]].visibility >= MIN_VISIBILITY for k in arm_keys)
            and all(raw_lms[leg_side[k]].visibility >= MIN_VISIBILITY for k in leg_keys)
        )
        if not all_visible:
            continue
        h, w = frame.shape[:2]
        lm_dict = {}
        for k in arm_keys:
            lm = raw_lms[arm_side[k]]
            lm_dict[k] = (lm.x * w, lm.y * h)
        for k in leg_keys:
            lm = raw_lms[leg_side[k]]
            lm_dict[k] = (lm.x * w, lm.y * h)
        # 얼굴 랜드마크 추가
        lm_dict["nose"] = (raw_lms[FACE["nose"]].x * w, raw_lms[FACE["nose"]].y * h)
        eye_y = min(raw_lms[FACE["left_eye"]].y, raw_lms[FACE["right_eye"]].y) * h
        lm_dict["eye_y"] = eye_y
        lm_dict["head_top_y"] = _estimate_head_top_y(lm_dict["nose"][1], eye_y)
        valid.append((fi, frame, lm_dict))

    if len(valid) < 3:
        result["error"] = (
            "영상에서 자세를 감지할 수 없습니다. "
            "측면에서 한 사람만 촬영된 영상을 올려주세요."
        )
        return result

    # --- 릴리스: 팔꿈치 가장 펴진 프레임 (손목이 어깨 위) ---
    release_candidates = []
    for i, (_, _, ld) in enumerate(valid):
        elbow_ang = _calc_angle(ld["shoulder"], ld["elbow"], ld["wrist"])
        if ld["wrist"][1] < ld["shoulder"][1]:
            release_candidates.append((i, elbow_ang))

    if release_candidates:
        release_idx = max(release_candidates, key=lambda x: x[1])[0]
    else:
        release_idx = min(range(len(valid)), key=lambda i: valid[i][2]["wrist"][1])

    # --- 셋업: 무릎 가장 구부러진 프레임 ---
    setup_idx = min(
        range(len(valid)),
        key=lambda i: _calc_angle(
            valid[i][2]["hip"], valid[i][2]["knee"], valid[i][2]["ankle"]
        ),
    )

    release_ld = valid[release_idx][2]
    setup_ld = valid[setup_idx][2]

    result["elbow_angle"] = round(
        _calc_angle(release_ld["shoulder"], release_ld["elbow"], release_ld["wrist"]), 1
    )
    result["knee_angle"] = round(
        _calc_angle(setup_ld["hip"], setup_ld["knee"], setup_ld["ankle"]), 1
    )
    result["lean_angle"] = round(_calc_lean(release_ld["shoulder"], release_ld["hip"]), 1)
    result["release_frame"] = valid[release_idx][1]
    result["setup_frame"] = valid[setup_idx][1]
    result["release_landmarks"] = release_ld
    result["setup_landmarks"] = setup_ld

    # --- 넷볼용 추가 지표 ---

    # 슛 시작 높이: 슛 준비 구간(팔꿈치 < 140°, 아직 펴지기 전) 중
    # 손목이 머리 위에 있는 프레임이 하나라도 있으면 합격.
    # 이렇게 해야 공을 잠깐 모으는 동작에서 False가 되지 않는다.
    shot_height_ok = False
    for i, (_, _, ld) in enumerate(valid):
        elbow_ang = _calc_angle(ld["shoulder"], ld["elbow"], ld["wrist"])
        if elbow_ang < 140 and ld["wrist"][1] < ld["head_top_y"]:
            shot_height_ok = True
            break
    result["shot_height_above_head"] = shot_height_ok

    # 슛 방향: 릴리스 전후 손목 이동 벡터의 각도 (90°=위, 0°=앞)
    if release_idx > 0:
        prev_ld = valid[release_idx - 1][2]
        dx = release_ld["wrist"][0] - prev_ld["wrist"][0]
        dy = prev_ld["wrist"][1] - release_ld["wrist"][1]  # y 반전 (위가 +)
        if abs(dx) + abs(dy) > 1e-3:
            direction_angle = math.degrees(math.atan2(dy, abs(dx)))
            result["shot_direction_angle"] = round(max(0, min(90, direction_angle)), 1)

    return result


# ---------------------------------------------------------------------------
# 정면 영상 분석 (넷볼 전용)
# ---------------------------------------------------------------------------
def analyze_front_video(video_bytes: bytes):
    """
    정면 영상에서 좌우 정렬 + 어깨 수평을 분석한다.

    Returns dict:
        alignment_angle, shoulder_level_angle,
        front_frame, front_landmarks, error
    """
    result = {
        "alignment_angle": 0.0,
        "shoulder_level_angle": 0.0,
        "finger_direction_angle": 0.0,
        "front_frame": None,
        "front_landmarks": None,
        "error": None,
    }

    cap, tmp_path = _open_video(video_bytes)
    if not cap.isOpened():
        result["error"] = "정면 영상 파일을 열 수 없습니다."
        os.unlink(tmp_path)
        return result

    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    landmarker = _create_landmarker()
    raw_frames = _extract_raw_frames(cap, landmarker, fps)
    cap.release()
    landmarker.close()
    os.unlink(tmp_path)

    # 정면에서는 양쪽 어깨/팔꿈치/손목 + 검지(손끝 방향용) 필요
    valid = []
    for fi, frame, raw_lms in raw_frames:
        if raw_lms is None:
            continue
        # 11~16: 양쪽 어깨/팔꿈치/손목, 19~20: 양쪽 검지
        keys_to_check = [11, 12, 13, 14, 15, 16]
        if all(raw_lms[k].visibility >= MIN_VISIBILITY for k in keys_to_check):
            h, w = frame.shape[:2]
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
            valid.append((fi, frame, ld))

    if len(valid) < 2:
        result["error"] = (
            "정면 영상에서 자세를 감지할 수 없습니다. "
            "정면에서 한 사람만 촬영된 영상을 올려주세요."
        )
        return result

    # 릴리스 = 손목이 가장 높이 올라간 프레임
    release_idx = min(
        range(len(valid)),
        key=lambda i: min(valid[i][2]["r_wrist"][1], valid[i][2]["l_wrist"][1]),
    )
    ld = valid[release_idx][2]

    # 슛 팔 결정 (손목이 더 높은 쪽)
    if ld["r_wrist"][1] <= ld["l_wrist"][1]:
        shot_shoulder, shot_elbow, shot_wrist = ld["r_shoulder"], ld["r_elbow"], ld["r_wrist"]
        shot_index = ld["r_index"]
    else:
        shot_shoulder, shot_elbow, shot_wrist = ld["l_shoulder"], ld["l_elbow"], ld["l_wrist"]
        shot_index = ld["l_index"]

    # 좌우 정렬: 어깨-팔꿈치-손목의 x좌표가 수직선에서 얼마나 벗어나는지
    dx_elbow = abs(shot_elbow[0] - shot_shoulder[0])
    dy_elbow = abs(shot_shoulder[1] - shot_elbow[1]) + 1e-8
    alignment = math.degrees(math.atan2(dx_elbow, dy_elbow))
    result["alignment_angle"] = round(alignment, 1)

    # 어깨 수평: 양쪽 어깨의 y좌표 차이를 각도로
    shoulder_dx = abs(ld["r_shoulder"][0] - ld["l_shoulder"][0]) + 1e-8
    shoulder_dy = abs(ld["r_shoulder"][1] - ld["l_shoulder"][1])
    shoulder_tilt = math.degrees(math.atan2(shoulder_dy, shoulder_dx))
    result["shoulder_level_angle"] = round(shoulder_tilt, 1)

    # 손끝 방향: 손목→검지 벡터가 수직에서 얼마나 틀어져 있는지
    # 이상적: 검지가 손목 바로 위 → 0°, 옆으로 틀어지면 각도 증가
    finger_dx = abs(shot_index[0] - shot_wrist[0])
    finger_dy = abs(shot_wrist[1] - shot_index[1]) + 1e-8
    finger_angle = math.degrees(math.atan2(finger_dx, finger_dy))
    result["finger_direction_angle"] = round(finger_angle, 1)

    result["front_frame"] = valid[release_idx][1]
    result["front_landmarks"] = ld

    return result


# ---------------------------------------------------------------------------
# 스켈레톤 오버레이
# ---------------------------------------------------------------------------
def draw_skeleton(frame, landmarks, angles_text=None):
    """측면 프레임에 관절 점 + 연결선 + 각도 텍스트를 그린다."""
    img = frame.copy()
    connections = [
        ("shoulder", "elbow"), ("elbow", "wrist"),
        ("shoulder", "hip"), ("hip", "knee"), ("knee", "ankle"),
    ]
    for a, b in connections:
        if a in landmarks and b in landmarks:
            pt1 = tuple(map(int, landmarks[a]))
            pt2 = tuple(map(int, landmarks[b]))
            cv2.line(img, pt1, pt2, (0, 255, 128), 3)
    for key in REQUIRED_KEYS:
        if key in landmarks:
            pt = tuple(map(int, landmarks[key]))
            cv2.circle(img, pt, 7, (0, 140, 255), -1)
            cv2.circle(img, pt, 7, (255, 255, 255), 2)
    if angles_text:
        y_offset = 30
        for txt in angles_text:
            cv2.putText(img, txt, (15, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 30
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)


def draw_front_skeleton(frame, landmarks, angles_text=None):
    """정면 프레임에 양쪽 어깨/팔꿈치/손목을 그린다."""
    img = frame.copy()
    connections = [
        ("r_shoulder", "r_elbow"), ("r_elbow", "r_wrist"),
        ("l_shoulder", "l_elbow"), ("l_elbow", "l_wrist"),
        ("r_shoulder", "l_shoulder"),
    ]
    for a, b in connections:
        if a in landmarks and b in landmarks:
            pt1 = tuple(map(int, landmarks[a]))
            pt2 = tuple(map(int, landmarks[b]))
            cv2.line(img, pt1, pt2, (0, 255, 128), 3)
    for key in landmarks:
        pt = tuple(map(int, landmarks[key]))
        cv2.circle(img, pt, 7, (0, 140, 255), -1)
        cv2.circle(img, pt, 7, (255, 255, 255), 2)
    if angles_text:
        y_offset = 30
        for txt in angles_text:
            cv2.putText(img, txt, (15, y_offset),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            y_offset += 30
    return cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
