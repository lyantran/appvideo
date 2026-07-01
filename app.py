import streamlit as st
from datetime import time, date, timedelta
import time as t
import os
import re
import json
import random
import hashlib
import base64
import smtplib
from email.mime.text import MIMEText

import requests

# ============ CẤU HÌNH TRANG ============
st.set_page_config(page_title="AI Content Studio", page_icon="🎬", layout="wide")

ADMIN_VERIFICATION_EMAIL = "anluanlh@gmail.com"  # Nơi nhận mã xác nhận khi có người đăng ký thành viên mới
OTP_EXPIRE_MINUTES = 10

# Danh sách các nhà cung cấp AI hỗ trợ. Có thể chỉnh "models" khi các hãng ra model mới.
# "models": danh sách model gợi ý để chọn qua dropdown (mục đầu tiên = mặc định).
AI_PROVIDERS = {
    "Claude (Anthropic)": {
        "key": "claude",
        "models": ["claude-sonnet-5", "claude-opus-4-8", "claude-haiku-4-5-20251001"],
        "help": "API key tại console.anthropic.com/settings/keys",
        "supports_image": True,
    },
    "ChatGPT (OpenAI)": {
        "key": "openai",
        "models": ["gpt-5.5", "gpt-5.4", "gpt-5.4-mini", "gpt-5.4-nano", "gpt-5.3-codex"],
        "help": "API key tại platform.openai.com/api-keys",
        "supports_image": True,
    },
    "Gemini (Google)": {
        "key": "gemini",
        "models": ["gemini-flash-latest", "gemini-3.1-pro-preview", "gemini-3.5-flash", "gemini-3.1-flash-lite"],
        "help": "API key tại aistudio.google.com/apikey",
        "supports_image": True,
    },
    "Grok (xAI)": {
        "key": "grok",
        "models": ["grok-4", "grok-4-fast", "grok-3-mini"],
        "help": "API key tại console.x.ai",
        "supports_image": False,
    },
    "DeepSeek": {
        "key": "deepseek",
        "models": ["deepseek-chat", "deepseek-reasoner"],
        "help": "API key tại platform.deepseek.com",
        "supports_image": False,
    },
    "Mistral AI": {
        "key": "mistral",
        "models": ["mistral-large-latest", "mistral-medium-latest", "mistral-small-latest"],
        "help": "API key tại console.mistral.ai",
        "supports_image": False,
    },
}

CUSTOM_MODEL_LABEL = "✏️ Khác (tự nhập tên model)"

# ============ CSS TÙY CHỈNH - GIAO DIỆN HIỆN ĐẠI ============
st.markdown("""
<style>
    .stButton>button {border-radius: 10px; font-weight: 600; padding: 0.5rem 1rem;}
    div[data-testid="stMetric"] {background:#f8f9fa; padding:10px; border-radius:10px;}
    section[data-testid="stSidebar"] {background-color:#111827;}
    section[data-testid="stSidebar"] * {color:#f5f5f5 !important;}
    h1,h2,h3 {font-weight:700;}
</style>
""", unsafe_allow_html=True)

# ============ KHỞI TẠO DỮ LIỆU MẪU (SESSION STATE) ============
if "posts" not in st.session_state:
    st.session_state.posts = [
        {"title": "Video Review iPhone 16 Pro Max", "status": "Đã xong"},
        {"title": "Bài viết: Du lịch Đà Lạt mùa hoa", "status": "Chờ xử lý"},
        {"title": "Clip Reels: Món ngon Hà Nội", "status": "Đã xong"},
        {"title": "Bài PR sản phẩm mỹ phẩm mới", "status": "Chờ xử lý"},
        {"title": "Video Unbox laptop Gaming 2026", "status": "Đã xong"},
        {"title": "TikTok: Xu hướng thời trang Hè", "status": "Chờ xử lý"},
    ]
if "description" not in st.session_state:
    st.session_state.description = ""
if "translated_text" not in st.session_state:
    st.session_state.translated_text = ""
if "subtitles" not in st.session_state:
    st.session_state.subtitles = [
        {"time": "00:01 - 00:03", "text": "Xin chào các bạn đã quay trở lại kênh!"},
        {"time": "00:03 - 00:06", "text": "Hôm nay chúng ta sẽ khám phá sản phẩm mới."},
        {"time": "00:06 - 00:10", "text": ""},
    ]
if "video_library" not in st.session_state:
    # Dữ liệu mẫu giả lập kho video (thực tế sẽ lấy từ API/CSDL nội bộ)
    st.session_state.video_library = [
        {"title": "Áo thun nam basic form rộng", "shop": "Shop Thời Trang ABC", "date": date(2026, 6, 28), "duration": "0:32", "size": "12MB"},
        {"title": "Đèn LED trang trí phòng ngủ", "shop": "HomeDeco Store", "date": date(2026, 6, 25), "duration": "0:45", "size": "20MB"},
        {"title": "Son môi lì màu cam đất", "shop": "Beauty House", "date": date(2026, 6, 20), "duration": "0:28", "size": "9MB"},
        {"title": "Giày sneaker unisex trắng", "shop": "Shop Thời Trang ABC", "date": date(2026, 6, 15), "duration": "0:50", "size": "18MB"},
        {"title": "Nồi chiên không dầu 5L", "shop": "Điện Máy XYZ", "date": date(2026, 6, 10), "duration": "1:02", "size": "35MB"},
        {"title": "Balo laptop chống nước", "shop": "TravelGo Store", "date": date(2026, 6, 5), "duration": "0:38", "size": "15MB"},
        {"title": "Kem dưỡng ẩm ban đêm", "shop": "Beauty House", "date": date(2026, 5, 30), "duration": "0:33", "size": "11MB"},
        {"title": "Tai nghe bluetooth chống ồn", "shop": "Điện Máy XYZ", "date": date(2026, 5, 22), "duration": "0:40", "size": "16MB"},
    ]
if "users" not in st.session_state:
    st.session_state.users = {}          # username -> {"password_hash":.., "email":..}
if "current_user" not in st.session_state:
    st.session_state.current_user = None
if "pending_registration" not in st.session_state:
    st.session_state.pending_registration = None
if "ai_provider" not in st.session_state:
    st.session_state.ai_provider = list(AI_PROVIDERS.keys())[0]
if "ai_api_key" not in st.session_state:
    st.session_state.ai_api_key = ""
if "ai_model" not in st.session_state:
    st.session_state.ai_model = ""

# =========================================================
# HÀM PHỤ TRỢ: GỌI AI (ĐA NHÀ CUNG CẤP)
# =========================================================
def ai_ready():
    return bool(st.session_state.get("ai_api_key")) and bool(st.session_state.get("ai_provider"))


def _call_claude(api_key, model, system, prompt, image_b64=None, image_mime=None, max_tokens=800):
    content = []
    if image_b64:
        content.append({"type": "image", "source": {"type": "base64", "media_type": image_mime or "image/jpeg", "data": image_b64}})
    content.append({"type": "text", "text": prompt})
    r = requests.post(
        "https://api.anthropic.com/v1/messages",
        headers={"x-api-key": api_key, "anthropic-version": "2023-06-01", "content-type": "application/json"},
        json={"model": model, "max_tokens": max_tokens, "system": system,
              "messages": [{"role": "user", "content": content}]},
        timeout=60,
    )
    r.raise_for_status()
    data = r.json()
    return "".join(b.get("text", "") for b in data.get("content", []) if b.get("type") == "text").strip()


def _call_openai(api_key, model, system, prompt, image_b64=None, image_mime=None, max_tokens=800):
    content = [{"type": "text", "text": prompt}]
    if image_b64:
        content.append({"type": "image_url", "image_url": {"url": f"data:{image_mime or 'image/jpeg'};base64,{image_b64}"}})
    r = requests.post(
        "https://api.openai.com/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "max_completion_tokens": max_tokens,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": content}]},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def _call_gemini(api_key, model, system, prompt, image_b64=None, image_mime=None, max_tokens=800):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"
    parts = [{"text": prompt}]
    if image_b64:
        parts.append({"inline_data": {"mime_type": image_mime or "image/jpeg", "data": image_b64}})
    payload = {
        "system_instruction": {"parts": [{"text": system}]},
        "contents": [{"role": "user", "parts": parts}],
        "generationConfig": {"maxOutputTokens": max_tokens},
    }
    r = requests.post(url, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data["candidates"][0]["content"]["parts"][0]["text"].strip()


def _call_openai_compatible(base_url, api_key, model, system, prompt, max_tokens=800):
    r = requests.post(
        f"{base_url}/chat/completions",
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        json={"model": model, "max_tokens": max_tokens,
              "messages": [{"role": "system", "content": system}, {"role": "user", "content": prompt}]},
        timeout=60,
    )
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def ask_ai(prompt, system=None, max_tokens=700, image_bytes=None, image_media_type=None):
    """Gọi AI theo nhà cung cấp đã cấu hình. Trả về None nếu chưa cấu hình hoặc gọi lỗi
    -> nơi gọi hàm này sẽ tự động dùng nội dung minh hoạ (demo) thay thế."""
    if not ai_ready():
        return None
    provider_label = st.session_state.ai_provider
    cfg = AI_PROVIDERS[provider_label]
    api_key = st.session_state.ai_api_key.strip()
    model = st.session_state.ai_model.strip() or cfg["models"][0]
    sys_prompt = system or (
        "Bạn là trợ lý AI cho nền tảng quản lý & sản xuất nội dung mạng xã hội (AI Content Studio). "
        "Luôn trả lời bằng tiếng Việt, súc tích, tự nhiên và hữu ích."
    )
    img_b64 = base64.b64encode(image_bytes).decode("utf-8") if image_bytes else None
    try:
        key = cfg["key"]
        if key == "claude":
            return _call_claude(api_key, model, sys_prompt, prompt, img_b64, image_media_type, max_tokens)
        elif key == "openai":
            return _call_openai(api_key, model, sys_prompt, prompt, img_b64, image_media_type, max_tokens)
        elif key == "gemini":
            return _call_gemini(api_key, model, sys_prompt, prompt, img_b64, image_media_type, max_tokens)
        elif key == "grok":
            return _call_openai_compatible("https://api.x.ai/v1", api_key, model, sys_prompt, prompt, max_tokens)
        elif key == "deepseek":
            return _call_openai_compatible("https://api.deepseek.com", api_key, model, sys_prompt, prompt, max_tokens)
        elif key == "mistral":
            return _call_openai_compatible("https://api.mistral.ai/v1", api_key, model, sys_prompt, prompt, max_tokens)
    except Exception as e:
        st.session_state["_last_ai_error"] = str(e)
        return None
    return None


def ai_status_caption():
    if ai_ready():
        model = st.session_state.ai_model.strip() or AI_PROVIDERS[st.session_state.ai_provider]["models"][0]
        st.caption(f"🤖 AI đang hoạt động: **{st.session_state.ai_provider}** · model `{model}`")
    else:
        st.caption("🔌 AI chưa được cấu hình — đang hiển thị nội dung minh hoạ. Vào Trang chủ để nhập API Key.")


def show_ai_insight(context_label, results):
    """Thêm 1 nhận xét ngắn từ AI bên dưới kết quả tìm kiếm (dùng ở các tab Tải video)."""
    if not results or not ai_ready():
        return
    titles = ", ".join(v["title"] for v in results[:8])
    insight = ask_ai(
        f"Bối cảnh: {context_label}. Dựa trên danh sách video sau, đưa ra 1 câu nhận xét ngắn gọn "
        f"và 1 gợi ý hành động cho người dùng (tiếng Việt, tối đa 2 câu): {titles}",
        max_tokens=150,
    )
    if insight:
        st.info(f"🤖 **AI nhận xét:** {insight}")


# =========================================================
# HÀM PHỤ TRỢ: XÁC THỰC THÀNH VIÊN & GỬI EMAIL OTP
# =========================================================
def hash_password(pw):
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def generate_otp():
    return f"{random.randint(0, 999999):06d}"


def _get_secret(key):
    try:
        if key in st.secrets:
            return st.secrets[key]
    except Exception:
        pass
    return os.environ.get(key, "")


def send_verification_email(code, username, to_email=ADMIN_VERIFICATION_EMAIL):
    """Gửi email chứa mã OTP qua Gmail SMTP. Cần cấu hình SMTP_EMAIL / SMTP_PASSWORD
    (App Password của Gmail) trong st.secrets hoặc biến môi trường."""
    smtp_email = _get_secret("SMTP_EMAIL")
    smtp_password = _get_secret("SMTP_PASSWORD")
    if not smtp_email or not smtp_password:
        return False, "missing_credentials"
    try:
        msg = MIMEText(
            f"Có yêu cầu đăng ký thành viên mới trên AI Content Studio.\n\n"
            f"Tài khoản đăng ký: {username}\n"
            f"Mã xác nhận: {code}\n"
            f"Mã có hiệu lực trong {OTP_EXPIRE_MINUTES} phút.\n\n"
            f"Nếu bạn không thực hiện yêu cầu này, có thể bỏ qua email."
        )
        msg["Subject"] = "[AI Content Studio] Mã xác nhận đăng ký thành viên"
        msg["From"] = smtp_email
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15) as server:
            server.login(smtp_email, smtp_password)
            server.sendmail(smtp_email, [to_email], msg.as_string())
        return True, None
    except Exception as e:
        return False, str(e)


# ============ HÀM DÙNG CHUNG: HIỂN THỊ KẾT QUẢ VIDEO ============
def render_video_results(results):
    if not results:
        st.info("Không tìm thấy video nào phù hợp với tiêu chí tìm kiếm.")
        return
    st.caption(f"🔎 Tìm thấy **{len(results)}** video phù hợp")
    cols = st.columns(3)
    for i, v in enumerate(results):
        with cols[i % 3]:
            with st.container(border=True):
                st.markdown(
                    "<div style='height:120px;display:flex;align-items:center;justify-content:center;"
                    "background:#e5e7eb;border-radius:8px;color:#6b7280;font-size:28px;'>🎞️</div>",
                    unsafe_allow_html=True
                )
                st.markdown(f"**{v['title']}**")
                st.caption(f"🏪 {v['shop']}  ·  📅 {v['date'].strftime('%d/%m/%Y')}")
                st.caption(f"⏱️ {v['duration']}  ·  💾 {v['size']}")
                bc1, bc2 = st.columns(2)
                bc1.button("⬇️ Tải về", key=f"dl_{v['title']}_{i}", use_container_width=True)
                bc2.button("➕ Thêm vào dự án", key=f"add_{v['title']}_{i}", use_container_width=True)


def ai_semantic_filter(query, lib, context_label="tìm theo tên sản phẩm"):
    """Dùng AI để chọn ra các video phù hợp về mặt ngữ nghĩa với từ khoá.
    Nếu AI chưa sẵn sàng hoặc lỗi -> quay về so khớp chuỗi con (demo)."""
    if not query:
        return lib
    if not ai_ready():
        return [v for v in lib if query.lower() in v["title"].lower()]
    titles = [v["title"] for v in lib]
    listing = "\n".join(f"{i}. {ttl}" for i, ttl in enumerate(titles))
    resp = ask_ai(
        f"Bối cảnh: {context_label}. Từ khoá người dùng nhập: \"{query}\".\n"
        f"Dưới đây là danh sách video (đánh số):\n{listing}\n\n"
        f"Hãy trả về CHỈ MỘT dòng JSON dạng mảng số chỉ mục (index) của các video phù hợp với từ khoá "
        f"(kể cả phù hợp theo nghĩa gần đúng/đồng nghĩa), ví dụ: [0,2,5]. Nếu không có video nào phù hợp, trả về [].",
        max_tokens=200,
    )
    if resp:
        try:
            match = re.search(r"\[[\d,\s]*\]", resp)
            if match:
                idxs = json.loads(match.group(0))
                filtered = [lib[i] for i in idxs if isinstance(i, int) and 0 <= i < len(lib)]
                if filtered:
                    return filtered
        except Exception:
            pass
    return [v for v in lib if query.lower() in v["title"].lower()]


# ============ SIDEBAR - THANH ĐIỀU HƯỚNG ============
with st.sidebar:
    st.title("🎛️ AI Content Studio")
    st.caption("Nền tảng quản lý nội dung thông minh")
    menu = st.radio(
        "Điều hướng",
        ["🏠 TRANG CHỦ", "📥 TẢI VIDEO", "📝 TẠO MÔ TẢ", "🌐 DỊCH THUẬT",
         "🎬 PHỤ ĐỀ & LỒNG TIẾNG", "🚀 XUẤT BẢN & LÊN LỊCH"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    if st.session_state.current_user:
        st.caption(f"👤 Đang đăng nhập: **{st.session_state.current_user}**")
    ai_status_caption()
    st.markdown("---")
    st.caption(" Bản thử nghiệm\n LyanTran")

# =========================================================
# 1. TRANG CHỦ
# =========================================================
if menu == "🏠 TRANG CHỦ":
    st.header("🏠 Trang chủ")

    # ---------------------------------------------------
    # 1.1 KHU VỰC CẤU HÌNH AI (chọn nhà cung cấp + API key)
    # ---------------------------------------------------
    with st.container(border=True):
        st.subheader("🤖 Cấu hình AI tích hợp hệ thống")
        st.caption(
            "Chọn nhà cung cấp AI và nhập API Key để kích hoạt AI thật cho toàn bộ tính năng: "
            "tạo mô tả, dịch thuật, tìm kiếm thông minh, tạo phụ đề, gợi ý caption & lịch đăng..."
        )
        provider_names = list(AI_PROVIDERS.keys())
        cfg_c1, cfg_c2 = st.columns([1.3, 2])
        with cfg_c1:
            provider_label = st.selectbox(
                "Chọn AI", provider_names,
                index=provider_names.index(st.session_state.ai_provider)
                if st.session_state.ai_provider in provider_names else 0,
                key="ai_provider_select",
            )
        with cfg_c2:
            api_key_input = st.text_input(
                "API Key", value=st.session_state.ai_api_key, type="password",
                placeholder=AI_PROVIDERS[provider_label]["help"], key="ai_api_key_input",
            )
        # --- Chọn model bằng dropdown (kèm tuỳ chọn tự nhập nếu muốn model khác) ---
        model_choices = AI_PROVIDERS[provider_label]["models"] + [CUSTOM_MODEL_LABEL]
        current_model = st.session_state.ai_model.strip()
        default_idx = model_choices.index(current_model) if current_model in model_choices else 0
        mcol1, mcol2 = st.columns([1.3, 2])
        with mcol1:
            model_select = st.selectbox(
                "Chọn model", model_choices, index=default_idx, key="ai_model_select",
            )
        with mcol2:
            if model_select == CUSTOM_MODEL_LABEL:
                custom_model_input = st.text_input(
                    "Nhập tên model tuỳ chỉnh",
                    value=current_model if current_model not in AI_PROVIDERS[provider_label]["models"] else "",
                    placeholder="VD: gpt-5.6, gemini-3.5-pro...",
                    key="ai_model_custom_input",
                )
            else:
                custom_model_input = ""
                st.write("")

        scol1, scol2 = st.columns([1, 3])
        with scol1:
            if st.button("💾 Lưu cấu hình AI", type="primary", use_container_width=True):
                final_model = custom_model_input.strip() if model_select == CUSTOM_MODEL_LABEL else model_select
                st.session_state.ai_provider = provider_label
                st.session_state.ai_api_key = api_key_input.strip()
                st.session_state.ai_model = final_model
                st.success(f"Đã lưu cấu hình AI: {provider_label} · model `{final_model}`")
                st.rerun()
        with scol2:
            st.write("")
            ai_status_caption()
        st.caption(
            "🔒 API Key chỉ được lưu tạm trong phiên làm việc hiện tại (session), không ghi ra ổ đĩa, "
            "và chỉ dùng để gọi trực tiếp tới nhà cung cấp AI bạn đã chọn."
        )

    st.write("")

    # ---------------------------------------------------
    # 1.2 KHU VỰC ĐĂNG NHẬP / ĐĂNG KÝ THÀNH VIÊN
    # ---------------------------------------------------
    with st.container(border=True):
        if st.session_state.current_user:
            cA, cB = st.columns([4, 1])
            with cA:
                st.success(f"👋 Xin chào, **{st.session_state.current_user}**! Bạn đã đăng nhập.")
            with cB:
                if st.button("Đăng xuất", use_container_width=True):
                    st.session_state.current_user = None
                    st.rerun()
        else:
            st.subheader("🔐 Thành viên")
            tab_login, tab_register = st.tabs(["Đăng nhập", "Đăng ký"])

            with tab_login:
                lu = st.text_input("Tên đăng nhập", key="login_user")
                lp = st.text_input("Mật khẩu", type="password", key="login_pw")
                if st.button("Đăng nhập", key="btn_login"):
                    user = st.session_state.users.get(lu)
                    if user and user["password_hash"] == hash_password(lp):
                        st.session_state.current_user = lu
                        st.success("Đăng nhập thành công!")
                        st.rerun()
                    else:
                        st.error("Sai tên đăng nhập hoặc mật khẩu.")

            with tab_register:
                pending = st.session_state.pending_registration
                if pending is None:
                    ru = st.text_input("Tên đăng nhập", key="reg_user")
                    r_email = st.text_input("Email của bạn (để liên hệ)", key="reg_email")
                    rp = st.text_input("Mật khẩu", type="password", key="reg_pw")
                    rp2 = st.text_input("Xác nhận mật khẩu", type="password", key="reg_pw2")
                    if st.button("Gửi mã xác nhận", key="btn_send_otp", type="primary"):
                        if not ru or not rp:
                            st.error("Vui lòng nhập đầy đủ tên đăng nhập và mật khẩu.")
                        elif ru in st.session_state.users:
                            st.error("Tên đăng nhập đã tồn tại.")
                        elif rp != rp2:
                            st.error("Mật khẩu xác nhận không khớp.")
                        elif r_email and not re.match(r"[^@]+@[^@]+\.[^@]+", r_email):
                            st.error("Email không hợp lệ.")
                        else:
                            code = generate_otp()
                            ok, err = send_verification_email(code, ru)
                            st.session_state.pending_registration = {
                                "username": ru, "password_hash": hash_password(rp),
                                "email": r_email, "otp": code,
                                "expires": t.time() + OTP_EXPIRE_MINUTES * 60,
                                "send_ok": ok, "send_err": err,
                            }
                            st.rerun()
                else:
                    # Hiển thị ĐÚNG trạng thái gửi email đã lưu lại (không bị mất sau khi rerun)
                    if pending.get("send_ok"):
                        st.success(f"✅ Đã gửi email thành công đến **{ADMIN_VERIFICATION_EMAIL}**. Vui lòng kiểm tra hộp thư (kể cả mục Spam) và nhập mã bên dưới.")
                    elif pending.get("send_err") == "missing_credentials":
                        st.warning(
                            "⚠️ Chưa cấu hình SMTP (SMTP_EMAIL / SMTP_PASSWORD trong `.streamlit/secrets.toml`) nên "
                            f"CHƯA gửi được email thật. Chế độ demo — mã xác nhận của bạn là **{pending['otp']}** "
                            f"(sẽ được gửi thật tới {ADMIN_VERIFICATION_EMAIL} sau khi bạn cấu hình SMTP và khởi động lại app)."
                        )
                    else:
                        st.error(
                            f"❌ Gửi email thất bại — lỗi: `{pending.get('send_err')}`. "
                            f"Mã demo để bạn test tạm: **{pending['otp']}**"
                        )
                    st.caption(f"Tài khoản đang chờ xác nhận: `{pending['username']}`")
                    code_input = st.text_input("Nhập mã xác nhận (6 chữ số)", key="otp_input", max_chars=6)
                    cc1, cc2 = st.columns(2)
                    with cc1:
                        if st.button("Xác nhận & Hoàn tất đăng ký", type="primary", use_container_width=True):
                            if t.time() > pending["expires"]:
                                st.error("Mã xác nhận đã hết hạn. Vui lòng đăng ký lại.")
                                st.session_state.pending_registration = None
                            elif code_input.strip() == pending["otp"]:
                                st.session_state.users[pending["username"]] = {
                                    "password_hash": pending["password_hash"],
                                    "email": pending["email"],
                                }
                                st.session_state.current_user = pending["username"]
                                st.session_state.pending_registration = None
                                st.success("🎉 Đăng ký thành công! Bạn đã được đăng nhập.")
                                st.balloons()
                                st.rerun()
                            else:
                                st.error("Mã xác nhận không đúng.")
                    with cc2:
                        if st.button("Huỷ / Đăng ký lại", use_container_width=True):
                            st.session_state.pending_registration = None
                            st.rerun()

    st.markdown("---")

    # ---------------------------------------------------
    # 1.3 TÌM KIẾM & DANH SÁCH BÀI ĐĂNG
    # ---------------------------------------------------
    col_search, col_btn = st.columns([5, 1])
    with col_search:
        keyword = st.text_input("Tìm kiếm", placeholder="🔍 Nhập từ khóa để tìm nội dung...",
                                 label_visibility="collapsed")
    with col_btn:
        st.button("Tìm kiếm", use_container_width=True)

    st.subheader("📋 Danh sách bài đăng / video gần đây")
    data = st.session_state.posts
    filtered = [p for p in data if keyword.lower() in p["title"].lower()] if keyword else data

    if not filtered:
        st.info("Không tìm thấy nội dung phù hợp.")
    else:
        cols = st.columns(3)
        for i, post in enumerate(filtered):
            with cols[i % 3]:
                with st.container(border=True):
                    st.markdown(f"**{post['title']}**")
                    if post["status"] == "Đã xong":
                        st.success(f"✅ {post['status']}")
                    else:
                        st.warning(f"⏳ {post['status']}")
                    st.button("Xem chi tiết", key=f"view_{i}", use_container_width=True)

        if st.button("🤖 AI gợi ý nội dung tiếp theo nên sản xuất"):
            with st.spinner("AI đang phân tích danh sách bài đăng..."):
                idea = ask_ai(
                    "Dựa trên danh sách bài đăng/video sau, hãy gợi ý 3 ý tưởng nội dung tiếp theo nên sản xuất, "
                    "kèm lý do ngắn gọn (tiếng Việt): " + ", ".join(p["title"] for p in filtered)
                )
            if idea:
                st.write(idea)
            else:
                st.info(
                    "💡 (Nội dung minh hoạ — hãy cấu hình AI ở trên để nhận gợi ý thật) Thử làm thêm video review "
                    "sản phẩm mới, bài viết xu hướng theo mùa, và clip mẹo vặt ngắn để đa dạng nội dung."
                )

# =========================================================
# 2. TẢI VIDEO (TÌM KIẾM & TẢI VỀ)
# =========================================================
elif menu == "📥 TẢI VIDEO":
    st.header("📥 Tải video từ kho nội dung")
    st.caption("Tìm kiếm video theo nhiều tiêu chí khác nhau (được hỗ trợ bởi AI), sau đó tải về hoặc thêm trực tiếp vào dự án.")
    ai_status_caption()

    tab_name, tab_image, tab_shop, tab_date, tab_link, tab_all = st.tabs(
        ["🔤 Theo tên sản phẩm", "🖼️ Theo hình ảnh", "🏪 Theo Shop", "📅 Theo ngày đăng",
         "🔗 Theo đường link", "🧩 Tất cả tiêu chí"]
    )
    lib = st.session_state.video_library

    # --- Tìm theo tên sản phẩm (AI hiểu ngữ nghĩa) ---
    with tab_name:
        c1, c2 = st.columns([4, 1])
        with c1:
            name_kw = st.text_input("Tên sản phẩm", placeholder="VD: áo thun, giày sneaker, nồi chiên...")
        with c2:
            st.write("")
            search_name = st.button("🔍 Tìm kiếm", key="search_name", use_container_width=True, type="primary")
        if search_name:
            with st.spinner("AI đang phân tích từ khoá và tìm video phù hợp..."):
                t.sleep(0.3)
                results = ai_semantic_filter(name_kw, lib, "tìm video theo tên sản phẩm") if name_kw else lib
            render_video_results(results)
            show_ai_insight("kết quả tìm theo tên sản phẩm", results)

    # --- Tìm theo hình ảnh (AI Vision) ---
    with tab_image:
        st.write("Tải lên hình ảnh sản phẩm để AI phân tích và tìm các video có nội dung/sản phẩm tương tự.")
        img = st.file_uploader("Tải ảnh sản phẩm", type=["png", "jpg", "jpeg"], key="img_search")
        if img is not None:
            st.image(img, width=200)
        search_img = st.button("🔍 Tìm kiếm bằng hình ảnh", key="search_img", type="primary")
        if search_img:
            if img is None:
                st.error("⚠️ Vui lòng tải lên một hình ảnh trước khi tìm kiếm!")
            else:
                img_bytes = img.getvalue()
                mime = img.type or "image/jpeg"
                results = lib[:4]
                if ai_ready() and AI_PROVIDERS[st.session_state.ai_provider]["supports_image"]:
                    with st.spinner("AI đang phân tích hình ảnh..."):
                        titles = "\n".join(f"{i}. {v['title']} ({v['shop']})" for i, v in enumerate(lib))
                        resp = ask_ai(
                            "Đây là ảnh một sản phẩm. Hãy mô tả ngắn gọn sản phẩm trong ảnh (tiếng Việt, 1 câu), "
                            f"sau đó từ danh sách video sau, chọn các video có sản phẩm liên quan gần nhất:\n{titles}\n\n"
                            "Trả lời gồm 2 phần: dòng đầu là mô tả ảnh; dòng thứ hai CHỈ chứa JSON mảng index, "
                            "ví dụ: [0,3]",
                            image_bytes=img_bytes, image_media_type=mime, max_tokens=300,
                        )
                    if resp:
                        st.write(f"🤖 **AI nhận diện:** {resp.splitlines()[0]}")
                        m = re.search(r"\[[\d,\s]*\]", resp)
                        if m:
                            try:
                                idxs = json.loads(m.group(0))
                                picked = [lib[i] for i in idxs if isinstance(i, int) and 0 <= i < len(lib)]
                                if picked:
                                    results = picked
                            except Exception:
                                pass
                else:
                    with st.spinner("Đang tìm video tương tự (chế độ minh hoạ)..."):
                        t.sleep(1.0)
                render_video_results(results)
                show_ai_insight("kết quả tìm theo hình ảnh sản phẩm", results)

    # --- Tìm theo Shop ---
    with tab_shop:
        shops = sorted(set(v["shop"] for v in lib))
        c1, c2 = st.columns([4, 1])
        with c1:
            shop_choice = st.selectbox("Chọn Shop", ["Tất cả"] + shops)
        with c2:
            st.write("")
            search_shop = st.button("🔍 Tìm kiếm", key="search_shop", use_container_width=True, type="primary")
        if search_shop:
            with st.spinner("Đang tìm video theo Shop..."):
                t.sleep(0.6)
            results = lib if shop_choice == "Tất cả" else [v for v in lib if v["shop"] == shop_choice]
            render_video_results(results)
            show_ai_insight(f"kết quả tìm theo shop {shop_choice}", results)

    # --- Tìm theo ngày đăng ---
    with tab_date:
        c1, c2, c3 = st.columns([2, 2, 1])
        with c1:
            from_date = st.date_input("Từ ngày", value=date(2026, 5, 1), key="date_from")
        with c2:
            to_date = st.date_input("Đến ngày", value=date.today(), key="date_to")
        with c3:
            st.write("")
            search_date = st.button("🔍 Tìm kiếm", key="search_date", use_container_width=True, type="primary")
        if search_date:
            with st.spinner("Đang tìm video theo khoảng ngày..."):
                t.sleep(0.6)
            if from_date > to_date:
                st.error("⚠️ 'Từ ngày' phải nhỏ hơn hoặc bằng 'Đến ngày'!")
            else:
                results = [v for v in lib if from_date <= v["date"] <= to_date]
                render_video_results(results)
                show_ai_insight("kết quả tìm theo khoảng ngày đăng", results)

    # --- Tìm theo đường link ---
    with tab_link:
        st.write("Dán đường link nguồn (trang sản phẩm, video, bài đăng...) để tìm kiếm nội dung chi tiết liên quan.")
        lc1, lc2 = st.columns([3, 1])
        with lc1:
            link_url = st.text_input("Đường link", placeholder="https://vidu.com/san-pham/ao-thun-nam", key="link_url")
        with lc2:
            link_mode = st.radio(
                "Chế độ tìm kiếm",
                ["🌐 Tìm tổng quát", "🎯 Tìm theo web đã post"],
                key="link_mode"
            )
        search_link = st.button("🔍 Tìm kiếm theo đường link", key="search_link", type="primary", use_container_width=True)

        if search_link:
            if not link_url.strip():
                st.error("⚠️ Vui lòng nhập đường link trước khi tìm kiếm!")
            else:
                domain = link_url.split("//")[-1].split("/")[0] if "//" in link_url else link_url.split("/")[0]
                if link_mode == "🌐 Tìm tổng quát":
                    with st.spinner("Đang tìm kiếm nội dung liên quan trên toàn bộ hệ thống..."):
                        t.sleep(1)
                    st.caption(f"🌐 Phạm vi tìm kiếm: **Tất cả nguồn** · Link tham chiếu: `{link_url}`")
                    results = lib  # Demo: tìm tổng quát trên toàn bộ kho
                else:
                    with st.spinner(f"Đang tìm kiếm nội dung trong phạm vi trang: {domain} ..."):
                        t.sleep(1)
                    st.caption(f"🎯 Phạm vi tìm kiếm: chỉ trong **{domain}** · Link tham chiếu: `{link_url}`")
                    # Demo: giả lập lọc theo shop có tên gần giống domain, nếu không khớp thì lấy 3 kết quả đầu
                    results = [v for v in lib if domain.split(".")[0].lower() in v["shop"].lower()] or lib[:3]
                render_video_results(results)
                show_ai_insight(f"kết quả tìm theo đường link {link_url}", results)

    # --- Tìm theo tất cả tiêu chí ---
    with tab_all:
        st.write("Kết hợp nhiều tiêu chí cùng lúc để tìm kiếm chính xác hơn.")
        ac1, ac2 = st.columns(2)
        with ac1:
            all_name = st.text_input("Tên sản phẩm", key="all_name", placeholder="Bỏ trống nếu không lọc")
            all_shop = st.selectbox("Shop", ["Tất cả"] + sorted(set(v["shop"] for v in lib)), key="all_shop")
        with ac2:
            all_from = st.date_input("Từ ngày", value=date(2026, 1, 1), key="all_from")
            all_to = st.date_input("Đến ngày", value=date.today(), key="all_to")
        all_img = st.file_uploader("Ảnh sản phẩm tham chiếu (tùy chọn)", type=["png", "jpg", "jpeg"], key="all_img")
        if all_img is not None:
            st.image(all_img, width=150)
        all_link_c1, all_link_c2 = st.columns([3, 1])
        with all_link_c1:
            all_link = st.text_input("Đường link tham chiếu (tùy chọn)", placeholder="https://...", key="all_link")
        with all_link_c2:
            all_link_mode = st.radio("Chế độ", ["🌐 Tổng quát", "🎯 Theo web"], key="all_link_mode")

        search_all = st.button("🔍 Tìm kiếm theo tất cả tiêu chí", key="search_all", type="primary", use_container_width=True)
        if search_all:
            with st.spinner("Đang tổng hợp và lọc kết quả theo mọi tiêu chí..."):
                t.sleep(1)
            results = lib
            if all_name:
                results = ai_semantic_filter(all_name, results, "tìm theo tất cả tiêu chí")
            if all_shop != "Tất cả":
                results = [v for v in results if v["shop"] == all_shop]
            results = [v for v in results if all_from <= v["date"] <= all_to]
            # Nếu có ảnh tham chiếu, demo giả lập ưu tiên 4 kết quả đầu
            if all_img is not None:
                results = results[:4]
            # Nếu có đường link và chọn "Theo web", demo giả lập lọc theo domain khớp tên shop
            if all_link.strip() and all_link_mode == "🎯 Theo web":
                dom = all_link.split("//")[-1].split("/")[0].split(".")[0].lower()
                results = [v for v in results if dom in v["shop"].lower()] or results[:3]
            render_video_results(results)
            show_ai_insight("kết quả tìm theo tất cả tiêu chí", results)

# =========================================================
# 3. TẠO MÔ TẢ
# =========================================================
elif menu == "📝 TẠO MÔ TẢ":
    st.header("📝 Tạo mô tả nội dung bằng AI")
    ai_status_caption()
    left, right = st.columns(2)

    with left:
        title = st.text_input("Tiêu đề bài đăng", placeholder="VD: Review điện thoại mới nhất 2026")
        media = st.file_uploader("Tải lên hình ảnh / video", type=["png", "jpg", "jpeg", "mp4", "mov"])
        if media is not None and media.type.startswith("image"):
            st.image(media, use_container_width=True)
        elif media is not None:
            st.video(media)

        if st.button("🤖 Auto-Describe bằng AI", use_container_width=True, type="primary"):
            image_bytes, image_mime = None, None
            if media is not None and media.type.startswith("image") and ai_ready() and \
                    AI_PROVIDERS[st.session_state.ai_provider]["supports_image"]:
                image_bytes, image_mime = media.getvalue(), media.type

            with st.spinner("AI đang phân tích nội dung..."):
                ai_text = ask_ai(
                    f"Viết một đoạn mô tả hấp dẫn (3-4 câu) bằng tiếng Việt cho bài đăng mạng xã hội có tiêu đề: "
                    f"'{title or 'nội dung của người dùng'}'. Giọng văn cuốn hút, phù hợp TikTok/Facebook, "
                    f"kèm 3-5 hashtag liên quan ở cuối.",
                    image_bytes=image_bytes, image_media_type=image_mime,
                )
            if ai_text:
                st.session_state.description = ai_text
                st.success("✅ AI đã sinh mô tả thành công!")
            else:
                st.session_state.description = (
                    f"Mô tả tự động cho \"{title or 'nội dung của bạn'}\": Đây là nội dung nổi bật với hình ảnh/video "
                    f"chất lượng cao, bố cục thu hút, truyền tải rõ thông điệp chính. Phù hợp để đăng tải trên các nền "
                    f"tảng mạng xã hội nhằm tăng tương tác và tiếp cận khách hàng mục tiêu."
                )
                st.info("ℹ️ Đang dùng nội dung minh hoạ — hãy cấu hình AI ở Trang chủ để nhận mô tả do AI thật tạo ra.")

    with right:
        st.session_state.description = st.text_area(
            "📄 Nội dung mô tả (AI sinh ra - có thể chỉnh sửa)",
            value=st.session_state.description, height=380
        )

# =========================================================
# 4. DỊCH THUẬT
# =========================================================
elif menu == "🌐 DỊCH THUẬT":
    st.header("🌐 Dịch thuật nội dung bằng AI")
    ai_status_caption()
    languages = ["Tiếng Việt", "Tiếng Anh", "Tiếng Hàn", "Tiếng Nhật", "Tiếng Trung"]

    c1, c2, c3 = st.columns([2, 2, 1.2])
    with c1:
        source_lang = st.selectbox("Ngôn ngữ gốc", languages, index=0)
    with c2:
        target_lang = st.selectbox("Ngôn ngữ đích", languages, index=1)
    with c3:
        st.write("")
        st.write("")
        translate_clicked = st.button("🔁 Dịch ngay", use_container_width=True, type="primary")

    col_src, col_dst = st.columns(2)
    with col_src:
        source_text = st.text_area(f"Văn bản gốc ({source_lang})", height=320,
                                    placeholder="Nhập nội dung cần dịch...")
    with col_dst:
        if translate_clicked and source_text.strip():
            with st.spinner("AI đang dịch..."):
                ai_translated = ask_ai(
                    f"Dịch đoạn văn bản sau từ {source_lang} sang {target_lang}, giữ nguyên văn phong tự nhiên, "
                    f"CHỈ trả về bản dịch, không thêm giải thích hay ghi chú:\n\n{source_text}",
                    max_tokens=1200,
                )
            if ai_translated:
                st.session_state.translated_text = ai_translated
            else:
                st.session_state.translated_text = f"[{target_lang}] {source_text}"
                st.info("ℹ️ Đang dùng bản dịch minh hoạ — hãy cấu hình AI ở Trang chủ để dịch thật.")
        st.session_state.translated_text = st.text_area(
            f"Kết quả dịch ({target_lang}) - có thể sửa trực tiếp",
            value=st.session_state.translated_text, height=320
        )

# =========================================================
# 5. PHỤ ĐỀ & LỒNG TIẾNG
# =========================================================
elif menu == "🎬 PHỤ ĐỀ & LỒNG TIẾNG":
    st.header("🎬 Phụ đề & Lồng tiếng")
    ai_status_caption()
    left, right = st.columns([1, 1.3])

    with left:
        st.subheader("▶️ Xem trước video")
        video_file = st.file_uploader("Tải video lên để xem trước", type=["mp4", "mov"])
        if video_file:
            st.video(video_file)
        else:
            with st.container(border=True):
                st.info("📽️ Chưa có video nào được tải lên.\n\nKhung xem trước sẽ hiển thị tại đây.")

        st.markdown("---")
        st.caption("🤖 AI tạo phụ đề tự động từ kịch bản/lời thoại")
        script_text = st.text_area("Dán kịch bản hoặc lời thoại video", height=140,
                                    placeholder="VD: Xin chào các bạn, hôm nay mình sẽ giới thiệu...")
        if st.button("🤖 Tạo phụ đề từ kịch bản", use_container_width=True):
            if not script_text.strip():
                st.error("⚠️ Vui lòng nhập kịch bản trước.")
            else:
                with st.spinner("AI đang chia dòng và gắn mốc thời gian..."):
                    ai_resp = ask_ai(
                        "Chia đoạn kịch bản sau thành các dòng phụ đề ngắn (mỗi dòng tối đa ~10 từ), "
                        "ước lượng mốc thời gian hợp lý bắt đầu từ 00:00, mỗi dòng cách nhau 2-4 giây. "
                        "CHỈ trả về JSON là một mảng các object có 2 khoá 'time' (định dạng 'MM:SS - MM:SS') "
                        f"và 'text'. Kịch bản:\n\n{script_text}",
                        max_tokens=1000,
                    )
                new_subs = None
                if ai_resp:
                    try:
                        m = re.search(r"\[.*\]", ai_resp, re.DOTALL)
                        if m:
                            new_subs = json.loads(m.group(0))
                    except Exception:
                        new_subs = None
                if new_subs:
                    st.session_state.subtitles = new_subs
                    st.success("✅ AI đã tạo phụ đề từ kịch bản!")
                    st.rerun()
                else:
                    st.info("ℹ️ Chưa cấu hình AI (hoặc AI lỗi) — hãy cấu hình ở Trang chủ để dùng tính năng này.")

    with right:
        st.subheader("💬 Danh sách phụ đề (Vietsub)")
        for i, sub in enumerate(st.session_state.subtitles):
            tc1, tc2 = st.columns([1, 3])
            with tc1:
                st.session_state.subtitles[i]["time"] = st.text_input(
                    "Timeline", value=sub["time"], key=f"time_{i}", label_visibility="collapsed")
            with tc2:
                st.session_state.subtitles[i]["text"] = st.text_input(
                    "Nội dung", value=sub["text"], key=f"text_{i}", label_visibility="collapsed",
                    placeholder="Nhập lời thoại phụ đề...")

        if st.button("➕ Thêm dòng phụ đề"):
            st.session_state.subtitles.append({"time": "00:00 - 00:00", "text": ""})
            st.rerun()

        st.markdown("---")
        if st.button("🔊 Tạo giọng nói AI (Lồng tiếng tự động)", use_container_width=True, type="primary"):
            with st.spinner("Đang tổng hợp giọng nói từ văn bản..."):
                t.sleep(1.5)
            st.success("✅ Đã tạo file lồng tiếng thành công! (Bản demo)")
            st.caption(
                "ℹ️ Lồng tiếng thật cần một dịch vụ Text-to-Speech riêng (vd: ElevenLabs, Google TTS) — "
                "phần này hiện là bản minh hoạ giao diện."
            )

# =========================================================
# 6. XUẤT BẢN & LÊN LỊCH
# =========================================================
elif menu == "🚀 XUẤT BẢN & LÊN LỊCH":
    st.header("🚀 Xuất bản & Lên lịch đăng bài")
    ai_status_caption()
    left, right = st.columns([1, 1.1])

    with left:
        st.subheader("Chọn nền tảng đăng")
        fb = st.checkbox("📘 Facebook")
        tk = st.checkbox("🎵 TikTok")
        yt = st.checkbox("▶️ YouTube")

        st.subheader("Lên lịch đăng bài")
        pub_date = st.date_input("Ngày đăng")
        pub_time = st.time_input("Giờ đăng", value=time(9, 0))

        if st.button("🤖 AI gợi ý caption & giờ đăng tối ưu", use_container_width=True):
            platforms_sel = [name for name, checked in [("Facebook", fb), ("TikTok", tk), ("YouTube", yt)] if checked]
            with st.spinner("AI đang phân tích và đưa ra gợi ý..."):
                sugg = ask_ai(
                    "Người dùng chuẩn bị đăng bài lên các nền tảng: "
                    f"{', '.join(platforms_sel) or 'chưa chọn nền tảng'}. Nội dung mô tả hiện tại: "
                    f"\"{st.session_state.get('description', '') or '(chưa có mô tả)'}\". "
                    "Hãy gợi ý: 1) một caption ngắn hấp dẫn kèm hashtag phù hợp cho từng nền tảng, "
                    "2) khung giờ đăng tối ưu trong ngày (tiếng Việt, súc tích)."
                )
            if sugg:
                st.markdown(sugg)
            else:
                st.info(
                    "💡 (Minh hoạ) Buổi tối 19:00-21:00 thường có tương tác tốt trên Facebook/TikTok; "
                    "hãy cấu hình AI ở Trang chủ để nhận gợi ý caption thật theo nội dung của bạn."
                )

        st.markdown("---")
        if st.button("🚀 ĐĂNG BÀI NGAY", use_container_width=True, type="primary"):
            platforms = [name for name, checked in
                         [("Facebook", fb), ("TikTok", tk), ("YouTube", yt)] if checked]
            if not platforms:
                st.error("⚠️ Vui lòng chọn ít nhất một nền tảng để đăng!")
            else:
                st.success(f"✅ Đã lên lịch đăng vào {pub_date} lúc {pub_time} trên: {', '.join(platforms)}")
                st.balloons()

    with right:
        st.subheader("📱 Xem trước bài đăng (Live Preview)")
        with st.container(border=True):
            st.markdown("**🎬 AI Content Studio**")
            st.caption("Vừa xong · 🌍 Công khai")
            preview_text = st.session_state.get("description") or "Nội dung bài đăng của bạn sẽ hiển thị tại đây..."
            st.write(preview_text)
            with st.container(border=True):
                st.markdown(
                    "<div style='height:220px;display:flex;align-items:center;justify-content:center;"
                    "background:#e5e7eb;border-radius:8px;color:#6b7280;'>🖼️ Khung xem trước hình ảnh/video</div>",
                    unsafe_allow_html=True
                )
            pc1, pc2, pc3 = st.columns(3)
            pc1.button("👍 Thích", key="like_prev", use_container_width=True)
            pc2.button("💬 Bình luận", key="cmt_prev", use_container_width=True)
            pc3.button("↗️ Chia sẻ", key="share_prev", use_container_width=True)
