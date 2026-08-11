import cv2
import os
import numpy as np

def process_book_scan(image_path, output_folder):
    # 1. 이미지 읽기
    filename = os.path.basename(image_path)
    img = cv2.imread(image_path)
    
    if img is None:
        print(f"이미지를 불러올 수 없습니다: {filename}")
        return

    # 2. 전처리: 그레이스케일 변환 및 노이즈 제거
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    blur = cv2.GaussianBlur(gray, (5, 5), 0)

    # 3. 책 영역 감지 (Thresholding & Contours)
    # 배경과 책의 경계를 찾기 위해 이진화(Binarization) 수행
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # 윤곽선(Contours) 찾기
    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print(f"책의 윤곽선을 찾을 수 없습니다: {filename}")
        return

    # 가장 큰 윤곽선이 책일 확률이 높음
    c = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(c)

    # 4. 여백 제거 (Crop)
    # 약간의 여유를 두고 자르거나 타이트하게 자르려면 아래 수치 조정 가능
    crop_img = img[y:y+h, x:x+w]

    # 5. 반으로 자르기 (중심점 보정 및 대폭 중첩 적용)
    h_c, w_c, _ = crop_img.shape
    
    # [중요 수정 1] 중심점 이동 (Center Shift)
    # 양수면 오른쪽, 음수면 왼쪽으로 이동합니다.
    # 오른쪽 페이지가 잘리므로, 기준선을 왼쪽으로 50픽셀 정도 당깁니다.
    shift_center = -50 
    mid_point = (w_c // 2) + shift_center

    # [중요 수정 2] 중첩 범위 대폭 확대 (Overlap)
    # 기존 70에서 300으로 늘려, 제본선 주변을 아주 넉넉하게 포함시킵니다.
    # 나중에 보기에 안 좋으면 조금씩 줄이면 되지만, 텍스트 손실을 막는 게 우선입니다.
    overlap = 300 

    # 파이썬 슬라이싱 범위가 이미지 크기를 벗어나지 않도록 안전장치 추가
    start_left = 0
    end_left = min(w_c, mid_point + overlap)
    
    start_right = max(0, mid_point - overlap)
    end_right = w_c

    # 물리적 왼쪽 페이지 (잘린 중심선보다 오른쪽으로 300px 더 가져옴)
    left_page = crop_img[:, start_left:end_left]
    
    # 물리적 오른쪽 페이지 (잘린 중심선보다 왼쪽으로 300px 더 가져옴)
    right_page = crop_img[:, start_right:end_right]

    # 6. 저장 (순서 변경: 우철 방식 적용)
    name_no_ext = os.path.splitext(filename)[0]
    
    # 오른쪽 페이지가 먼저 읽히므로 _1, 왼쪽이 _2가 됩니다.
    first_page_path = os.path.join(output_folder, f"{name_no_ext}_1.jpg") # 오른쪽
    second_page_path = os.path.join(output_folder, f"{name_no_ext}_2.jpg") # 왼쪽

    cv2.imwrite(first_page_path, right_page)
    cv2.imwrite(second_page_path, left_page)
    
    print(f"완료: {filename} -> 우철(Right-to-Left) 순서로 저장됨")

def main():
    # 설정: 입력 폴더와 출력 폴더
    input_folder = "./1_one_sheets"  # 현재 폴더 (이미지가 있는 곳)
    output_folder = "./2_two_sides" # 결과물이 저장될 폴더

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 현재 폴더의 모든 jpg 파일 처리
    files = [f for f in os.listdir(input_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

    # [추가] 테스트를 위해 처음 3장만 뽑아서 실행
    # files = files[10:15] ##############
    
    print(f"총 {len(files)}개의 파일을 처리합니다...")
    
    for f in files:
        process_book_scan(os.path.join(input_folder, f), output_folder)

if __name__ == "__main__":
    main()