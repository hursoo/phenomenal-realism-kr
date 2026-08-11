import fitz  # PyMuPDF
import os

# ==========================================
# 설정: PDF 파일 경로와 저장할 폴더 이름
pdf_path = "./01_pdf/1a_origin_file/0_哲学と宗教_952938_0001.pdf"  # PDF 파일명 수정하세요
output_folder = "1_one_sheets"
# ==========================================

if not os.path.exists(output_folder):
    os.makedirs(output_folder)

doc = fitz.open(pdf_path)

print(f"총 {len(doc)}페이지 변환을 시작합니다...")

for i, page in enumerate(doc):
    # dpi 300 이상의 고화질로 변환 (matrix=2.0 ~ 3.0 추천)
    pix = page.get_pixmap(matrix=fitz.Matrix(2.0, 2.0))
    # 파일명은 0001.png, 0002.png 식이어야 ScanTailor가 순서를 잘 인식합니다.
    pix.save(f"{output_folder}/{i+1:04d}.png")

print("이미지 변환 완료!")