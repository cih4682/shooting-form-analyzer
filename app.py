"""
app.py — Shot Form Analyzer (Streamlit)
"""

import streamlit as st
from analyzer import analyze_side_video, analyze_front_video, draw_skeleton, draw_front_skeleton
from feedback import generate_feedback

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

/* 스코어 카드 */
.score-card {
    background: linear-gradient(145deg, #16161F, #1C1C28);
    border: 1px solid #2A2A3A;
    border-radius: 16px;
    padding: 24px 20px;
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.score-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0, 212, 170, 0.1);
}
.score-label {
    font-size: 0.8rem;
    color: #8888A0;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    font-weight: 600;
    margin-bottom: 8px;
}
.score-value {
    font-size: 2.8rem;
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

/* 기본 info 박스 숨기기 (커스텀 사용) */
div[data-testid="stAlert"] { display: none; }
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

def render_score_card(label, score):
    cls = get_score_class(score)
    color_map = {"perfect": "#00D4AA", "good": "#00A3FF", "warning": "#FFB800", "danger": "#FF4757"}
    color = color_map[cls]
    st.markdown(f"""
    <div class="score-card">
        <div class="score-label">{label}</div>
        <div class="score-value score-{cls}">{score}</div>
        <div class="progress-bar">
            <div class="progress-fill" style="width:{score}%; background:{color};"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def render_feedback(title, text, score):
    cls = get_score_class(score)
    color_map = {"perfect": "#00D4AA", "good": "#00A3FF", "warning": "#FFB800", "danger": "#FF4757"}
    st.markdown(f"""
    <div class="feedback-card feedback-{cls}">
        <div class="feedback-title" style="color:{color_map[cls]};">{title}</div>
        {text}
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
if sport_key == "basketball":
    guide_text = "슛하는 팔이 카메라 쪽을 향하도록 <b>측면</b>에서 촬영해주세요. 전신이 나오게, 2~10초 클립."
else:
    guide_text = "<b>측면</b> + <b>정면</b> 영상 2개를 올려주세요. 슛하는 팔이 카메라 쪽을 향하게, 전신이 나오게 촬영."
st.markdown(f'<div class="guide-box">{guide_text}</div>', unsafe_allow_html=True)
st.markdown("<br>", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 영상 업로드
# ---------------------------------------------------------------------------
if sport_key == "netball":
    up_col1, up_col2 = st.columns(2)
    with up_col1:
        side_video = st.file_uploader("SIDE VIEW", type=["mp4", "mov"], key="side")
    with up_col2:
        front_video = st.file_uploader("FRONT VIEW", type=["mp4", "mov"], key="front")
else:
    side_video = st.file_uploader("SIDE VIEW", type=["mp4", "mov"], key="side")
    front_video = None

can_analyze = side_video is not None
if sport_key == "netball":
    can_analyze = can_analyze and front_video is not None

st.markdown("<br>", unsafe_allow_html=True)
analyze_btn = st.button("ANALYZE", disabled=(not can_analyze), use_container_width=True)

# ---------------------------------------------------------------------------
# 분석 실행
# ---------------------------------------------------------------------------
if analyze_btn and can_analyze:
    with st.spinner("Analyzing..."):
        side_bytes = side_video.read()
        side_result = analyze_side_video(side_bytes)

    if side_result["error"]:
        st.error(side_result["error"])
    else:
        front_result = None
        if sport_key == "netball" and front_video is not None:
            with st.spinner("Analyzing front view..."):
                front_bytes = front_video.read()
                front_result = analyze_front_video(front_bytes)
            if front_result["error"]:
                st.error(front_result["error"])
                front_result = None

        # 피드백 생성
        fb_kwargs = {
            "elbow_angle": side_result["elbow_angle"],
            "knee_angle": side_result["knee_angle"],
            "lean_angle": side_result["lean_angle"],
        }
        if sport_key == "netball":
            fb_kwargs["shot_height_above_head"] = side_result["shot_height_above_head"]
            fb_kwargs["shot_direction_angle"] = side_result["shot_direction_angle"]
            if front_result:
                fb_kwargs["alignment_angle"] = front_result["alignment_angle"]
                fb_kwargs["shoulder_level_angle"] = front_result["shoulder_level_angle"]

        fb = generate_feedback(sport_key, **fb_kwargs)

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 총점
        # =================================================================
        all_scores = [fb["elbow_score"], fb["knee_score"], fb["lean_score"]]
        if sport_key == "netball":
            all_scores += [fb["shot_height_score"], fb["shot_direction_score"]]
            if front_result:
                all_scores += [fb["alignment_score"], fb["shoulder_level_score"]]

        render_overall(all_scores)
        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 분석 프레임
        # =================================================================
        if sport_key == "netball" and front_result and front_result.get("front_frame") is not None:
            f_col1, f_col2, f_col3 = st.columns(3)
        else:
            f_col1, f_col2 = st.columns(2)
            f_col3 = None

        with f_col1:
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

        with f_col2:
            st.markdown('<div class="frame-container"><div class="frame-label">Setup</div></div>', unsafe_allow_html=True)
            setup_img = draw_skeleton(
                side_result["setup_frame"],
                side_result["setup_landmarks"],
                angles_text=[f"Knee: {side_result['knee_angle']}"],
            )
            st.image(setup_img, use_container_width=True)

        if f_col3 and front_result:
            with f_col3:
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
        # 점수 카드
        # =================================================================
        cols = st.columns(3)
        with cols[0]: render_score_card("ELBOW", fb["elbow_score"])
        with cols[1]: render_score_card("KNEE", fb["knee_score"])
        with cols[2]: render_score_card("POSTURE", fb["lean_score"])

        if sport_key == "netball":
            st.markdown("<br>", unsafe_allow_html=True)
            n_extra = 2
            if front_result:
                n_extra = 4
            extra_cols = st.columns(n_extra)
            with extra_cols[0]: render_score_card("SHOT HEIGHT", fb["shot_height_score"])
            with extra_cols[1]: render_score_card("DIRECTION", fb["shot_direction_score"])
            if front_result:
                with extra_cols[2]: render_score_card("ALIGNMENT", fb["alignment_score"])
                with extra_cols[3]: render_score_card("SHOULDERS", fb["shoulder_level_score"])

        st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)

        # =================================================================
        # 피드백
        # =================================================================
        render_feedback("ELBOW", fb["elbow_feedback"], fb["elbow_score"])
        render_feedback("KNEE", fb["knee_feedback"], fb["knee_score"])
        render_feedback("POSTURE", fb["lean_feedback"], fb["lean_score"])

        if sport_key == "netball":
            render_feedback("SHOT HEIGHT", fb["shot_height_feedback"], fb["shot_height_score"])
            render_feedback("DIRECTION", fb["shot_direction_feedback"], fb["shot_direction_score"])
            if front_result:
                render_feedback("ALIGNMENT", fb["alignment_feedback"], fb["alignment_score"])
                render_feedback("SHOULDERS", fb["shoulder_level_feedback"], fb["shoulder_level_score"])

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
