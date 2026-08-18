import random
import re
import requests
import streamlit as st

# Cấu hình giao diện tối (Dark Mode)
st.set_page_config(
    page_title="Tra cứu điểm SV",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
]

# CSS Dark Mode dịu mắt
DARK_THEME_CSS = """
<style>
    .stApp {
        background-color: #0f172a !important;
        color: #e2e8f0 !important;
    }
    .result-container {
        margin-top: 20px;
        padding: 20px;
        background-color: #1e293b;
        border-radius: 10px;
        border: 1px solid #334155;
        color: #f8fafc;
        overflow-x: auto;
    }
    table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin-top: 8px;
        font-size: 14px;
        color: #f1f5f9 !important;
    }
    th, td {
        border: 1px solid #334155 !important;
        padding: 10px 12px !important;
        text-align: left;
    }
    th {
        background-color: #334155 !important;
        color: #38bdf8 !important;
        font-weight: 600;
    }
    tr:nth-child(even) { background-color: #1e293b; }
    tr:nth-child(odd) { background-color: #0f172a; }
    tr:hover { background-color: #475569 !important; }
</style>
"""
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def fetch_student_data(masv: str, password: str):
    session = requests.Session()
    chosen_ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": chosen_ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://htql.dhsphue.edu.vn",
        "Referer": "https://htql.dhsphue.edu.vn/htql/login.php",
    }
    session.headers.update(headers)

    login_url = "https://htql.dhsphue.edu.vn/htql/login.php"
    api_url = "https://htql.dhsphue.edu.vn/htql/MESSENGER/api2json.php"

    # 1. Khởi tạo phiên
    session.get(login_url, timeout=300)

    # 2. Đăng nhập
    form_data = {"username": masv, "password": password, "login": ""}
    login_resp = session.post(
        login_url, data=form_data, timeout=686, allow_redirects=True
    )
    login_resp.raise_for_status()

    # 3. Lấy dữ liệu điểm
    api_headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://htql.dhsphue.edu.vn/htql/home.php",
    }
    payload = {
        "message": "xem kết quả học tập",
        "previousMessage": "",
        "messageHistory": {"action": "", "masv": masv},
    }

    api_resp = session.post(
        api_url, json=payload, headers=api_headers, timeout=686
    )
    api_resp.raise_for_status()

    return api_resp.json()


# ================= GIAO DIỆN =================
st.title("🎓 Tra cứu KQHT HUEdu")
st.caption("Dùng khi web chính lag!!")

with st.form("form_tra_cuu"):
    masv = st.text_input(
        "Mã sinh viên:", placeholder="Nhập mã sinh viên"
    ).strip()
    password = st.text_input(
        "Mật khẩu:", type="password", placeholder="Nhập mật khẩu"
    )
    submit_btn = st.form_submit_button(
        "Đăng nhập & Tra cứu", use_container_width=True
    )

if submit_btn:
    if not masv or not password:
        st.warning("⚠️ Vui lòng nhập đầy đủ Mã sinh viên và Mật khẩu.")
    else:
        with st.spinner("⏳ Đang kết nối máy chủ và lấy dữ liệu..."):
            try:
                data = fetch_student_data(masv, password)

                html_content = ""
                if isinstance(data, dict):
                    html_content = data.get("response", {}).get("text", "")

                if "Bạn cần đăng nhập" in html_content:
                    st.error(
                        "❌ Đăng nhập không thành công! Vui lòng kiểm tra lại Mã SV và Mật khẩu."
                    )
                elif html_content:
                    # Cắt bỏ phần "Ai ✒ : Điểm sinh viên ..." trước thẻ <table>
                    clean_html = re.sub(
                        r"^.*?<strong>Điểm sinh viên.*?:\s*</strong>\s*",
                        "",
                        html_content,
                        flags=re.IGNORECASE | re.DOTALL,
                    ).strip()

                    # Trường hợp dự phòng nếu cấu trúc chuỗi có thay đổi nhỏ
                    if clean_html.startswith("<strong>Ai</strong>"):
                        clean_html = re.sub(
                            r"^.*?<table", "<table", clean_html, flags=re.DOTALL
                        )

                    st.success("✅ Lấy kết quả thành công!")
                    st.markdown(
                        f'<div class="result-container">{clean_html}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(
                        "❌ Không nhận được dữ liệu phản hồi từ máy chủ trường."
                    )

            except requests.exceptions.Timeout:
                st.error("⏱️ Quá thời gian chờ (Timeout). Vui lòng thử lại!")
            except requests.exceptions.ConnectionError:
                st.error(
                    "🌐 Lỗi kết nối đến máy chủ. Vui lòng bấm thử lại!"
                )
            except Exception as e:
                st.error(f"❌ Lỗi: {e}. Vui lòng thử lại!")
