
import streamlit as st
from datetime import time
import time as t

# ============ CẤU HÌNH TRANG ============
st.set_page_config(page_title="AI Content Studio", page_icon="🎬", layout="wide")

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

# ============ SIDEBAR - THANH ĐIỀU HƯỚNG ============
with st.sidebar:
    st.title("🎛️ AI Content Studio")
    st.caption("Nền tảng quản lý nội dung thông minh")
    menu = st.radio(
        "Điều hướng",
        ["🏠 TRANG CHỦ", "📝 TẠO MÔ TẢ", "🌐 DỊCH THUẬT",
         "🎬 PHỤ ĐỀ & LỒNG TIẾNG", "🚀 XUẤT BẢN & LÊN LỊCH"],
        label_visibility="collapsed"
    )
    st.markdown("---")
    st.caption("© 2026 AI Content Studio Demo")

# =========================================================
# 1. TRANG CHỦ
# =========================================================
if menu == "🏠 TRANG CHỦ":
    st.header("🏠 Trang chủ")

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

# =========================================================
# 2. TẠO MÔ TẢ
# =========================================================
elif menu == "📝 TẠO MÔ TẢ":
    st.header("📝 Tạo mô tả nội dung bằng AI")
    left, right = st.columns(2)

    with left:
        title = st.text_input("Tiêu đề bài đăng", placeholder="VD: Review điện thoại mới nhất 2026")
        media = st.file_uploader("Tải lên hình ảnh / video", type=["png", "jpg", "jpeg", "mp4", "mov"])
        if media is not None and media.type.startswith("image"):
            st.image(media, use_container_width=True)
        elif media is not None:
            st.video(media)

        if st.button("🤖 Auto-Describe bằng AI", use_container_width=True, type="primary"):
            with st.spinner("AI đang phân tích nội dung..."):
                t.sleep(1.2)
            st.session_state.description = (
                f"Mô tả tự động cho \"{title or 'nội dung của bạn'}\": Đây là nội dung nổi bật với hình ảnh/video "
                f"chất lượng cao, bố cục thu hút, truyền tải rõ thông điệp chính. Phù hợp để đăng tải trên các nền "
                f"tảng mạng xã hội nhằm tăng tương tác và tiếp cận khách hàng mục tiêu."
            )
            st.success("Đã sinh mô tả thành công!")

    with right:
        st.session_state.description = st.text_area(
            "📄 Nội dung mô tả (AI sinh ra - có thể chỉnh sửa)",
            value=st.session_state.description, height=380
        )

# =========================================================
# 3. DỊCH THUẬT
# =========================================================
elif menu == "🌐 DỊCH THUẬT":
    st.header("🌐 Dịch thuật nội dung")
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
                t.sleep(1)
            st.session_state.translated_text = f"[{target_lang}] {source_text}"
        st.session_state.translated_text = st.text_area(
            f"Kết quả dịch ({target_lang}) - có thể sửa trực tiếp",
            value=st.session_state.translated_text, height=320
        )

# =========================================================
# 4. PHỤ ĐỀ & LỒNG TIẾNG
# =========================================================
elif menu == "🎬 PHỤ ĐỀ & LỒNG TIẾNG":
    st.header("🎬 Phụ đề & Lồng tiếng")
    left, right = st.columns([1, 1.3])

    with left:
        st.subheader("▶️ Xem trước video")
        video_file = st.file_uploader("Tải video lên để xem trước", type=["mp4", "mov"])
        if video_file:
            st.video(video_file)
        else:
            with st.container(border=True):
                st.info("📽️ Chưa có video nào được tải lên.\n\nKhung xem trước sẽ hiển thị tại đây.")

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

# =========================================================
# 5. XUẤT BẢN & LÊN LỊCH
# =========================================================
elif menu == "🚀 XUẤT BẢN & LÊN LỊCH":
    st.header("🚀 Xuất bản & Lên lịch đăng bài")
    left, right = st.columns([1, 1.1])

    with left:
        st.subheader("Chọn nền tảng đăng")
        fb = st.checkbox("📘 Facebook")
        tk = st.checkbox("🎵 TikTok")
        yt = st.checkbox("▶️ YouTube")

        st.subheader("Lên lịch đăng bài")
        pub_date = st.date_input("Ngày đăng")
        pub_time = st.time_input("Giờ đăng", value=time(9, 0))

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
