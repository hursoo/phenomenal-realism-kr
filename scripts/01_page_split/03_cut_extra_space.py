import cv2
import os
import numpy as np

def crop_content_union(image_path, output_folder, debug_mode=False):
    filename = os.path.basename(image_path)
    img = cv2.imread(image_path)
    
    if img is None:
        return

    h, w = img.shape[:2]
    
    # 1. 그레이스케일 및 이진화
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # 배경은 검은색, 글자는 흰색으로 반전 (Inverse)
    # OTSU 알고리즘이 자동으로 최적의 명암 기준을 잡습니다.
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

    # 2. [중요] 가장자리 노이즈 강제 제거 (Safety Mask)
    # 스캔된 이미지의 가장자리(제본선 그림자, 종이 끝 등)를 아예 무시합니다.
    # 상하 5%, 좌우 8% 영역을 검은색으로 칠해버립니다.
    margin_top_bottom = int(h * 0.05)
    margin_left_right = int(w * 0.08)
    
    thresh[:margin_top_bottom, :] = 0  # 상단 지움
    thresh[h-margin_top_bottom:, :] = 0 # 하단 지움
    thresh[:, :margin_left_right] = 0   # 좌측 지움
    thresh[:, w-margin_left_right:] = 0 # 우측 지움

    # 3. 팽창 (Dilation) - 글자들을 뚱뚱하게 만들어 덩어리화
    # 세로쓰기 텍스트이므로 세로(Vertical) 방향으로 더 강력하게 뭉칩니다.
    # kernel size: (가로 10, 세로 30) -> 세로로 긴 커널 사용
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (10, 30))
    dilated = cv2.dilate(thresh, kernel, iterations=3)

    # 4. 윤곽선 찾기
    contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    if not contours:
        print(f"[Skip] 내용 없음: {filename}")
        return

    # 5. [핵심 변경] 유효한 덩어리들을 '모두' 찾아서 하나의 큰 박스로 합치기
    min_x, min_y = w, h
    max_x, max_y = 0, 0
    found_valid_block = False

    # 너무 작은 점(먼지)은 무시하는 기준
    noise_threshold = (w * h) * 0.001 

    valid_contours = [] # 디버깅용 저장

    for cnt in contours:
        area = cv2.contourArea(cnt)
        if area > noise_threshold:
            x, y, cw, ch = cv2.boundingRect(cnt)
            
            # 현재 덩어리의 좌표를 전체 범위에 갱신
            if x < min_x: min_x = x
            if y < min_y: min_y = y
            if x + cw > max_x: max_x = x + cw
            if y + ch > max_y: max_y = y + ch
            
            found_valid_block = True
            valid_contours.append(cnt)

    if not found_valid_block:
        print(f"[Skip] 유효한 텍스트 블록 없음: {filename}")
        return

    # 6. 패딩(여백) 추가
    padding = 40 # 글자 주변에 40픽셀 여유 공간
    
    final_x = max(0, min_x - padding)
    final_y = max(0, min_y - padding)
    final_w = min(w, max_x + padding) - final_x
    final_h = min(h, max_y + padding) - final_y

    # 7. 디버깅 이미지 저장 (확인용)
    if debug_mode:
        vis = img.copy()
        # 인식된 유효 덩어리들 (빨간색)
        cv2.drawContours(vis, valid_contours, -1, (0, 0, 255), 2)
        # 최종 계산된 자를 범위 (초록색 박스)
        cv2.rectangle(vis, (final_x, final_y), (final_x + final_w, final_y + final_h), (0, 255, 0), 5)
        
        vis_path = os.path.join(output_folder, f"vis_{filename}")
        cv2.imwrite(vis_path, vis)

    # 8. 최종 자르기 및 저장
    cropped_img = img[final_y:final_y+final_h, final_x:final_x+final_w]
    
    save_path = os.path.join(output_folder, filename)
    cv2.imwrite(save_path, cropped_img)
    print(f"완료: {filename}")

def main():
    input_folder = "./2_two_sides"       # 1단계(반으로 자르기) 결과가 있는 폴더
    output_folder = "./3_cutted_results" # 최종 결과 폴더
    
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    # 테스트할 파일 목록 (반으로 잘린 파일들만)
    files = [f for f in os.listdir(input_folder) if f.endswith(('_1.jpg', '_2.jpg'))]
    
    # 일단 10개만 테스트
    # files = files[:10]

    print(f"총 {len(files)}개 파일에 대해 '통합 박스 크롭' 테스트 시작...")
    for f in files:
        crop_content_union(os.path.join(input_folder, f), output_folder)

if __name__ == "__main__":
    main()