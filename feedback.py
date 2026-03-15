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
        "shot_direction": {"name": "슛 방향 (위로)", "ideal_min": 65, "ideal_max": 80},
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
            "슛을 놓는 순간 팔꿈치는 '거의 펴졌지만 살짝 여유 있는' 상태(150°~170°)가 가장 좋아요. "
            "완전히 펴버리면(180°) 팔이 '잠겨서' 손목으로 미세 조정을 할 수 없어요. "
            "살짝 여유를 남기면 다리→허리→어깨→팔꿈치→손목 순서로 힘이 자연스럽게 전달되고, "
            "마지막에 손목이 공에 부드러운 백스핀을 걸어줘요."
        ),
        "knee": (
            "슛 준비할 때 무릎은 '의자에 살짝 걸터앉는 정도'(90°~120°)가 가장 좋아요. "
            "이 깊이에서 허벅지 앞쪽 근육이 가장 효율적으로 힘을 만들어요. "
            "무릎을 구부렸다 펴는 힘이 상체를 거쳐 팔까지 전달되어야 "
            "먼 거리에서도 힘들이지 않고 슛할 수 있어요."
        ),
        "lean": (
            "슛할 때 상체는 거의 곧게(수직에서 15° 이내) 유지하는 게 이상적이에요. "
            "상체가 곧으면 매번 같은 위치에서 공을 놓을 수 있어서 슛이 일정해져요. "
            "앞으로 기울면 공이 낮게 날아가고, 뒤로 기울면 힘 조절이 어려워요. "
            "발끝-무릎-배꼽-코가 일직선이라고 생각하면 쉬워요."
        ),
    },
    "netball": {
        "elbow": (
            "슛을 놓는 순간 팔꿈치는 '거의 펴졌지만 살짝 여유 있는' 상태(150°~170°)가 가장 좋아요. "
            "넷볼은 공을 위로 높이 올리는 게 핵심인데, 팔꿈치를 완전히 펴버리면 "
            "손목 스냅을 할 수 없어서 방향 조절이 안 돼요. "
            "살짝 여유를 남기고 손목으로 공을 위로 밀어올리면, "
            "수비수 블로킹도 피하고 부드러운 백스핀도 걸 수 있어요."
        ),
        "knee": (
            "넷볼은 골대가 가까우니까 무릎을 '살짝만' 구부리면(100°~165°) 충분해요. "
            "너무 깊이 앉으면 올라오는 데 에너지를 낭비하고, 슛 타이밍이 느려져요. "
            "가볍게 구부렸다 펴는 리듬으로 하체의 작은 힘을 팔까지 부드럽게 전달하는 게 포인트예요. "
            "'톡' 하고 가볍게 튀어오르는 느낌이면 딱 좋아요."
        ),
        "lean": (
            "상체는 거의 곧게(수직에서 15° 이내) 유지하는 게 이상적이에요. "
            "넷볼은 공을 위로 쏘는 스포츠라서, 상체가 기울면 공도 같이 기울어져 나가요. "
            "몸을 곧게 세우면 공이 수직으로 올라가서 골대에 정확히 떨어져요. "
            "발끝부터 머리까지 '기둥'처럼 서 있다고 생각하세요."
        ),
        "shot_height": (
            "넷볼 슛은 머리 위(정수리 높이)에서 시작하는 게 가장 좋아요. "
            "높은 위치에서 슛을 시작하면 수비수가 손을 뻗어도 블로킹하기 어렵고, "
            "공이 높은 포물선을 그리면서 골대에 부드럽게 들어가요. "
            "공을 이마 앞이 아닌 머리 '위'에 올려놓고 시작하세요!"
        ),
        "shot_direction": (
            "넷볼 슛에서 팔이 향하는 각도는 65°~80°가 이상적이에요. "
            "완전히 위로(90°)만 쏘면 공이 골대까지 못 미치고, "
            "너무 앞으로(60° 이하) 던지면 포물선이 낮아서 블로킹에 걸려요. "
            "약간 앞을 향해 높이 올린다는 느낌(70°~80°)으로 쏘면, "
            "공이 위에서 아래로 떨어지면서 링에 쏙 들어가요. "
            "넷볼 골대는 백보드가 없으니 위에서 내려오는 각도가 아주 중요해요!"
        ),
    },
    # 정면 분석 (농구/넷볼 공통)
    "common": {
        "alignment": (
            "정면에서 봤을 때 어깨→팔꿈치→손목이 수직 일직선(0°~10°)이면 이상적이에요. "
            "팔꿈치가 바깥으로 벌어지면 공에 옆방향 힘이 가해져서 좌우로 빠지는 슛이 돼요. "
            "거울 앞에서 '팔꿈치가 어깨 바로 위에 있는지' 확인해보세요. "
            "일직선이 되면 공이 골대를 향해 반듯하게 날아가요."
        ),
        "shoulder_level": (
            "양쪽 어깨는 수평(0°~5° 이내)을 유지하는 게 이상적이에요. "
            "한쪽 어깨가 올라가면 공도 그쪽으로 빠져요. 마치 양팔저울처럼 "
            "양쪽이 같은 높이여야 몸이 틀어지지 않고 곧은 슛이 나와요. "
            "슛 전에 어깨를 한 번 으쓱했다 내려놓으면 자연스럽게 수평이 돼요."
        ),
        "finger_direction": (
            "공을 놓은 뒤 집게손가락이 골대 정중앙을 가리키는 게 이상적이에요(0°~10°). "
            "이걸 '팔로우 스루'라고 하는데, 쉽게 말하면 '과자 통 맨 위 과자를 꺼내는 손 모양'이에요. "
            "손끝이 목표를 향하면 공에 정확한 방향의 백스핀이 걸리고, "
            "좌우로 빠지지 않고 반듯하게 날아가요."
        ),
    },
}


# ===========================================================================
# YOUR FORM 피드백 (실제 측정값 기반 구체적 피드백)
# ===========================================================================
def _your_form_elbow(angle, score, sport):
    if score == 100:
        return f"팔꿈치 각도가 {angle}°로 딱 좋아요! 이 느낌 그대로 유지하세요!"
    if angle < CRITERIA[sport]["elbow"]["ideal_min"]:
        if score >= 70:
            return (
                f"현재 {angle}°로 팔이 조금 접혀 있어요. "
                f"공을 놓을 때 팔을 조금만 더 뻗어보세요. '하늘에 손을 뻗는다'는 느낌이면 좋아요."
            )
        return (
            f"현재 {angle}°로 팔이 많이 접혀 있어요. 팔힘으로만 던지는 느낌이 나고 있어요. "
            f"연습 팁: 공 없이 벽 앞에서 팔을 하늘로 쭉 뻗는 동작을 반복해보세요. "
            f"팔이 귀 옆까지 올라가는 느낌이면 딱이에요!"
        )
    if score >= 70:
        return (
            f"현재 {angle}°로 팔이 약간 과하게 펴져 있어요. "
            f"팔꿈치가 완전히 '잠기면' 손목으로 방향을 조절할 수 없어요. "
            f"팔을 살짝 부드럽게 유지한 채로 손목 스냅으로 마무리해보세요."
        )
    return (
        f"현재 {angle}°로 팔이 너무 펴지고 있어요. "
        f"팔꿈치에 무리가 갈 수 있고, '던지는' 느낌이 되어 정확도가 떨어져요. "
        f"연습 팁: 팔을 자연스럽게 올리고 '부드럽게 펴지는 느낌'에서 손목 스냅! "
        f"힘을 빼는 게 핵심이에요."
    )


def _your_form_knee(angle, score, sport):
    c = CRITERIA[sport]["knee"]
    if score == 100:
        return f"무릎 각도가 {angle}°로 딱 좋아요! 다리 힘이 잘 전달되고 있어요!"
    if angle < c["ideal_min"]:
        if score >= 70:
            return f"현재 {angle}°로 무릎을 조금 많이 구부리고 있어요. 살짝만 덜 앉아도 충분해요."
        if sport == "basketball":
            return (
                f"현재 {angle}°로 너무 깊이 앉고 있어요. 올라오는 데 힘을 다 써버려요. "
                f"연습 팁: 의자에 살짝 걸터앉는 깊이에서 바로 점프하며 슛하는 연습을 해보세요. "
                f"그 정도가 딱 적당한 깊이예요!"
            )
        return (
            f"현재 {angle}°로 너무 많이 구부리고 있어요. "
            f"넷볼은 가까운 거리라 가볍게 구부리면 돼요. "
            f"'톡' 하고 가볍게 튀어오르는 느낌으로 리듬감 있게 해보세요!"
        )
    if score >= 70:
        if sport == "basketball":
            return (
                f"현재 {angle}°로 무릎을 조금 더 구부려야 해요. "
                f"다리를 더 굽히면 점프할 때 스프링처럼 힘이 실려서 공이 편하게 날아가요."
            )
        return f"현재 {angle}°로 다리를 살짝 더 구부려서 리듬을 타보세요. 가볍게 '톡'!"
    if sport == "basketball":
        return (
            f"현재 {angle}°로 거의 서서 쏘고 있어요! 다리 힘을 전혀 못 쓰고 있어요. "
            f"연습 팁: '앉았다 일어나면서 던진다'는 느낌으로 해보세요. "
            f"무릎에서 나오는 힘이 공까지 전달되면 훨씬 편해져요!"
        )
    return (
        f"현재 {angle}°로 다리를 거의 안 쓰고 있어요. "
        f"살짝만 구부렸다 펴면서 그 타이밍에 맞춰 공을 올려보세요. "
        f"다리 리듬과 팔 동작이 하나로 연결되는 느낌이 중요해요!"
    )


def _your_form_lean(angle, score, sport):
    if score == 100:
        return f"상체 기울기 {angle}°로 반듯해요! 안정적인 자세예요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 상체가 살짝 기울어져 있어요. "
            f"슛할 때 배꼽이 골대를 향하도록 의식해보세요. 배꼽 방향만 잡아도 몸이 곧아져요."
        )
    return (
        f"현재 {angle}°로 상체가 많이 기울어져 있어요. 이러면 공이 매번 다른 곳으로 가요. "
        f"연습 팁: 슛 전에 '발끝-무릎-배꼽-코'가 일직선인지 체크하세요. "
        f"이 일직선을 유지하면서 쏘는 연습을 반복하면 슛이 일정해져요!"
    )


def _your_form_shot_height(is_above_head, is_in_front=False):
    if is_above_head:
        return "슛 시작 위치가 머리 위에 있어요! 완벽한 위치예요!"
    if is_in_front:
        return (
            "공 높이는 충분하지만, 머리 '앞'에 있어요. "
            "머리 앞에 있으면 수비수가 손을 뻗어서 블로킹할 수 있어요. "
            "공을 머리 '위'(정수리 위)로 올려야 안전해요! "
            "연습 팁: 거울 옆에서 측면을 보면서, 공이 이마 앞이 아니라 "
            "머리 위에 올라가 있는지 확인해보세요."
        )
    return (
        "슛 시작 위치가 머리보다 낮아요. 낮은 위치에서 시작하면 수비에 걸리기 쉬워요. "
        "연습 팁: 공을 머리 위로 올린 상태에서 슛을 시작해보세요. "
        "거울 앞에서 '공이 머리 위에 있는지' 확인하며 반복하면 금방 익숙해져요!"
    )


def _your_form_shot_direction(angle, score):
    if score == 100:
        return f"슛 방향이 {angle}°로 딱 좋아요! 높은 포물선으로 골대에 정확히 들어갈 수 있어요!"
    if angle > 80:
        if score >= 70:
            return (
                f"현재 {angle}°로 공이 너무 위로만 올라가고 있어요. "
                f"약간만 앞쪽으로 보내는 느낌을 더하면 골대까지 정확히 도달해요."
            )
        return (
            f"현재 {angle}°로 공이 거의 수직으로 올라가고 있어요. "
            f"이러면 골대까지 거리가 부족할 수 있어요. "
            f"연습 팁: 골대를 바라보면서 '높은 무지개를 그려서 골대에 떨어뜨린다'는 느낌으로 해보세요."
        )
    if score >= 70:
        return (
            f"현재 {angle}°로 공이 약간 앞쪽으로 나가고 있어요. "
            f"팔을 조금 더 위로 뻗으면 포물선이 높아져서 골대에 부드럽게 들어가요."
        )
    return (
        f"현재 {angle}°로 공이 앞으로 '던져지고' 있어요. 포물선이 낮으면 블로킹에 걸려요. "
        f"연습 팁: 벽 바로 앞에 서서 공이 벽에 안 닿게 위로만 쏘는 연습을 해보세요. "
        f"'위로, 위로!' 라고 말하면서 하면 감각이 잡혀요."
    )


def _your_form_alignment(angle, score):
    if score == 100:
        return f"팔 정렬이 {angle}°로 반듯한 일직선이에요! 공이 똑바로 날아가요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 팔꿈치가 살짝 바깥으로 벌어져 있어요. "
            f"이러면 공이 옆으로 살짝 빠질 수 있어요. "
            f"어깨-팔꿈치-손목이 일직선이 되도록 의식해보세요."
        )
    return (
        f"현재 {angle}°로 팔꿈치가 많이 벌어져 있어요. "
        f"팔꿈치가 벌어지면 공에 옆 힘이 가해져서 좌우로 흔들리는 슛이 돼요. "
        f"연습 팁: 거울 앞에서 정면을 보면서 팔꿈치가 어깨 바로 위에 있는지 확인하세요. "
        f"벽에 등을 대고 팔꿈치가 벽에 닿는 느낌으로 연습하면 좋아요!"
    )


def _your_form_shoulder_level(angle, score):
    if score == 100:
        return f"어깨가 {angle}°로 수평을 잘 유지하고 있어요! 안정적이에요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 어깨가 살짝 기울어져 있어요. "
            f"한쪽 어깨가 올라가면 공도 그쪽으로 빠져요. "
            f"양쪽 어깨 높이를 같게 맞추는 걸 의식해보세요."
        )
    return (
        f"현재 {angle}°로 어깨가 많이 기울어져 있어요. 이러면 슛이 한쪽으로 계속 빠져요. "
        f"연습 팁: 슛 전에 어깨를 한 번 '으쓱' 했다가 내려놓으세요. "
        f"그 자세가 자연스러운 수평이에요. 이걸 습관으로 만들어보세요!"
    )


def _your_form_finger(angle, score):
    if score == 100:
        return f"손끝 방향이 {angle}°로 골대를 정확히 가리키고 있어요! 공이 반듯하게 날아가요!"
    if score >= 70:
        return (
            f"현재 {angle}°로 손끝이 살짝 틀어져 있어요. "
            f"공을 놓을 때 집게손가락이 골대 정중앙을 가리키도록 의식해보세요. "
            f"손끝 방향 = 공이 가는 방향이에요."
        )
    return (
        f"현재 {angle}°로 손끝이 많이 틀어져 있어요. 이러면 공이 옆으로 빠져요. "
        f"연습 팁: 슛을 쏜 뒤 손가락이 골대 한가운데를 가리킨 채로 2초간 멈춰보세요. "
        f"이 '팔로우 스루' 자세를 매번 반복하면 손끝 방향이 자연스럽게 잡혀요!"
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
