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
    /* Nền ứng dụng & font chữ */
    .stApp {
        background-color: #0f172a !important;
        color: #e2e8f0 !important;
    }
    
    /* Khung kết quả tra cứu */
    .result-container {
        margin-top: 20px;
        padding: 20px;
        background-color: #1e293b;
        border-radius: 10px;
        border: 1px solid #334155;
        color: #f8fafc;
        overflow-x: auto;
    }
    
    /* Bảng điểm trên nền tối */
    table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin-top: 12px;
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
    tr:nth-child(even) {
        background-color: #1e293b;
    }
    tr:nth-child(odd) {
        background-color: #0f172a;
    }
    tr:hover {
        background-color: #475569 !important;
    }
    
    /* Link trong text trả về */
    a {
        color: #38bdf8 !important;
        text-decoration: underline;
    }
</style>
"""
st.markdown(DARK_THEME_CSS, unsafe_allow_html=True)


def fetch_student_data(masv: str, password: str):
    session = requests.Session()
    
    # Dùng cố định 1 User-Agent duy nhất cho toàn bộ phiên này
    chosen_ua = random.choice(USER_AGENTS)
    headers = {
        "User-Agent": chosen_ua,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
        "Accept-Language": "vi-VN,vi;q=0.9,en-US;q=0.8,en;q=0.7",
        "Origin": "https://htql.dhsphue.edu.vn",
        "Referer": "https://htql.dhsphue.edu.vn/htql/login.php",
    }
    session.headers.update(headers)

    login_url = "https://htql.dhsphue.edu.vn/htql/login.php"
    api_url = "https://htql.dhsphue.edu.vn/htql/MESSENGER/api2json.php"

    # Bước 1: GET trang login trước để khởi tạo PHPSESSID hợp lệ
    session.get(login_url, timeout=300)

    # Bước 2: POST thông tin đăng nhập
    form_data = {
        "username": masv,
        "password": password,
        "login": ""
    }
    login_resp = session.post(login_url, data=form_data, timeout=300, allow_redirects=True)
    login_resp.raise_for_status()

    # Bước 3: Gửi payload sang API tra cứu điểm
    api_headers = {
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://htql.dhsphue.edu.vn/htql/home.php"
    }
    payload = {
        "message": "xem kết quả học tập",
        "previousMessage": "xem thông tin sinh viên",
        "messageHistory": {
            "action": "",
            "masv": masv
        }
    }
    
    api_resp = session.post(api_url, json=payload, headers=api_headers, timeout=300)
    api_resp.raise_for_status()

    return api_resp.json()


# ================= GIAO DIỆN =================
st.title("🎓 Tra cứu kết quả học tập")
st.caption("Hệ thống ĐH Sư Phạm - Đại học Huế")

with st.form("form_tra_cuu"):
    masv = st.text_input("Mã sinh viên:", placeholder="Nhập mã sinh viên (VD: 25S1060062)").strip()
    password = st.text_input("Mật khẩu:", type="password", placeholder="Nhập mật khẩu")
    submit_btn = st.form_submit_button("Đăng nhập & Tra cứu", use_container_width=True)

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
                    st.error("❌ Đăng nhập không thành công! Vui lòng kiểm tra lại Mã SV và Mật khẩu.")
                elif html_content:
                    st.success("✅ Lấy kết quả thành công!")
                    st.markdown(f'<div class="result-container">{html_content}</div>', unsafe_allow_html=True)
                else:
                    st.error("❌ Không nhận được dữ liệu phản hồi từ máy chủ trường.")

            except requests.exceptions.Timeout:
                st.error("⏱️ Quá thời gian chờ (Timeout). Vui lòng thử lại!")
            except requests.exceptions.ConnectionError:
                st.error("🌐 Lỗi kết nối đến máy chủ. Vui lòng bấm thử lại!")
            except Exception as e:
                st.error(f"❌ Lỗi: {e}. Vui lòng thử lại!")
