"""
feedback.py — 종목별 점수 변환 + BEST/YOUR FORM 피드백 생성

BEST: 운동역학 원리 기반 이상적 자세 설명 (초록)
YOUR FORM: 실제 측정값 기반 구체적 피드백 (빨강)
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


def calc_score(measured, ideal_min, ideal_max):
    if ideal_min <= measured <= ideal_max:
        return 100
    if measured < ideal_min:
        diff = ideal_min - measured
    else:
        diff = measured - ideal_max
    return max(0, round(100 - diff * PENALTY_PER_DEGREE))


# ===========================================================================
# BEST 설명 (운동역학 원리 — 종목 공통/개별)
# ===========================================================================
BEST_TEXT = {
    "basketball": {
        "elbow": (
            "릴리스 순간 팔꿈치는 150°~170°가 이상적이에요. "
            "완전히 펴지지 않고 '살짝 부드러운' 상태에서 손목 스냅이 마지막 가속을 만들어요. "
            "이것을 운동 사슬(kinetic chain)이라고 해요 — 다리→허리→어깨→팔꿈치→손목 순서로 "
            "에너지가 전달되면서 마지막에 손목이 공에 백스핀을 걸어줘요."
        ),
        "knee": (
            "슛 준비 시 무릎은 90°~120°로 구부리는 게 이상적이에요. "
            "이 깊이에서 대퇴사두근(허벅지 앞쪽 근육)이 가장 효율적으로 힘을 만들어요. "
            "무릎을 구부렸다 펴는 힘이 상체를 거쳐 팔까지 전달되어야 먼 거리에서도 "
            "편하게 슛할 수 있어요."
        ),
        "lean": (
            "슛할 때 상체는 수직에서 15° 이내로 유지하는 게 이상적이에요. "
            "상체가 곧으면 매번 같은 릴리스 포인트에서 공을 놓을 수 있어서 "
            "슛 일관성이 올라가요. 앞으로 기울면 포물선이 낮아지고, "
            "뒤로 기울면 힘 조절이 어려워져요."
        ),
    },
    "netball": {
        "elbow": (
            "릴리스 순간 팔꿈치는 150°~170°가 이상적이에요. "
            "넷볼은 슛을 위로 높이 쏘는 게 핵심이에요. 팔꿈치가 '거의 펴졌지만 살짝 부드러운' "
            "상태에서 손목 스냅으로 공을 위로 올리면, 수비수의 블로킹도 피하면서 "
            "부드러운 백스핀이 걸린 정확한 슛이 나와요."
        ),
        "knee": (
            "넷볼은 골대가 가까우니까 무릎을 100°~165° 정도로 가볍게 사용하면 돼요. "
            "너무 깊이 앉으면 올라오는 데 에너지를 낭비하고, 슛 리듬이 느려져요. "
            "살짝 구부렸다 펴는 리듬으로 하체의 작은 힘을 상체로 부드럽게 전달하는 게 포인트예요."
        ),
        "lean": (
            "상체는 수직에서 15° 이내로 곧게 유지하는 게 이상적이에요. "
            "넷볼은 공을 위로 쏘는 스포츠이므로, 상체가 기울면 공이 앞이나 "
            "옆으로 빠져요. 몸이 곧아야 공이 수직으로 올라가요."
        ),
        "shot_height": (
            "넷볼 슛은 머리 위에서 시작하는 게 이상적이에요. "
            "높은 위치에서 슛을 시작하면 수비수가 블로킹하기 어렵고, "
            "공이 높은 포물선을 그리면서 골대에 부드럽게 들어가요. "
            "공을 머리 위(정수리 높이)에서 잡고 시작하세요."
        ),
        "shot_direction": (
            "넷볼 슛은 앞이 아니라 위로 쏘는 게 핵심이에요 (이상적: 60°~90°). "
            "골대가 가까우니까 공을 멀리 보낼 필요가 없어요. "
            "위로 높이 쏘면 포물선이 커져서 골대 링에 부드럽게 빠지고, "
            "수비수의 블로킹도 넘길 수 있어요."
        ),
    },
    # 정면 분석 (농구/넷볼 공통)
    "common": {
        "alignment": (
            "정면에서 봤을 때 어깨→팔꿈치→손목이 수직 일직선(0°~10°)이면 이상적이에요. "
            "팔꿈치가 바깥으로 벌어지면(chicken wing) 공에 옆방향 힘이 가해져서 "
            "좌우로 빠지는 슛이 나와요. 팔꿈치가 어깨 바로 위에 있어야 "
            "공이 일직선으로 날아가요."
        ),
        "shoulder_level": (
            "양쪽 어깨는 수평(0°~5° 이내)을 유지하는 게 이상적이에요. "
            "슛 손 쪽 어깨가 올라가면 릴리스 포인트가 매번 달라지고, "
            "반대쪽이 올라가면 상체가 틀어져요. 어깨가 수평이어야 "
            "상체 회전 없이 곧은 슛이 나와요."
        ),
        "finger_direction": (
            "릴리스 후 검지(집게손가락)가 골대 정중앙을 가리키는 게 이상적이에요 (0°~10°). "
            "이것을 '팔로우 스루(follow through)'라고 해요. 손끝이 목표를 향하면 "
            "공에 정확한 방향의 백스핀이 걸리고, 좌우 편차 없이 반듯하게 날아가요."
        ),
    },
}


# ===========================================================================
# YOUR FORM 피드백 (실제 측정값 기반 구체적 피드백)
# ===========================================================================
def _your_form_elbow(angle, score, sport):
    if score == 100:
        return f"팔꿈치 각도가 {angle}°로 이상적인 범위 안에 있어요. 이 느낌 그대로 유지하세요!"
    if angle < CRITERIA[sport]["elbow"]["ideal_min"]:
        if score >= 70:
            return (
                f"현재 {angle}°로 팔이 조금 접혀 있어요. "
                f"공을 놓을 때 팔을 조금만 더 뻗으면서 손목 스냅으로 마무리해보세요."
            )
        return (
            f"현재 {angle}°로 팔이 많이 접혀 있어요. "
            f"연습법: 공 없이 벽 앞에서 팔을 하늘로 쭉 뻗는 동작을 반복하세요. "
            f"팔이 귀 옆까지 올라가는 느낌이면 딱 좋아요."
        )
    if score >= 70:
        return (
            f"현재 {angle}°로 팔이 약간 과하게 펴져 있어요. "
            f"팔꿈치가 완전히 잠기면 손목 스냅 타이밍을 놓칠 수 있어요. "
            f"살짝 부드럽게 유지하면서 손목으로 마무리해보세요."
        )
    return (
        f"현재 {angle}°로 팔이 과신전(hyperextension)되고 있어요. "
        f"팔꿈치 관절에 무리가 갈 수 있고, 힘으로 던지는 느낌이 돼요. "
        f"연습법: 팔을 자연스럽게 올리고 '팔꿈치가 부드럽게 펴지는 느낌'에서 손목 스냅!"
    )


def _your_form_knee(angle, score, sport):
    c = CRITERIA[sport]["knee"]
    if score == 100:
        return f"무릎 각도가 {angle}°로 이상적이에요. 하체 힘이 잘 전달되고 있어요!"
    if angle < c["ideal_min"]:
        if score >= 70:
            return f"현재 {angle}°로 무릎을 조금 많이 구부리고 있어요. 살짝만 덜 앉아도 충분해요."
        if sport == "basketball":
            return (
                f"현재 {angle}°로 너무 깊이 앉고 있어요. "
                f"연습법: 의자에 살짝 걸터앉는 깊이에서 바로 점프하며 슛하는 연습을 해보세요."
            )
        return (
            f"현재 {angle}°로 너무 많이 구부리고 있어요. "
            f"넷볼은 가까운 거리라 가볍게 구부리면 돼요. 리듬감 있게 살짝만!"
        )
    if score >= 70:
        if sport == "basketball":
            return (
                f"현재 {angle}°로 무릎을 조금 더 구부려야 해요. "
                f"다리를 더 굽히면 점프할 때 힘이 더 실려서 공이 편하게 날아가요."
            )
        return f"현재 {angle}°로 다리를 살짝 더 구부려서 리듬을 타보세요."
    if sport == "basketball":
        return (
            f"현재 {angle}°로 거의 서서 쏘고 있어요! "
            f"연습법: '앉았다 일어나면서 던진다'는 느낌으로 무릎을 구부렸다 펴는 힘을 사용하세요."
        )
    return (
        f"현재 {angle}°로 다리를 거의 안 쓰고 있어요. "
        f"살짝만 구부렸다 펴면서 그 리듬에 맞춰 공을 올려보세요."
    )


def _your_form_lean(angle, score, sport):
    if score == 100:
        return f"상체 기울기 {angle}°로 반듯하게 유지하고 있어요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 상체가 살짝 기울어져 있어요. "
            f"슛할 때 배꼽이 골대를 향하도록 의식하면 몸이 곧아져요."
        )
    return (
        f"현재 {angle}°로 상체가 많이 기울어져 있어요. "
        f"연습법: 슛 전에 발끝-무릎-배꼽-코가 일직선인지 체크하세요. "
        f"이 일직선을 유지하면서 쏘는 연습을 반복하세요."
    )


def _your_form_shot_height(is_above_head, is_in_front=False):
    if is_above_head:
        return "슛 시작 위치가 머리 위에 있어요. 완벽해요!"
    if is_in_front:
        return (
            "공 높이는 충분하지만, 머리 '앞'에 있어요. 머리 '위(정수리 위)'에 있어야 해요! "
            "앞에 있으면 수비수가 블로킹할 수 있어요. "
            "연습법: 거울 옆에서 측면을 보면서, 공이 머리 앞이 아니라 "
            "정수리 위에 올라가 있는지 확인하세요. "
            "팔꿈치를 얼굴 옆에 붙이고 공을 머리 위로 들어올리는 느낌이에요."
        )
    return (
        "슛 시작 위치가 머리보다 낮아요. "
        "연습법: 공을 머리 위로 올린 상태에서 슛을 시작하세요. "
        "거울 앞에서 공이 머리 위(정수리 높이)에 있는지 확인하며 연습하면 좋아요."
    )


def _your_form_shot_direction(angle, score):
    if score == 100:
        return f"슛 방향이 {angle}°로 공이 위로 잘 올라가고 있어요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 공이 약간 앞쪽으로 나가고 있어요. "
            f"손목을 위로 꺾어서 공을 하늘로 올린다는 느낌으로 쏴보세요."
        )
    return (
        f"현재 {angle}°로 공이 앞으로 던져지고 있어요. "
        f"연습법: 벽 바로 앞에 서서 공이 벽에 안 닿게 위로만 쏘는 연습을 하세요. "
        f"자연스럽게 위로 쏘는 감각이 생겨요."
    )


def _your_form_alignment(angle, score):
    if score == 100:
        return f"팔 정렬이 {angle}°로 반듯한 일직선이에요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 팔꿈치가 살짝 바깥으로 벌어져 있어요. "
            f"팔꿈치-손목-손가락이 일직선이 되도록 의식해보세요."
        )
    return (
        f"현재 {angle}°로 팔꿈치가 많이 벌어져 있어요 (치킨윙). "
        f"연습법: 거울 앞에서 정면으로 서서 팔꿈치가 바깥으로 벌어지지 않는지 체크하세요."
    )


def _your_form_shoulder_level(angle, score):
    if score == 100:
        return f"어깨가 {angle}°로 수평을 잘 유지하고 있어요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 어깨가 살짝 기울어져 있어요. "
            f"양쪽 어깨 높이를 맞춰보세요. 한쪽이 올라가면 공도 그쪽으로 빠져요."
        )
    return (
        f"현재 {angle}°로 어깨가 많이 기울어져 있어요. "
        f"연습법: 슛 전에 어깨를 한 번 으쓱한 다음 내려놓으세요. 그 상태가 수평이에요."
    )


def _your_form_finger(angle, score):
    if score == 100:
        return f"손끝 방향이 {angle}°로 골대를 정확히 가리키고 있어요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 손끝이 살짝 틀어져 있어요. "
            f"공을 놓을 때 검지가 골대 정중앙을 가리키도록 의식해보세요."
        )
    return (
        f"현재 {angle}°로 손끝이 많이 틀어져 있어요. "
        f"연습법: 슛 후 손가락이 림 정중앙을 가리킨 채로 2초간 멈춰보세요. "
        f"이 팔로우 스루 자세를 반복하면 손끝 방향이 잡혀요."
    )


# ===========================================================================
# 통합 함수
# ===========================================================================
def generate_feedback(sport, **kwargs):
    c = CRITERIA[sport]
    result = {}

    # --- 측면 영상 지표 ---
    if "elbow_angle" in kwargs:
        elbow = kwargs["elbow_angle"]
        knee = kwargs["knee_angle"]
        lean = kwargs["lean_angle"]

        result["elbow_score"] = calc_score(elbow, c["elbow"]["ideal_min"], c["elbow"]["ideal_max"])
        result["knee_score"] = calc_score(knee, c["knee"]["ideal_min"], c["knee"]["ideal_max"])
        result["lean_score"] = calc_score(lean, c["lean"]["ideal_min"], c["lean"]["ideal_max"])

        result["elbow_best"] = BEST_TEXT[sport]["elbow"]
        result["knee_best"] = BEST_TEXT[sport]["knee"]
        result["lean_best"] = BEST_TEXT[sport]["lean"]

        result["elbow_yourform"] = _your_form_elbow(elbow, result["elbow_score"], sport)
        result["knee_yourform"] = _your_form_knee(knee, result["knee_score"], sport)
        result["lean_yourform"] = _your_form_lean(lean, result["lean_score"], sport)

        if sport == "netball":
            above = kwargs.get("shot_height_above_head", False)
            in_front = kwargs.get("shot_height_in_front", False)
            if above:
                result["shot_height_score"] = 100
            elif in_front:
                result["shot_height_score"] = 50  # 높이는 OK지만 앞에 있음
            else:
                result["shot_height_score"] = 30  # 높이도 부족
            result["shot_height_best"] = BEST_TEXT["netball"]["shot_height"]
            result["shot_height_yourform"] = _your_form_shot_height(above, in_front)

            sd = kwargs.get("shot_direction_angle", 90)
            result["shot_direction_score"] = calc_score(sd, c["shot_direction"]["ideal_min"], c["shot_direction"]["ideal_max"])
            result["shot_direction_best"] = BEST_TEXT["netball"]["shot_direction"]
            result["shot_direction_yourform"] = _your_form_shot_direction(sd, result["shot_direction_score"])

    # --- 정면 영상 지표 ---
    if "alignment_angle" in kwargs:
        al = kwargs["alignment_angle"]
        sl = kwargs.get("shoulder_level_angle", 0)
        fd = kwargs.get("finger_direction_angle", 0)

        result["alignment_score"] = calc_score(al, c["alignment"]["ideal_min"], c["alignment"]["ideal_max"])
        result["shoulder_level_score"] = calc_score(sl, c["shoulder_level"]["ideal_min"], c["shoulder_level"]["ideal_max"])
        result["finger_direction_score"] = calc_score(fd, c["finger_direction"]["ideal_min"], c["finger_direction"]["ideal_max"])

        result["alignment_best"] = BEST_TEXT["common"]["alignment"]
        result["shoulder_level_best"] = BEST_TEXT["common"]["shoulder_level"]
        result["finger_direction_best"] = BEST_TEXT["common"]["finger_direction"]

        result["alignment_yourform"] = _your_form_alignment(al, result["alignment_score"])
        result["shoulder_level_yourform"] = _your_form_shoulder_level(sl, result["shoulder_level_score"])
        result["finger_direction_yourform"] = _your_form_finger(fd, result["finger_direction_score"])

    return result
