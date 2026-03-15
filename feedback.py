"""
feedback.py — 종목별 점수 변환 + 한국어 피드백 생성

종목: basketball (농구), netball (넷볼)
"""

# ---------------------------------------------------------------------------
# 종목별 기준 상수
# ---------------------------------------------------------------------------
CRITERIA = {
    "basketball": {
        "elbow": {"name": "팔꿈치 각도", "ideal_min": 150, "ideal_max": 170},
        "knee": {"name": "무릎 각도", "ideal_min": 90, "ideal_max": 120},
        "lean": {"name": "상체 기울기", "ideal_min": 0, "ideal_max": 15},
        "alignment": {"name": "좌우 정렬", "ideal_min": 0, "ideal_max": 10},
        "shoulder_level": {"name": "어깨 수평", "ideal_min": 0, "ideal_max": 5},
        "finger_direction": {"name": "손끝 방향", "ideal_min": 0, "ideal_max": 10},
    },
    "netball": {
        "elbow": {"name": "팔꿈치 각도", "ideal_min": 150, "ideal_max": 170},
        "knee": {"name": "무릎 각도", "ideal_min": 100, "ideal_max": 165},
        "lean": {"name": "상체 기울기", "ideal_min": 0, "ideal_max": 15},
        "shot_height": {"name": "슛 시작 높이", "ideal": "머리 위"},
        "shot_direction": {"name": "슛 방향 (위로)", "ideal_min": 60, "ideal_max": 90},
        "alignment": {"name": "좌우 정렬", "ideal_min": 0, "ideal_max": 10},
        "shoulder_level": {"name": "어깨 수평", "ideal_min": 0, "ideal_max": 5},
        "finger_direction": {"name": "손끝 방향", "ideal_min": 0, "ideal_max": 10},
    },
}

PENALTY_PER_DEGREE = 3


# ---------------------------------------------------------------------------
# 점수 계산
# ---------------------------------------------------------------------------
def calc_score(measured, ideal_min, ideal_max):
    """이상 범위 대비 점수(0~100)를 반환한다."""
    if ideal_min <= measured <= ideal_max:
        return 100
    if measured < ideal_min:
        diff = ideal_min - measured
    else:
        diff = measured - ideal_max
    return max(0, round(100 - diff * PENALTY_PER_DEGREE))


# ===========================================================================
# 농구 피드백
# ===========================================================================
def _basketball_elbow(angle, score):
    if score == 100:
        return (
            f"팔 펴기 아주 잘하고 있어요! "
            f"공을 놓는 순간 팔이 쭉 펴져 있어서 정확한 슛이 나올 수 있어요. (현재 {angle}°)"
        )
    if angle < 150:
        if score >= 70:
            return (
                f"거의 다 됐어요! 공을 놓을 때 팔을 조금만 더 쭉 펴보세요. "
                f"팔을 끝까지 뻗으면서 손목을 툭 꺾어주는 느낌으로 던져보세요. (현재 {angle}°)"
            )
        return (
            f"공을 놓을 때 팔이 접혀 있어요. "
            f"연습 방법: 벽 앞에 서서 공 없이 팔을 하늘로 쭉 뻗는 동작을 반복해보세요. "
            f"팔이 귀 옆까지 올라가는 느낌이면 딱 좋아요! (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"팔이 너무 쭉 펴져서 힘이 빠져나가고 있어요. "
            f"팔꿈치가 살짝 부드럽게 굽혀진 상태에서 손목 스냅으로 공을 보내보세요. (현재 {angle}°)"
        )
    return (
        f"팔을 너무 세게 펴고 있어요. 힘으로 던지는 느낌이 되면 정확도가 떨어져요. "
        f"팔을 자연스럽게 올리고, 손목 스냅으로 가볍게 날려보세요. (현재 {angle}°)"
    )


def _basketball_knee(angle, score):
    if score == 100:
        return (
            f"무릎 구부리기 딱 좋아요! "
            f"다리에서 나오는 힘이 공까지 잘 전달되고 있어요. (현재 {angle}°)"
        )
    if angle < 90:
        if score >= 70:
            return (
                f"무릎을 조금 덜 구부려도 돼요. "
                f"너무 깊이 앉으면 올라오는 데 힘을 많이 써서 슛이 불안정해질 수 있어요. (현재 {angle}°)"
            )
        return (
            f"무릎을 너무 많이 구부리고 있어요. "
            f"연습 방법: 의자에 살짝 걸터앉는 정도만 구부려보세요. "
            f"그 높이에서 바로 점프하면서 슛하는 연습을 해보세요! (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"무릎을 조금 더 구부려보세요. "
            f"다리를 살짝 더 굽히면 점프할 때 힘이 더 실려서 공이 편하게 날아가요. (현재 {angle}°)"
        )
    return (
        f"거의 서서 쏘고 있어요! 다리 힘을 못 쓰면 팔로만 던지게 돼요. "
        f"연습 방법: 슛 전에 '앉았다 일어나면서 던진다'는 느낌으로 해보세요. "
        f"무릎을 구부렸다가 펴는 힘으로 공을 밀어올리는 거예요! (현재 {angle}°)"
    )


def _basketball_lean(angle, score):
    if score == 100:
        return (
            f"상체가 잘 세워져 있어요! "
            f"몸이 곧으면 매번 같은 자세로 쏠 수 있어서 슛이 일정해져요. (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"상체가 살짝 기울어져 있어요. "
            f"슛할 때 배꼽이 림을 향하도록 의식해보세요. "
            f"몸이 곧으면 공이 더 일직선으로 날아가요. (현재 {angle}°)"
        )
    return (
        f"상체가 많이 기울어져 있어요. 몸이 기울면 슛이 매번 달라질 수 있어요. "
        f"연습 방법: 슛 전에 발끝-무릎-배꼽-코가 일직선이 되는지 체크해보세요. "
        f"이 일직선을 유지하면서 쏘는 연습을 해보세요! (현재 {angle}°)"
    )


# ===========================================================================
# 넷볼 피드백
# ===========================================================================
def _netball_elbow(angle, score):
    if score == 100:
        return (
            f"팔 펴기 완벽해요! "
            f"공을 위로 밀어올리면서 팔이 쭉 펴져 있어서 블로킹도 피할 수 있어요. (현재 {angle}°)"
        )
    if angle < 150:
        if score >= 70:
            return (
                f"거의 다 됐어요! 공을 놓을 때 팔을 조금만 더 위로 뻗어보세요. "
                f"팔을 앞이 아니라 하늘 쪽으로 뻗는 느낌이 중요해요. (현재 {angle}°)"
            )
        return (
            f"팔이 많이 접혀 있어요. 넷볼은 슛을 위로 높이 쏘는 게 중요해요. "
            f"연습 방법: 공 없이 머리 위에서 하늘로 팔을 쭉 뻗는 동작을 반복해보세요. "
            f"팔을 앞이 아니라 위로 뻗어야 블로킹을 피할 수 있어요! (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"팔이 조금 과하게 펴져 있어요. "
            f"손목 스냅으로 부드럽게 공을 날려보세요. 힘은 손목에서! (현재 {angle}°)"
        )
    return (
        f"팔이 너무 세게 펴져 있어요. "
        f"넷볼 슛은 힘보다 부드러운 손목 스냅이 중요해요. "
        f"팔을 자연스럽게 뻗고 손목으로 백스핀을 걸어보세요. (현재 {angle}°)"
    )


def _netball_knee(angle, score):
    if score == 100:
        return (
            f"무릎 사용이 적절해요! "
            f"넷볼은 거리가 가까우니까 가볍게 무릎을 써서 리듬을 타는 게 좋아요. (현재 {angle}°)"
        )
    if angle < 100:
        if score >= 70:
            return (
                f"무릎을 조금 덜 구부려도 돼요. "
                f"넷볼은 가까운 거리에서 쏘니까 가볍게 구부리는 정도면 충분해요. (현재 {angle}°)"
            )
        return (
            f"무릎을 너무 많이 구부리고 있어요. "
            f"넷볼은 골대가 가까우니까 깊이 앉을 필요가 없어요. "
            f"연습 방법: 살짝만 무릎을 굽히고 리듬감 있게 쏘는 연습을 해보세요! (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"무릎을 살짝만 더 구부려보세요. "
            f"다리를 약간만 굽혀도 슛에 리듬이 생겨서 더 부드럽게 쏠 수 있어요. (현재 {angle}°)"
        )
    return (
        f"다리를 거의 안 쓰고 있어요. "
        f"연습 방법: 무릎을 살짝 굽혔다 펴면서 그 리듬에 맞춰 공을 올려보세요. "
        f"다리의 작은 힘이 슛을 더 편하게 만들어줘요! (현재 {angle}°)"
    )


def _netball_lean(angle, score):
    if score == 100:
        return (
            f"상체가 잘 세워져 있어요! "
            f"몸이 곧아야 공이 위로 반듯하게 올라가요. (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"상체가 살짝 기울어져 있어요. "
            f"넷볼 슛은 위로 쏘는 게 핵심이니까 몸을 곧게 세워보세요. (현재 {angle}°)"
        )
    return (
        f"상체가 많이 기울어져 있어요. 몸이 기울면 공이 옆으로 빠질 수 있어요. "
        f"연습 방법: 양발을 어깨 너비로 벌리고 배꼽이 골대를 향하게 선 다음 쏴보세요! (현재 {angle}°)"
    )


def _netball_shot_height(is_above_head, score):
    if is_above_head:
        return (
            "슛 시작 위치가 머리 위에 있어서 완벽해요! "
            "높은 위치에서 시작하면 수비수가 블로킹하기 어려워요."
        )
    return (
        "슛 시작 위치가 머리보다 낮아요. "
        "연습 방법: 공을 머리 위로 올린 상태에서 슛을 시작해보세요. "
        "거울 앞에서 공이 이마 위에 있는지 확인하면서 연습하면 좋아요!"
    )


def _netball_shot_direction(angle, score):
    if score == 100:
        return (
            f"공이 위로 잘 올라가고 있어요! "
            f"앞으로 던지는 게 아니라 위로 쏘는 느낌이 잘 나와요. (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"공이 약간 앞쪽으로 나가고 있어요. "
            f"손목을 위로 꺾어서 공을 하늘로 올린다는 느낌으로 쏴보세요. (현재 {angle}°)"
        )
    return (
        f"공이 앞으로 던져지고 있어요. 넷볼은 위로 높이 쏘는 게 중요해요! "
        f"연습 방법: 벽 바로 앞에 서서 공이 벽에 안 닿게 위로만 쏘는 연습을 해보세요. "
        f"자연스럽게 위로 쏘는 감각이 생겨요! (현재 {angle}°)"
    )


def _netball_alignment(angle, score):
    if score == 100:
        return (
            f"팔이 반듯하게 일직선이에요! "
            f"공이 좌우로 흔들리지 않고 똑바로 날아갈 수 있어요. (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"팔이 살짝 옆으로 틀어져 있어요. "
            f"팔꿈치-손목-손가락이 일직선이 되도록 의식해보세요. (현재 {angle}°)"
        )
    return (
        f"팔이 많이 옆으로 틀어져 있어요. 이러면 공이 좌우로 빠질 수 있어요. "
        f"연습 방법: 거울 앞에서 정면으로 서서, 팔꿈치가 바깥으로 벌어지지 않는지 "
        f"체크하면서 슛 동작을 해보세요! (현재 {angle}°)"
    )


def _netball_shoulder_level(angle, score):
    if score == 100:
        return (
            f"어깨가 수평으로 잘 유지되고 있어요! "
            f"어깨가 반듯해야 슛이 일정해져요. (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"어깨가 살짝 기울어져 있어요. "
            f"양쪽 어깨 높이를 맞춰보세요. 한쪽이 올라가면 공도 그쪽으로 빠져요. (현재 {angle}°)"
        )
    return (
        f"어깨가 많이 기울어져 있어요. "
        f"연습 방법: 슛 전에 양쪽 어깨를 한 번 으쓱한 다음 내려놓으세요. "
        f"그 상태가 수평이에요. 그 느낌을 유지하면서 쏴보세요! (현재 {angle}°)"
    )


def _finger_direction_feedback(angle, score):
    """농구/넷볼 공통 — 손끝 방향 피드백."""
    if score == 100:
        return (
            f"손끝이 골대를 향해 반듯하게 나가고 있어요! "
            f"이 느낌 그대로 유지하면 공이 일직선으로 날아가요. (현재 {angle}°)"
        )
    if score >= 70:
        return (
            f"손끝이 살짝 옆으로 틀어져 있어요. "
            f"공을 놓을 때 검지가 골대 정중앙을 가리키도록 의식해보세요. "
            f"팔로우 스루 할 때 손가락이 림을 가리키면 딱 좋아요! (현재 {angle}°)"
        )
    return (
        f"손끝이 많이 틀어져 있어요. 이러면 공이 좌우로 빠질 수 있어요. "
        f"연습 방법: 슛 후 손가락이 림 정중앙을 가리킨 채로 2초간 멈춰보세요. "
        f"이 '팔로우 스루' 자세를 기억하면서 반복 연습하면 손끝 방향이 잡혀요! (현재 {angle}°)"
    )


# ===========================================================================
# 통합 함수
# ===========================================================================
def generate_feedback(sport, **kwargs):
    """
    종목에 따라 피드백을 생성한다.

    basketball: elbow_angle, knee_angle, lean_angle
    netball:    elbow_angle, knee_angle, lean_angle,
                shot_height_above_head (bool), shot_direction_angle,
                alignment_angle, shoulder_level_angle
    """
    c = CRITERIA[sport]
    result = {}

    # --- 측면 영상 지표 (있을 때만) ---
    if "elbow_angle" in kwargs:
        elbow = kwargs["elbow_angle"]
        knee = kwargs["knee_angle"]
        lean = kwargs["lean_angle"]

        elbow_score = calc_score(elbow, c["elbow"]["ideal_min"], c["elbow"]["ideal_max"])
        knee_score = calc_score(knee, c["knee"]["ideal_min"], c["knee"]["ideal_max"])
        lean_score = calc_score(lean, c["lean"]["ideal_min"], c["lean"]["ideal_max"])

        result["elbow_score"] = elbow_score
        result["knee_score"] = knee_score
        result["lean_score"] = lean_score

        if sport == "basketball":
            result["elbow_feedback"] = _basketball_elbow(elbow, elbow_score)
            result["knee_feedback"] = _basketball_knee(knee, knee_score)
            result["lean_feedback"] = _basketball_lean(lean, lean_score)
        elif sport == "netball":
            result["elbow_feedback"] = _netball_elbow(elbow, elbow_score)
            result["knee_feedback"] = _netball_knee(knee, knee_score)
            result["lean_feedback"] = _netball_lean(lean, lean_score)

            # 슛 시작 높이
            above = kwargs.get("shot_height_above_head", False)
            result["shot_height_score"] = 100 if above else 30
            result["shot_height_feedback"] = _netball_shot_height(above, result["shot_height_score"])

            # 슛 방향
            sd = kwargs.get("shot_direction_angle", 90)
            sd_score = calc_score(sd, c["shot_direction"]["ideal_min"], c["shot_direction"]["ideal_max"])
            result["shot_direction_score"] = sd_score
            result["shot_direction_feedback"] = _netball_shot_direction(sd, sd_score)

    # --- 정면 영상 지표 (있을 때만, 농구/넷볼 공통) ---
    if "alignment_angle" in kwargs:
        al = kwargs["alignment_angle"]
        al_score = calc_score(al, c["alignment"]["ideal_min"], c["alignment"]["ideal_max"])
        result["alignment_score"] = al_score
        result["alignment_feedback"] = _netball_alignment(al, al_score)

        sl = kwargs.get("shoulder_level_angle", 0)
        sl_score = calc_score(sl, c["shoulder_level"]["ideal_min"], c["shoulder_level"]["ideal_max"])
        result["shoulder_level_score"] = sl_score
        result["shoulder_level_feedback"] = _netball_shoulder_level(sl, sl_score)

        fd = kwargs.get("finger_direction_angle", 0)
        fd_score = calc_score(fd, c["finger_direction"]["ideal_min"], c["finger_direction"]["ideal_max"])
        result["finger_direction_score"] = fd_score
        result["finger_direction_feedback"] = _finger_direction_feedback(fd, fd_score)

    return result
