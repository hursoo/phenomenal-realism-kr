import pandas as pd
import re
import os

class InoueFinalParserV3:
    def __init__(self, book_id, start_page="a0"):
        self.book_id = book_id
        self.data = []
        self.global_sort_order = 0
        self.current_page = start_page 
        
        # [상태 추적 변수]
        self.curr_chap_id = None
        self.curr_sec_id = None
        self.curr_item_id = None
        
        # [카운터 변수]
        self.chap_count = 0
        self.sec_count = 0
        self.item_count = 0
        self.para_count = 0 

    def _get_uid(self):
        self.global_sort_order += 1
        return f"{self.book_id}_{self.global_sort_order:05d}"

    def _increment_page(self, page_str):
        """페이지 번호 증가 (a4 -> a5, 10 -> 11)"""
        if page_str.isdigit():
            return str(int(page_str) + 1)
        match = re.search(r'(\d+)$', page_str)
        if match:
            num_part = match.group(1)
            prefix = page_str[:match.start()]
            new_num = int(num_part) + 1
            return f"{prefix}{new_num}"
        return page_str

    def parse_file(self, file_path):
        if not os.path.exists(file_path):
            print(f"❌ 파일을 찾을 수 없습니다: {file_path}")
            return

        print(f"📂 파일 분석 시작: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Root 생성
        self.data.append({
            "uid": self._get_uid(),
            "local_id": "ROOT",
            "page_info": str(self.current_page),
            "line_class": "STRUCT",
            "kr_text": "철학과 종교 (전체)", 
            "structure_id": "ROOT",
            "parent_id": None,
            "depth_level": 0,
            "sort_order": self.global_sort_order
        })

        for line in lines:
            line = line.strip()
            if not line: continue

            # --- [1] 주석/해설(///) 처리 (ANNOTATION) ---
            if line.startswith('///'):
                anno_content = line.replace('///', '', 1).strip()
                parent = self.curr_item_id or self.curr_sec_id or self.curr_chap_id or "ROOT"
                self._add_row("ANNOTATION", parent, anno_content, 99, parent, str(self.current_page), "ANNO")
                continue

            # --- [2] 구조(Header) 파싱 ---
            header_match = re.match(r'^(#{1,3})\s*(.+)', line)

            if header_match:
                marker = header_match.group(1)
                content = header_match.group(2).strip()

                if marker == '###':
                    self.item_count += 1
                    self.para_count = 0
                    parent = self.curr_sec_id if self.curr_sec_id else self.curr_chap_id
                    if not parent: parent = self.curr_chap_id or "ROOT"
                    s_id = f"{parent}-I{self.item_count:02d}"
                    self.curr_item_id = s_id
                    self._add_row("STRUCT", s_id, content, 3, parent, str(self.current_page), s_id)

                elif marker == '##':
                    self.sec_count += 1
                    self.item_count = 0
                    self.para_count = 0
                    parent = self.curr_chap_id if self.curr_chap_id else "ROOT"
                    s_id = f"{self.curr_chap_id}-S{self.sec_count:02d}"
                    self.curr_sec_id = s_id
                    self.curr_item_id = None
                    self._add_row("STRUCT", s_id, content, 2, parent, str(self.current_page), s_id)

                elif marker == '#':
                    self.chap_count += 1
                    self.sec_count = 0
                    self.item_count = 0
                    self.para_count = 0
                    s_id = f"C{self.chap_count:02d}"
                    self.curr_chap_id = s_id
                    self.curr_sec_id = None
                    self.curr_item_id = None
                    self._add_row("STRUCT", s_id, content, 1, "ROOT", str(self.current_page), s_id)

            # --- [3] 본문(Text) 파싱 ---
            else:
                self.para_count += 1
                parent_struct = self.curr_item_id or self.curr_sec_id or self.curr_chap_id or "ROOT"
                para_id = f"{parent_struct}-P{self.para_count:02d}"
                
                sentences = re.split(r'(?<=[。\.])\s*', line)
                sent_count = 0
                
                for sent in sentences:
                    sent = sent.strip()
                    if not sent: continue
                    
                    sent_count += 1
                    
                    # [스마트 쪽수 처리 로직]
                    page_match = re.search(r'<([a-zA-Z0-9]+)>', sent)
                    
                    final_page_str = ""
                    clean_content = sent
                    
                    if page_match:
                        marker_val = page_match.group(1) # a4
                        next_page_val = self._increment_page(marker_val) # a5
                        
                        # 마커 위치 확인: 문장의 '맨 끝'에 있는지?
                        # 마커 뒤에 아무 글자도 없거나 마침표/공백만 있으면 '끝'으로 간주
                        marker_end_pos = page_match.end()
                        remaining_text = sent[marker_end_pos:].strip()
                        
                        if not remaining_text:
                            # [Case A] 마커가 문장 끝에 있음 -> 현재 쪽수로 기록
                            final_page_str = marker_val # a4
                        else:
                            # [Case B] 마커가 문장 중간에 있음 -> 걸침 표시
                            final_page_str = f"{marker_val}-{next_page_val}" # a4-a5
                        
                        # 텍스트 정리 및 페이지 포인터 업데이트
                        clean_content = re.sub(r'<([a-zA-Z0-9]+)>', '', sent).strip()
                        self.current_page = next_page_val
                    else:
                        # 마커 없음 -> 현재 페이지 유지
                        final_page_str = str(self.current_page)
                    
                    sent_id = f"{para_id}-S{sent_count:02d}"
                    
                    self._add_row("TEXT", parent_struct, clean_content, 10, parent_struct, final_page_str, sent_id)

    def _add_row(self, line_class, structure_id, content, depth, parent_id, page_info, local_id):
        self.data.append({
            "uid": self._get_uid(),
            "local_id": local_id,
            "page_info": page_info,
            "line_class": line_class,
            "kr_text": content,
            "structure_id": structure_id,
            "parent_id": parent_id,
            "depth_level": depth,
            "sort_order": self.global_sort_order
        })

    def export_csv(self, filename):
        df = pd.DataFrame(self.data)
        cols = ["uid", "local_id", "page_info", "line_class", "kr_text", "structure_id", "parent_id", "depth_level", "sort_order"]
        df = df[cols]
        df.to_csv(filename, index=False, encoding='utf-8-sig')
        print(f"✅ 변환 완료! '{filename}' 파일이 생성되었습니다. (총 {len(df)}행)")
        return df

if __name__ == "__main__":
    input_filename = "final_result_v7.1(20250109)_plus.txt" 
    output_filename = "inoue_complete_db_v3.csv"

    parser = InoueFinalParserV3("BK_IT_1915_PR", start_page="a0")
    parser.parse_file(input_filename)
    parser.export_csv(output_filename)