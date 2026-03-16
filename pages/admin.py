"""
관리자 페이지 — /admin 경로로 접근
로그인 필수, 관리자/최고관리자만 접근 가능
"""
import streamlit as st
import os
import gc

st.set_page_config(
    page_title="Admin - Shot Form Analyzer",
    page_icon="⚙️",
    layout="centered",
)

# ---------------------------------------------------------------------------
# 설정 로드 (app.py와 동일한 로직)
# ---------------------------------------------------------------------------
def _get_config(section, key, default=None):
    try:
        return st.secrets.get(section, {}).get(key, default)
    except Exception:
        pass
    env_map = {
        ("supabase", "url"): "SUPABASE_URL",
        ("supabase", "key"): "SUPABASE_KEY",
        ("supabase", "admin_emails"): "ADMIN_EMAILS",
    }
    env_key = env_map.get((section, key))
    if env_key:
        val = os.environ.get(env_key, default)
        if key == "admin_emails" and isinstance(val, str):
            return [e.strip() for e in val.split(",")]
        return val
    return default

SUPABASE_URL = _get_config("supabase", "url", "")
SUPABASE_KEY = _get_config("supabase", "key", "")
ADMIN_EMAILS = _get_config("supabase", "admin_emails", [])
if isinstance(ADMIN_EMAILS, str):
    ADMIN_EMAILS = [e.strip() for e in ADMIN_EMAILS.split(",")]

def _init_supabase():
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    from supabase import create_client
    return create_client(SUPABASE_URL, SUPABASE_KEY)

# ---------------------------------------------------------------------------
# CSS
# ---------------------------------------------------------------------------
st.markdown("""
<style>
@import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard@v1.3.9/dist/web/variable/pretendardvariable-dynamic-subset.min.css');
html, body, [class*="css"] {
    font-family: 'Pretendard Variable', Pretendard, -apple-system, sans-serif !important;
}
footer {display: none !important;}
#MainMenu {display: none !important;}
header {display: none !important;}
div[data-testid="stToolbar"] {display: none !important;}
div[data-testid="stSidebarNav"] {display: none !important;}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# 로그인 체크
# ---------------------------------------------------------------------------
if "admin_logged_in" not in st.session_state:
    st.session_state["admin_logged_in"] = False

if not st.session_state["admin_logged_in"]:
    st.markdown("""
    <div style="text-align:center; margin: 40px 0 20px 0;">
        <div style="font-size:1.4rem; font-weight:800;
             background: linear-gradient(135deg, #00D4AA, #00A3FF);
             -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
             관리자 로그인</div>
    </div>
    """, unsafe_allow_html=True)

    email = st.text_input("이메일", key="admin_email")
    password = st.text_input("비밀번호", type="password", key="admin_pw")
    if st.button("로그인", use_container_width=True):
        supabase = _init_supabase()
        if supabase:
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                if res and res.user:
                    # 관리자 여부 확인
                    is_admin = email in ADMIN_EMAILS
                    if not is_admin:
                        try:
                            ar = supabase.table("approved_users").select("role").eq("email", email).execute()
                            if ar.data and ar.data[0].get("role") in ("admin", "superadmin"):
                                is_admin = True
                        except Exception:
                            pass
                    if is_admin:
                        st.session_state["admin_logged_in"] = True
                        st.session_state["admin_email"] = email
                        role_res = supabase.table("approved_users").select("role").eq("email", email).execute()
                        if role_res.data:
                            st.session_state["admin_role"] = role_res.data[0].get("role", "admin")
                        elif email in ADMIN_EMAILS:
                            st.session_state["admin_role"] = "superadmin"
                        st.rerun()
                    else:
                        st.error("관리자 권한이 없습니다.")
                else:
                    st.error("이메일 또는 비밀번호를 확인하세요.")
            except Exception as e:
                st.error("로그인 실패: 이메일 또는 비밀번호를 확인하세요.")
    st.stop()

# ---------------------------------------------------------------------------
# 관리자 페이지 본문
# ---------------------------------------------------------------------------
email = st.session_state.get("admin_email", "")
role = st.session_state.get("admin_role", "admin")
supabase = _init_supabase()

st.markdown(f"""
<div style="text-align:center; margin-bottom:24px;">
    <div style="font-size:1.4rem; font-weight:800;
         background: linear-gradient(135deg, #00D4AA, #00A3FF);
         -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
         ⚙️ 관리자 모드</div>
    <div style="color:#8888A0; font-size:0.85rem; margin-top:4px;">
        {email} ({"최고관리자" if role == "superadmin" else "관리자"})</div>
</div>
""", unsafe_allow_html=True)

# 로그아웃
if st.button("로그아웃", key="admin_logout"):
    st.session_state["admin_logged_in"] = False
    st.rerun()

st.markdown("---")

# 수업 모드 토글
def _is_class_mode():
    try:
        res = supabase.table("app_settings").select("value").eq("key", "class_mode").execute()
        if res.data:
            return res.data[0]["value"] == "on"
    except Exception:
        pass
    return False

def _toggle_class_mode(on):
    try:
        supabase.table("app_settings").upsert({"key": "class_mode", "value": "on" if on else "off"}).execute()
    except Exception:
        st.error("설정 변경 실패")

class_mode_on = _is_class_mode()
if class_mode_on:
    st.success("🟢 수업 모드 ON — 학생들이 로그인 없이 사용 가능합니다")
    if st.button("수업 모드 끄기", key="class_mode_off"):
        _toggle_class_mode(False)
        st.rerun()
else:
    st.info("⚪ 수업 모드 OFF — 로그인 필요")
    if st.button("수업 모드 켜기", key="class_mode_on"):
        _toggle_class_mode(True)
        st.rerun()

st.markdown("---")

# 데이터 로드
try:
    approved_res = supabase.table("approved_users").select("email, role, created_at").execute()
    approved_list = approved_res.data or []
    approved_map = {r["email"]: r["role"] for r in approved_list}
except Exception:
    approved_list = []
    approved_map = {}

try:
    pending_res = supabase.table("pending_users").select("email, created_at").execute()
    pending_users = [r for r in (pending_res.data or []) if r["email"] not in approved_map]
except Exception:
    pending_users = []

# 3개 탭
tab_pending, tab_approved, tab_admin = st.tabs(["🕐 승인 대기", "✅ 승인된 사용자", "👑 관리자"])

with tab_pending:
    if pending_users:
        for pu in pending_users:
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.markdown(f"**{pu['email']}**")
            if col2.button("승인", key=f"approve_{pu['email']}", type="primary"):
                try:
                    supabase.table("approved_users").insert({"email": pu["email"], "role": "user"}).execute()
                    supabase.table("pending_users").delete().eq("email", pu["email"]).execute()
                    st.rerun()
                except Exception:
                    st.error("승인 실패")
            if col3.button("삭제", key=f"del_p_{pu['email']}"):
                try:
                    supabase.table("pending_users").delete().eq("email", pu["email"]).execute()
                    st.rerun()
                except Exception:
                    st.error("삭제 실패")
    else:
        st.info("대기 중인 사용자가 없습니다.")

with tab_approved:
    users = [r for r in approved_list if r.get("role") == "user"]
    if users:
        for u in users:
            col1, col2, col3 = st.columns([4, 1, 1])
            col1.markdown(f"**{u['email']}**")
            if role == "superadmin":
                if col2.button("관리자", key=f"promote_{u['email']}"):
                    try:
                        supabase.table("approved_users").update({"role": "admin"}).eq("email", u["email"]).execute()
                        st.rerun()
                    except Exception:
                        st.error("변경 실패")
            if col3.button("삭제", key=f"del_u_{u['email']}"):
                try:
                    supabase.table("approved_users").delete().eq("email", u["email"]).execute()
                    st.rerun()
                except Exception:
                    st.error("삭제 실패")
    else:
        st.info("승인된 일반 사용자가 없습니다.")

with tab_admin:
    if role == "superadmin":
        admins = [r for r in approved_list if r.get("role") == "admin"]
        if admins:
            for a in admins:
                col1, col2 = st.columns([4, 1])
                col1.markdown(f"**{a['email']}**")
                if col2.button("해제", key=f"demote_{a['email']}"):
                    try:
                        supabase.table("approved_users").update({"role": "user"}).eq("email", a["email"]).execute()
                        st.rerun()
                    except Exception:
                        st.error("변경 실패")
        else:
            st.info("지정된 관리자가 없습니다.")
        st.markdown("---")
        st.caption(f"최고관리자: {email}")
    else:
        st.warning("최고관리자만 관리자를 관리할 수 있습니다.")
