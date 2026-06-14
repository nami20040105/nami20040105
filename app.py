import streamlit as st
from io import BytesIO
import requests
from PIL import Image

from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.units import mm

from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

pdfmetrics.registerFont(UnicodeCIDFont("HeiseiKakuGo-W5"))

# =============================
# 定数
# =============================
PAGE_W, PAGE_H = landscape(A4)

MARGIN = 10 * mm
COL_WIDTH = 80 * mm
GAP = 15 * mm

FRAME = 16 * mm
IMG = 14 * mm

FONT_SIZE = 8

LINE_GAP = 10 * mm


# =============================
# 画像取得
# =============================
def get_image(file, url):
    if file:
        img = Image.open(file)
        bio = BytesIO()
        img.save(bio, format="PNG")
        bio.seek(0)
        return bio

    if url:
        try:
            res = requests.get(url)
            res.raise_for_status()
            return BytesIO(res.content)
        except:
            return None

    return None


# =============================
# 折り返し
# =============================
def wrap(text, n=18):
    return [text[i:i + n] for i in range(0, len(text), n)]


# =============================
# ★本の高さを固定で定義（重要）
# =============================
def book_height():
    return FRAME + 25 * mm


# =============================
# PDF生成（完全修正版）
# =============================
def make_pdf_bytes(books):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=landscape(A4))

    x_positions = [
        MARGIN,
        MARGIN + COL_WIDTH + GAP,
        MARGIN + (COL_WIDTH + GAP) * 2
    ]

    c.setFont("HeiseiKakuGo-W5", FONT_SIZE)
    c.setLineWidth(0.3)

    col = 0
    y = PAGE_H - MARGIN

    for book in books:

        h = book_height()

        # =========================
        # 改ページ・列管理
        # =========================
        if y - h < MARGIN:
            col += 1
            y = PAGE_H - MARGIN

        if col >= 3:
            c.showPage()
            c.setFont("HeiseiKakuGo-W5", FONT_SIZE)
            col = 0
            y = PAGE_H - MARGIN

        x = x_positions[col]

        bottom_y = y - FRAME

        # =========================
        # 枠
        # =========================
        c.rect(x, bottom_y, FRAME, FRAME)

        # =========================
        # 画像
        # =========================
        img_io = book.get("image")

        if img_io:
            try:
                img_io.seek(0)
                img = ImageReader(img_io)

                c.drawImage(
                    img,
                    x + (FRAME - IMG) / 2,
                    bottom_y + (FRAME - IMG) / 2,
                    width=IMG,
                    height=IMG,
                    preserveAspectRatio=True,
                    mask="auto"
                )
            except:
                pass

        # =========================
        # テキスト
        # =========================
        text_x = x + FRAME + 4 * mm
        text_y = bottom_y + FRAME - 10

        lines = []

        if book.get("title"):
            lines += wrap("タイトル：" + book["title"])

        if book.get("author"):
            lines += wrap("著者：" + book["author"])

        if book.get("translator"):
            lines += wrap("訳者：" + book["translator"])

        if book.get("publisher"):
            lines += wrap("出版社：" + book["publisher"])

        if book.get("year"):
            lines += wrap("出版年：" + str(book["year"]))

        if book.get("pages"):
            lines += wrap("ページ数：" + str(book["pages"]) + "頁")

        for line in lines:
            c.drawString(text_x, text_y, line)
            text_y -= LINE_GAP

        # =========================
        # 区切り線（必ず本の直下）
        # =========================
        line_y = bottom_y - 2 * mm
        c.line(x, line_y, x + COL_WIDTH, line_y)

        # =========================
        # 次の本は「線のすぐ下」から開始
        # =========================
        y = line_y - 2 * mm

    c.save()
    buffer.seek(0)
    return buffer


# =============================
# UI
# =============================
st.title("読書シールメーカー 📚")

if "books" not in st.session_state:
    st.session_state.books = []


title = st.text_input("タイトル")
author = st.text_input("著者")
translator = st.text_input("訳者")
publisher = st.text_input("出版社")
year = st.text_input("出版年")
pages = st.text_input("ページ数")

file = st.file_uploader("画像（任意）")
url = st.text_input("画像URL")


if st.button("追加"):
    img = get_image(file, url)

    st.session_state.books.append({
        "title": title,
        "author": author,
        "translator": translator,
        "publisher": publisher,
        "year": year,
        "pages": pages,
        "image": img
    })

    st.rerun()


# =============================
# 一覧
# =============================
st.subheader("一覧")

for i, b in enumerate(st.session_state.books):
    col1, col2 = st.columns([6, 1])

    with col1:
        st.markdown(
            f"""
**{i+1}. {b.get('title', '')}**

- 著者：{b.get('author', '')}
- 訳者：{b.get('translator', '')}
- 出版社：{b.get('publisher', '')}
- 出版年：{b.get('year', '')}
- ページ数：{b.get('pages', '')}
"""
        )

    with col2:
        if st.button("削除", key=i):
            st.session_state.books.pop(i)
            st.rerun()


# =============================
# PDF
# =============================
if st.session_state.books:
    pdf = make_pdf_bytes(st.session_state.books)

    st.download_button(
        "PDFダウンロード",
        pdf,
        file_name="books.pdf",
        mime="application/pdf"
    )