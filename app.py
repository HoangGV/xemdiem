import random
import requests
import streamlit as st

# 1. Cấu hình trang web
st.set_page_config(
    page_title="Tra cứu kết quả học tập",
    page_icon="🎓",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# 2. Danh sách User-Agent để fake ngẫu nhiên mỗi lần submit
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:125.0) Gecko/20100101 Firefox/125.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1",
]

# 3. CSS tùy biến nhẹ nhàng, responsive và định dạng bảng điểm HTML
CUSTOM_CSS = """
<style>
    .stApp {
        background-color: #f8fafc;
    }
    .main-card {
        background: #ffffff;
        padding: 24px;
        border-radius: 12px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
        margin-bottom: 20px;
    }
    .result-container {
        margin-top: 15px;
        padding: 16px;
        background: #ffffff;
        border-radius: 8px;
        border: 1px solid #e2e8f0;
        overflow-x: auto;
    }
    table {
        width: 100% !important;
        border-collapse: collapse !important;
        margin-top: 10px;
        font-size: 14px;
    }
    th, td {
        border: 1px solid #cbd5e1 !important;
        padding: 8px 12px !important;
        text-align: left;
    }
    th {
        background-color: #f1f5f9 !important;
        font-weight: 600;
        color: #334155;
    }
    tr:nth-child(even) {
        background-color: #f8fafc;
    }
    tr:hover {
        background-color: #f1f5f9;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def fetch_student_data(masv: str, password: str):
    """Thực hiện đăng nhập duy trì session và gọi API lấy điểm"""
    session = requests.Session()

    # Fake header trình duyệt ngẫu nhiên
    headers = {
        "User-Agent": random.choice(USER_AGENTS),
        "Origin": "https://htql.dhsphue.edu.vn",
        "Referer": "https://htql.dhsphue.edu.vn/htql/login.php",
    }
    session.headers.update(headers)

    # Bước 1: Gửi form đăng nhập lấy Cookie
    login_url = "https://htql.dhsphue.edu.vn/htql/login.php"
    form_data = {"username": masv, "password": password, "login": ""}
    login_resp = session.post(
        login_url, data=form_data, timeout=300, allow_redirects=True
    )
    login_resp.raise_for_status()

    # Bước 2: Gọi API lấy kết quả học tập
    api_url = "https://htql.dhsphue.edu.vn/htql/MESSENGER/api2json.php"
    payload = {
        "message": "xem kết quả học tập",
        "previousMessage": "xem thông tin sinh viên",
        "messageHistory": {"action": "", "masv": masv},
    }
    session.headers.update({"Content-Type": "application/json"})
    api_resp = session.post(api_url, json=payload, timeout=300)
    api_resp.raise_for_status()

    return api_resp.json()


# ================= GIAO DIỆN CHÍNH =================
st.title("🎓 Tra cứu kết quả học tập")
st.caption("Cổng tra cứu kết quả sinh viên ĐH Sư Phạm - Huế")

with st.form("form_tra_cuu"):
    masv = st.text_input("Mã sinh viên:", placeholder="Ví dụ: 25S1060062").strip()
    password = st.text_input(
        "Mật khẩu:", type="password", placeholder="Nhập mật khẩu"
    )
    submit_btn = st.form_submit_button(
        "Đăng nhập & Xem kết quả", use_container_width=True
    )

if submit_btn:
    if not masv or not password:
        st.warning("⚠️ Vui lòng nhập đầy đủ Mã sinh viên và Mật khẩu.")
    else:
        with st.spinner("⏳ Đang kết nối máy chủ và lấy dữ liệu, vui lòng chờ..."):
            try:
                data = fetch_student_data(masv, password)

                # Trích xuất nội dung HTML trong trường "text"
                html_content = ""
                if isinstance(data, dict):
                    html_content = data.get("response", {}).get("text", "")

                if html_content:
                    st.success("✅ Lấy dữ liệu thành công!")
                    st.markdown(
                        f'<div class="result-container">{html_content}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.error(
                        "❌ Không tìm thấy bảng dữ liệu. Vui lòng kiểm tra lại Mã sinh viên hoặc Mật khẩu!"
                    )

            except requests.exceptions.Timeout:
                st.error(
                    "⏱️ Quá thời gian chờ (Timeout sau 5 phút). Máy chủ trường phản hồi chậm, vui lòng thử lại!"
                )
            except requests.exceptions.ConnectionError:
                st.error(
                    "🌐 Không thể kết nối tới máy chủ trường (Lỗi mạng hoặc server trường không phản hồi). Vui lòng bấm thử lại!"
                )
            except requests.exceptions.HTTPError as http_err:
                st.error(f"⚠️ Máy chủ trả về mã lỗi HTTP: {http_err}. Vui lòng thử lại!")
            except requests.exceptions.JSONDecodeError:
                st.error(
                    "⚠️ Dữ liệu trả về không đúng định dạng JSON. Vui lòng thử lại!"
                )
            except Exception as e:
                st.error(f"❌ Đã xảy ra lỗi không xác định: {e}. Vui lòng thử lại!")
