"""
app.py — Shot Form Analyzer (Streamlit)
"""

import streamlit as st
from analyzer import (
    analyze_side_video, analyze_front_video,
    draw_skeleton, draw_front_skeleton,
    draw_angle_comparison, draw_lean_comparison,
    draw_front_comparison, draw_shot_height_comparison, draw_shot_direction_comparison,
)
from feedback import generate_feedback, CRITERIA

# ---------------------------------------------------------------------------
# 페이지 설정
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="Shot Form Analyzer",
    page_icon="🏀",
    layout="wide",
)

# ---------------------------------------------------------------------------
# 커스텀 CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap');

/* 전역 폰트 */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Streamlit 하단 바, 메뉴, GitHub 아이콘 숨기기 */
footer {visibility: hidden;}
#MainMenu {visibility: hidden;}
header {visibility: hidden;}
div[data-testid="stStatusWidget"] {visibility: hidden;}
.viewerBadge_container__r5tak {display: none !important;}
.stDeployButton {display: none !important;}

/* 헤더 영역 */
.hero-title {
    font-size: 2.8rem;
    font-weight: 800;
    letter-spacing: -1px;
    background: linear-gradient(135deg, #00D4AA 0%, #00A3FF 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0;
    line-height: 1.1;
}
.hero-subtitle {
    font-size: 1.05rem;
    color: #8888A0;
    font-weight: 400;
    margin-top: 4px;
    margin-bottom: 24px;
}

/* 종목 탭 스타일 */
div[data-testid="stRadio"] > div {
    gap: 0;
    background: #16161F;
    border-radius: 12px;
    padding: 4px;
    display: inline-flex;
}
div[data-testid="stRadio"] label {
    padding: 10px 32px !important;
    border-radius: 10px !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    transition: all 0.2s;
}
div[data-testid="stRadio"] label[data-checked="true"],
div[data-testid="stRadio"] label:has(input:checked) {
    background: linear-gradient(135deg, #00D4AA, #00A3FF) !important;
    color: #000 !important;
}

/* 스코어 그리드: PC 한줄, 모바일 4열(4+4 or 4+3) */
.score-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
    gap: 10px;
    margin-bottom: 12px;
}
@media (max-width: 768px) {
    .score-grid {
        grid-template-columns: repeat(4, 1fr);
    }
}

/* 스코어 카드 */
.score-card {
    background: linear-gradient(145deg, #16161F, #1C1C28);
    border: 1px solid #2A2A3A;
    border-radius: 12px;
    padding: 14px 6px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.score-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 212, 170, 0.1);
}
.score-label {
    font-size: 0.6rem;
    color: #8888A0;
    text-transform: uppercase;
    letter-spacing: 0.8px;
    font-weight: 600;
    margin-bottom: 4px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.score-value {
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1;
    margin-bottom: 4px;
}
.score-perfect { color: #00D4AA; }
.score-good { color: #00A3FF; }
.score-warning { color: #FFB800; }
.score-danger { color: #FF4757; }

/* 프로그레스 바 */
.progress-bar {
    width: 100%;
    height: 4px;
    background: #2A2A3A;
    border-radius: 2px;
    margin-top: 12px;
    overflow: hidden;
}
.progress-fill {
    height: 100%;
    border-radius: 2px;
    transition: width 0.6s ease;
}

/* 피드백 카드 */
.feedback-card {
    background: #16161F;
    border-left: 3px solid;
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin-bottom: 12px;
    font-size: 0.95rem;
    line-height: 1.6;
    color: #D0D0E0;
}
.feedback-perfect { border-color: #00D4AA; }
.feedback-good { border-color: #00A3FF; }
.feedback-warning { border-color: #FFB800; }
.feedback-danger { border-color: #FF4757; }
.feedback-title {
    font-weight: 700;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 6px;
}

/* 분석 프레임 컨테이너 */
.frame-container {
    background: #16161F;
    border: 1px solid #2A2A3A;
    border-radius: 16px;
    padding: 12px;
    text-align: center;
}
.frame-label {
    font-size: 0.75rem;
    color: #8888A0;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin-bottom: 8px;
}

/* 총점 원형 */
.overall-score {
    text-align: center;
    padding: 32px 0;
}
.overall-circle {
    width: 140px;
    height: 140px;
    border-radius: 50%;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    flex-direction: column;
    margin-bottom: 12px;
}
.overall-number {
    font-size: 3rem;
    font-weight: 900;
    line-height: 1;
}
.overall-label {
    font-size: 0.7rem;
    text-transform: uppercase;
    letter-spacing: 2px;
    margin-top: 4px;
    color: #8888A0;
}
.overall-grade {
    font-size: 1.1rem;
    font-weight: 700;
    margin-top: 8px;
}

/* 업로드 영역 */
div[data-testid="stFileUploader"] {
    border: 2px dashed #2A2A3A !important;
    border-radius: 16px !important;
    padding: 12px !important;
    transition: border-color 0.2s;
}
div[data-testid="stFileUploader"]:hover {
    border-color: #00D4AA !important;
}

/* 분석 버튼 */
div[data-testid="stButton"] > button {
    background: linear-gradient(135deg, #00D4AA, #00A3FF) !important;
    color: #000 !important;
    font-weight: 700 !important;
    font-size: 1rem !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 14px 0 !important;
    letter-spacing: 0.5px;
    transition: opacity 0.2s, transform 0.2s !important;
}
div[data-testid="stButton"] > button:hover {
    opacity: 0.9;
    transform: translateY(-1px);
}
div[data-testid="stButton"] > button:disabled {
    background: #2A2A3A !important;
    color: #555 !important;
}

/* 섹션 구분선 */
.section-divider {
    height: 1px;
    background: linear-gradient(90deg, transparent, #2A2A3A, transparent);
    margin: 32px 0;
}

/* 개인정보 안내 */
.privacy-note {
    text-align: center;
    color: #555;
    font-size: 0.75rem;
    padding: 24px 0 8px 0;
    letter-spacing: 0.3px;
}

/* 가이드 안내 박스 */
.guide-box {
    background: #12121A;
    border: 1px solid #2A2A3A;
    border-radius: 12px;
    padding: 16px 20px;
    font-size: 0.9rem;
    color: #8888A0;
    line-height: 1.6;
}

/* metric 위젯 숨기기 (커스텀 카드 사용) */
div[data-testid="stMetric"] { display: none; }

/* 기본 info 박스 숨기기 (커스텀 사용) — error는 표시 */
div[data-testid="stAlert"][data-baseweb*="info"] { display: none; }

/* 모바일 반응형 */
@media (max-width: 768px) {
    .hero-title { font-size: 1.8rem; }
    .hero-subtitle { font-size: 0.85rem; }
    .score-value { font-size: 1.4rem; }
    .score-label { font-size: 0.55rem; letter-spacing: 0.5px; }
    .score-card { padding: 10px 4px; border-radius: 10px; }
    .overall-circle { width: 110px; height: 110px; }
    .overall-number { font-size: 2.2rem; }
    .feedback-card { padding: 12px 14px; font-size: 0.88rem; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 유틸 함수
# ---------------------------------------------------------------------------
def get_score_class(score):
    if score >= 90: return "perfect"
    if score >= 70: return "good"
    if score >= 50: return "warning"
    return "danger"

def _score_card_html(label, score):
    cls = get_score_class(score)
    color_map = {"perfect": "#00D4AA", "good": "#00A3FF", "warning": "#FFB800", "danger": "#FF4757"}
    color = color_map[cls]
    return f"""
    <div class="score-card">
        <div class="score-label">{label}</div>
        <div class="score-value score-{cls}">{score}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width:{score}%; background:{color};"></div>
        </div>
    </div>"""

def render_score_grid(items):
    """items: list of (label, score) tuples"""
    cards = "".join(_score_card_html(label, score) for label, score in items)
    st.markdown(f'<div class="score-grid">{cards}</div>', unsafe_allow_html=True)

def render_feedback(title, score, best_text, yourform_text, comparison_img=None):
    cls = get_score_class(score)
    with st.expander(f"{title} — {score}점  (클릭하여 자세 비교 보기)", expanded=False):
        if comparison_img is not None:
            st.image(comparison_img, use_container_width=True)
        st.markdown(f"""
        <div style="border-left:3px solid #00D4AA; padding:10px 14px; margin:8px 0; background:#0D1F17; border-radius:0 8px 8px 0;">
            <div style="color:#00D4AA; font-weight:700; font-size:0.85rem; letter-spacing:1px; margin-bottom:4px;">BEST</div>
            <div style="color:#C0E8D8; font-size:0.9rem; line-height:1.6;">{best_text}</div>
        </div>
        <div style="border-left:3px solid #FF4757; padding:10px 14px; margin:8px 0; background:#1F0D10; border-radius:0 8px 8px 0;">
            <div style="color:#FF4757; font-weight:700; font-size:0.85rem; letter-spacing:1px; margin-bottom:4px;">YOUR FORM</div>
            <div style="color:#E8C0C4; font-size:0.9rem; line-height:1.6;">{yourform_text}</div>
        </div>
        """, unsafe_allow_html=True)

def render_overall(scores):
    avg = round(sum(scores) / len(scores))
    cls = get_score_class(avg)
    color_map = {"perfect": "#00D4AA", "good": "#00A3FF", "warning": "#FFB800", "danger": "#FF4757"}
    color = color_map[cls]
    if avg >= 90: grade = "Excellent"
    elif avg >= 70: grade = "Good"
    elif avg >= 50: grade = "Needs Work"
    else: grade = "Keep Practicing"
    st.markdown(f"""
    <div class="overall-score">
        <div class="overall-circle" style="border: 3px solid {color}; box-shadow: 0 0 30px {color}33;">
            <div class="overall-number" style="color:{color};">{avg}</div>
            <div class="overall-label">Overall</div>
        </div>
        <div class="overall-grade" style="color:{color};">{grade}</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 헤더
# ---------------------------------------------------------------------------
st.markdown('<div class="hero-title">Shot Form Analyzer</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-subtitle">AI 기반 슛 자세 분석 — 프로처럼 쏴보세요</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 종목 선택
# ---------------------------------------------------------------------------
sport = st.radio(
    "종목",
    options=["Basketball", "Netball"],
    horizontal=True,
    label_visibility="collapsed",
)
sport_key = "basketball" if sport == "Basketball" else "netball"

# 가이드 안내
guide_text = (
    "<b>측면</b> 영상, <b>정면</b> 영상을 올려주세요 (둘 다 또는 하나만 가능). "
    "슛하는 팔이 카메라 쪽을 향하게, 전신이 나오게, 2~10초 클립."
)
st.markdown(f'<div class="guide-box">{guide_text}</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 영상 업로드 (농구/넷볼 공통: 측면 + 정면, 하나만 올려도 분석 가능)
# ---------------------------------------------------------------------------
up_col1, up_col2 = st.columns(2)
with up_col1:
    side_video = st.file_uploader("SIDE VIEW", type=["mp4", "mov"], key="side")
with up_col2:
    front_video = st.file_uploader("FRONT VIEW", type=["mp4", "mov"], key="front")

can_analyze = (side_video is not None) or (front_video is not None)

st.markdown("<br>", unsafe_allow_html=True)
analyze_btn = st.button("ANALYZE", disabled=(not can_analyze), use_container_width=True)

# ---------------------------------------------------------------------------
# 분석 실행
# ---------------------------------------------------------------------------
if analyze_btn and can_analyze:
    # --- 측면 분석 ---
    side_result = None
    if side_video is not None:
        with st.spinner("Analyzing side view..."):
            side_bytes = side_video.read()
            side_result = analyze_side_video(side_bytes)
        if side_result["error"]:
            st.markdown(
                f'<div style="background:#2D1117;border:1px solid #FF4757;border-radius:8px;'
                f'padding:12px 16px;color:#FF6B7A;margin:8px 0;">'
                f'⚠️ 측면 영상: {side_result["error"]}</div>',
                unsafe_allow_html=True,
            )
            side_result = None

    # --- 정면 분석 ---
    front_result = None
    if front_video is not None:
        with st.spinner("Analyzing front view..."):
            front_bytes = front_video.read()
            front_result = analyze_front_video(front_bytes)
        if front_result["error"]:
            st.markdown(
                f'<div style="background:#2D1117;border:1px solid #FF4757;border-radius:8px;'
                f'padding:12px 16px;color:#FF6B7A;margin:8px 0;">'
                f'⚠️ 정면 영상: {front_result["error"]}</div>',
                unsafe_allow_html=True,
            )
            front_result = None

    if side_result or front_result:
        # 피드백 생성
        fb_kwargs = {}
        if side_result:
            fb_kwargs["elbow_angle"] = side_result["elbow_angle"]
            fb_kwargs["knee_angle"] = side_result["knee_angle"]
            fb_kwargs["lean_angle"] = side_result["lean_angle"]
            if sport_key == "netball":
                fb_kwargs["shot_height_above_head"] = side_result["shot_height_above_head"]
                fb_kwargs["shot_height_in_front"] = side_result.get("shot_height_in_front", False)
                fb_kwargs["shot_direction_angle"] = side_result["shot_direction_angle"]
        if front_result:
            fb_kwargs["alignment_angle"] = front_result["alignment_angle"]
            fb_kwargs["shoulder_level_angle"] = front_result["shoulder_level_angle"]
            fb_kwargs["finger_direction_angle"] = front_result["finger_direction_angle"]

        fb = generate_feedback(sport_key, **fb_kwargs)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 총점
        # =================================================================
        all_scores = []
        if side_result:
            all_scores += [fb["elbow_score"], fb["knee_score"], fb["lean_score"]]
            if sport_key == "netball":
                all_scores += [fb["shot_height_score"], fb["shot_direction_score"]]
        if front_result:
            all_scores += [fb["alignment_score"], fb["shoulder_level_score"], fb["finger_direction_score"]]

        render_overall(all_scores)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 분석 프레임
        # =================================================================
        frame_cols_count = (2 if side_result else 0) + (1 if front_result else 0)
        frame_cols = st.columns(max(frame_cols_count, 1))
        col_idx = 0

        if side_result:
            with frame_cols[col_idx]:
                st.markdown('<div class="frame-container"><div class="frame-label">Release</div></div>', unsafe_allow_html=True)
                release_img = draw_skeleton(
                    side_result["release_frame"],
                    side_result["release_landmarks"],
                    angles_text=[
                        f"Elbow: {side_result['elbow_angle']}",
                        f"Lean: {side_result['lean_angle']}",
                    ],
                )
                st.image(release_img, use_container_width=True)
            col_idx += 1

            with frame_cols[col_idx]:
                st.markdown('<div class="frame-container"><div class="frame-label">Setup</div></div>', unsafe_allow_html=True)
                setup_img = draw_skeleton(
                    side_result["setup_frame"],
                    side_result["setup_landmarks"],
                    angles_text=[f"Knee: {side_result['knee_angle']}"],
                )
                st.image(setup_img, use_container_width=True)
            col_idx += 1

        if front_result:
            with frame_cols[col_idx]:
                st.markdown('<div class="frame-container"><div class="frame-label">Front</div></div>', unsafe_allow_html=True)
                front_img = draw_front_skeleton(
                    front_result["front_frame"],
                    front_result["front_landmarks"],
                    angles_text=[
                        f"Align: {front_result['alignment_angle']}",
                        f"Shoulder: {front_result['shoulder_level_angle']}",
                    ],
                )
                st.image(front_img, use_container_width=True)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 점수 카드 (CSS 그리드 — 모바일 2열, 데스크톱 3열)
        # =================================================================
        score_items = []
        if side_result:
            score_items += [
                ("ELBOW", fb["elbow_score"]),
                ("KNEE", fb["knee_score"]),
                ("POSTURE", fb["lean_score"]),
            ]
            if sport_key == "netball":
                score_items += [
                    ("SHOT HEIGHT", fb["shot_height_score"]),
                    ("DIRECTION", fb["shot_direction_score"]),
                ]
        if front_result:
            score_items += [
                ("ALIGNMENT", fb["alignment_score"]),
                ("SHOULDERS", fb["shoulder_level_score"]),
                ("FINGER", fb["finger_direction_score"]),
            ]
        render_score_grid(score_items)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 피드백 + 각도 비교 이미지
        # =================================================================
        c = CRITERIA[sport_key]

        if side_result:
            rl = side_result["release_landmarks"]
            sl = side_result["setup_landmarks"]

            # 팔꿈치 비교 이미지
            elbow_img = draw_angle_comparison(
                side_result["release_frame"],
                rl["shoulder"], rl["elbow"], rl["wrist"],
                side_result["elbow_angle"],
                c["elbow"]["ideal_min"], c["elbow"]["ideal_max"],
                label="ELBOW",
            )
            render_feedback("ELBOW", fb["elbow_score"], fb["elbow_best"], fb["elbow_yourform"], elbow_img)

            knee_img = draw_angle_comparison(
                side_result["setup_frame"], sl["hip"], sl["knee"], sl["ankle"],
                side_result["knee_angle"], c["knee"]["ideal_min"], c["knee"]["ideal_max"], label="KNEE")
            render_feedback("KNEE", fb["knee_score"], fb["knee_best"], fb["knee_yourform"], knee_img)

            lean_img = draw_lean_comparison(
                side_result["release_frame"], rl["shoulder"], rl["hip"],
                side_result["lean_angle"], c["lean"]["ideal_max"], label="POSTURE")
            render_feedback("POSTURE", fb["lean_score"], fb["lean_best"], fb["lean_yourform"], lean_img)

            if sport_key == "netball":
                height_img = draw_shot_height_comparison(
                    side_result["setup_frame"], sl, side_result["shot_height_above_head"])
                render_feedback("SHOT HEIGHT", fb["shot_height_score"], fb["shot_height_best"], fb["shot_height_yourform"], height_img)

                direction_img = draw_shot_direction_comparison(
                    side_result["release_frame"], rl, side_result["shot_direction_angle"])
                render_feedback("DIRECTION", fb["shot_direction_score"], fb["shot_direction_best"], fb["shot_direction_yourform"], direction_img)

        if front_result:
            fl = front_result["front_landmarks"]

            align_img = draw_front_comparison(
                front_result["front_frame"], fl, "alignment",
                front_result["alignment_angle"], c["alignment"]["ideal_max"], "ALIGNMENT")
            render_feedback("ALIGNMENT", fb["alignment_score"], fb["alignment_best"], fb["alignment_yourform"], align_img)

            shoulder_img = draw_front_comparison(
                front_result["front_frame"], fl, "shoulder_level",
                front_result["shoulder_level_angle"], c["shoulder_level"]["ideal_max"], "SHOULDERS")
            render_feedback("SHOULDERS", fb["shoulder_level_score"], fb["shoulder_level_best"], fb["shoulder_level_yourform"], shoulder_img)

            finger_img = draw_front_comparison(
                front_result["front_frame"], fl, "finger_direction",
                front_result["finger_direction_angle"], c["finger_direction"]["ideal_max"], "FINGER")
            render_feedback("FINGER", fb["finger_direction_score"], fb["finger_direction_best"], fb["finger_direction_yourform"], finger_img)

# ---------------------------------------------------------------------------
# 하단
# ---------------------------------------------------------------------------
st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
st.markdown(
    '<div class="privacy-note">'
    'PRIVACY — 업로드된 영상은 분석 후 즉시 삭제됩니다 · 외부 전송 없음 · 결과 저장 없음'
    '</div>',
    unsafe_allow_html=True,
)
