# type: ignore
from typing import Optional, Union, cast
import streamlit as st
import requests
import json
import re
import time
from datetime import datetime

# 페이지 설정
st.set_page_config(
    page_title="Groq AI ASP to C# Converter",
    page_icon="⚡",
    layout="wide"
)

class GroqConverter:
    def __init__(self):
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama3-8b-8192"
        self.daily_limit = 14400  # 토큰
        self.rate_limit = 30      # 분당 요청수

    def create_expert_prompt(self, asp_code: str) -> str:
        """Groq LLaMA3에 최적화된 전문 프롬프트"""
        return f"""You are a senior software engineer specializing in Classic ASP to C# migration. Convert the following ASP code to modern C# with PERFECT accuracy.

CRITICAL CONVERSION RULES:
1. VARIABLE DECLARATIONS:
   - "Dim x : x = False" → "bool x = false;"
   - "Dim x : x = True" → "bool x = true;"
   - "Dim x : x = 123" → "int x = 123;"
   - "Dim x : x = \"text\"" → "string x = \"text\";"
   - "Dim x" (no assignment) → "string x = \"\";"
   - "Dim a, b, c" → separate lines: "string a = \"\"; string b = \"\"; string c = \"\";"

2. DATA TYPES - DETECT CAREFULLY:
   - False/True values → bool type
   - Numeric values → int type
   - String values → string type
   - No initial value → string type with empty string

3. OPERATORS:
   - " & " → " + " (string concatenation)
   - " <> " → " != " (not equal)
   - " And " → " && "
   - " Or " → " || "
   - "Not " → "!"

4. CONTROL FLOW:
   - "If x Then" → "if (x) {{"
   - "ElseIf x Then" → "}} else if (x) {{"
   - "Else" → "}} else {{"
   - "End If" → "}}"

5. LOOPS:
   - "For i = 1 To 10" → "for (int i = 1; i <= 10; i++) {{"
   - "For Each item In collection" → "foreach (var item in collection) {{"
   - "Next" → "}}"

6. FUNCTIONS:
   - "Function Name(params)" → "public string Name(params) {{"
   - "Sub Name(params)" → "public void Name(params) {{"
   - "End Function/Sub" → "}}"

7. STRING FUNCTIONS:
   - "Len(x)" → "x.Length"
   - "UCase(x)" → "x.ToUpper()"
   - "LCase(x)" → "x.ToLower()"
   - "Replace(x, \"a\", \"b\")" → "x.Replace(\"a\", \"b\")"
   - "Trim(x)" → "x.Trim()"

8. WEB OBJECTS:
   - "Response.Write x" → "Response.Write(x);"
   - "Request.QueryString(\"id\")" → "Request.QueryString[\"id\"]"
   - "Request.Form(\"name\")" → "Request.Form[\"name\"]"
   - "Session(\"user\")" → "Session[\"user\"]"

9. ARRAY FUNCTIONS:
   - "IsArray(x)" → "(x is Array)"
   - "UBound(x)" → "(x.Length - 1)"

10. SYNTAX:
    - Add semicolons to end statements
    - Use proper C# casing
    - Remove ASP delimiters (<% %>)

ORIGINAL ASP CODE:
```asp
{asp_code}
```

Convert to C# following the rules above. Return ONLY the converted C# code, no explanations:"""

    def convert_with_groq(self, asp_code: str, api_key: str) -> str:
        """Groq API를 사용한 고품질 변환"""
        # 입력 검증
        if not asp_code or not isinstance(asp_code, str):
            return "❌ 입력 코드가 올바르지 않습니다."
        
        if not api_key or not isinstance(api_key, str):
            return "🔑 API 키가 올바르지 않습니다."
            
        try:
            headers = {
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {
                        "role": "system", 
                        "content": "You are an expert Classic ASP to C# converter. You always follow conversion rules exactly and produce perfect C# code."
                    },
                    {
                        "role": "user", 
                        "content": self.create_expert_prompt(asp_code)
                    }
                ],
                "temperature": 0.1,  # 매우 낮은 온도로 일관성 확보
                "max_tokens": 2000,
                "top_p": 0.9,
                "stream": False
            }
            
            response = requests.post(
                self.api_url,
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                converted_code = result['choices'][0]['message']['content'].strip()
                
                # 응답 정리
                cleaned_code = self.clean_groq_output(converted_code)
                
                # 후처리 적용
                final_code = self.apply_postprocessing(cleaned_code)
                
                return final_code
            
            elif response.status_code == 429:
                return "⏰ 일일 사용량 초과 또는 속도 제한. 잠시 후 다시 시도하세요."
            elif response.status_code == 401:
                return "🔑 API 키가 잘못되었습니다. 키를 다시 확인해주세요."
            else:
                error_detail = response.json() if response.content else "Unknown error"
                return f"❌ Groq API 오류 ({response.status_code}): {error_detail}"
                
        except requests.exceptions.Timeout:
            return "⏰ 요청 시간 초과. 네트워크를 확인하고 다시 시도하세요."
        except Exception as e:
            return f"❌ 변환 중 오류: {str(e)}"

    def clean_groq_output(self, output: str) -> str:
        """Groq 출력 정리"""
        if not output or output is None:
            return ""
        
        # 안전한 문자열 변환
        safe_output = str(output).strip()
        
        # 마크다운 코드 블록 제거
        safe_output = re.sub(r'```(?:csharp|cs|c#)?\n?', '', safe_output)
        safe_output = re.sub(r'```\n?', '', safe_output)
        
        # 불필요한 설명 제거
        lines = safe_output.split('\n')
        code_lines = []
        
        for line in lines:
            if line is not None:
                line = str(line).strip()
                # 실제 코드 라인만 유지
                if line and not line.startswith(('///', 'Here', 'Note:', 'The converted', 'Output:', 'This converts')):
                    code_lines.append(line)
        
        return '\n'.join(code_lines)

    def apply_postprocessing(self, code: str) -> str:
        """Groq 결과에 정교한 후처리 적용"""
        if not code or code is None:
            return ""
        
        # 안전한 문자열 변환
        safe_code = str(code).strip()
        
        # 세부 수정 규칙들
        corrections = [
            # 불린 값 완벽 수정
            (r'string\s+(\w+)\s*=\s*"?False"?\s*;', r'bool \1 = false;'),
            (r'string\s+(\w+)\s*=\s*"?True"?\s*;', r'bool \1 = true;'),
            
            # ASP 스타일 연산자 수정
            (r'\s+&\s+', r' + '),
            (r'\s+<>\s+', r' != '),
            (r'\bAnd\b', r'&&'),
            (r'\bOr\b', r'||'),
            (r'\bNot\s+', r'!'),
            
            # 웹 객체 완벽 변환
            (r'Response\.Write\s+([^;]+)(?!;)', r'Response.Write(\1);'),
            (r'Request\.QueryString\("([^"]+)"\)', r'Request.QueryString["\1"]'),
            (r'Request\.Form\("([^"]+)"\)', r'Request.Form["\1"]'),
            (r'Session\("([^"]+)"\)', r'Session["\1"]'),
            
            # 문자열 함수
            (r'Len\(([^)]+)\)', r'\1.Length'),
            (r'UCase\(([^)]+)\)', r'\1.ToUpper()'),
            (r'LCase\(([^)]+)\)', r'\1.ToLower()'),
            (r'Trim\(([^)]+)\)', r'\1.Trim()'),
            
            # 배열 함수
            (r'IsArray\(([^)]+)\)', r'(\1 is Array)'),
            (r'UBound\(([^)]+)\)', r'(\1.Length - 1)'),
            
            # 세미콜론 정리
            (r'([^;{}\s])\s*\n', r'\1;\n'),  # 줄 끝에 세미콜론 추가
            (r';;+', r';'),  # 중복 세미콜론 제거
            (r'}\s*;', r'}'),  # 중괄호 뒤 세미콜론 제거
        ]
        
        for pattern, replacement in corrections:
            safe_code = re.sub(pattern, replacement, safe_code, flags=re.IGNORECASE | re.MULTILINE)
        
        return safe_code.strip()

    def estimate_tokens(self, text: str) -> int:
        """토큰 수 계산"""
        if not text or not isinstance(text, str):
            return 0
            
        safe_text = text.strip()
        if not safe_text:
            return 0
            
        # 영어 기준 약 4자당 1토큰
        return len(safe_text) // 4

    def get_usage_info(self) -> dict:
        """사용량 정보 반환"""
        return {
            "daily_limit": self.daily_limit,
            "rate_limit": self.rate_limit,
            "model": self.model,
            "cost": "무료"
        }

def main():
    st.title("⚡ Groq AI ASP to C# 변환기")
    st.markdown("**LLaMA3-8B로 유료급 품질의 무료 변환**")
    
    converter = GroqConverter()
    
    # 사이드바
    with st.sidebar:
        st.header("⚡ Groq 정보")
        
        usage_info = converter.get_usage_info()
        st.success(f"""
        **🚀 Groq 무료 혜택:**
        - 모델: {usage_info['model']}
        - 일일 한도: {usage_info['daily_limit']:,} 토큰
        - 속도 제한: {usage_info['rate_limit']}회/분
        - 비용: {usage_info['cost']}
        """)
        
        st.markdown("---")
        
        # API 키 관리
        st.header("🔑 API 키 설정")
        
        if 'groq_token' not in st.session_state:
            st.session_state.groq_token = ""
        
        key_management = st.radio(
            "키 관리 방식:",
            ["임시 사용", "세션 저장"],
            help="세션 저장 시 브라우저 종료까지 유지"
        )
        
        if key_management == "임시 사용":
            groq_key = st.text_input(
                "Groq API Key:",
                type="password",
                placeholder="gsk_...",
                help="발급받은 Groq API 키를 입력하세요"
            )
        else:
            if st.session_state.groq_token:
                st.success(f"✅ 저장된 키 사용 중 (...{st.session_state.groq_token[-8:]})")
                groq_key = st.session_state.groq_token
                
                if st.button("🗑️ 저장된 키 삭제"):
                    st.session_state.groq_token = ""
                    st.rerun()
            else:
                new_key = st.text_input(
                    "Groq API Key:",
                    type="password",
                    placeholder="gsk_...",
                    help="키를 입력하고 저장하세요"
                )
                
                if new_key and st.button("💾 키 저장"):
                    st.session_state.groq_token = new_key
                    st.success("✅ 키가 세션에 저장되었습니다!")
                    st.rerun()
                
                groq_key = new_key
        
        # API 키 발급 안내
        if not groq_key:
            with st.expander("🚀 Groq API 키 발급 방법"):
                st.markdown("""
                **2분만에 무료 발급:**
                
                1. [console.groq.com](https://console.groq.com) 접속
                2. Google 계정으로 회원가입
                3. "API Keys" 메뉴 클릭
                4. "Create API Key" 클릭
                5. 이름 입력 후 "Submit"
                6. 생성된 키 복사 (한 번만 표시!)
                
                **💡 키 형식:** `gsk_...` 로 시작
                """)
        
        st.markdown("---")
        
        # 변환 옵션
        st.header("⚙️ 변환 설정")
        add_using = st.checkbox("using 문 자동 추가", value=True)
        add_namespace = st.checkbox("네임스페이스 추가", value=False)
        show_tokens = st.checkbox("토큰 사용량 표시", value=True)
        
        if add_namespace:
            namespace_name = st.text_input("네임스페이스 이름:", value="ConvertedCode")
        
        st.markdown("---")
        
        # 사용 통계
        st.header("📊 사용 현황")
        
        if 'groq_conversions' not in st.session_state:
            st.session_state.groq_conversions = 0
        if 'groq_tokens_used' not in st.session_state:
            st.session_state.groq_tokens_used = 0
        
        col_stats1, col_stats2 = st.columns(2)
        with col_stats1:
            st.metric("변환 횟수", st.session_state.groq_conversions)
        with col_stats2:
            st.metric("사용 토큰", f"{st.session_state.groq_tokens_used:,}")
        
        remaining_tokens = converter.daily_limit - st.session_state.groq_tokens_used
        if remaining_tokens > 0:
            st.success(f"남은 토큰: {remaining_tokens:,}")
        else:
            st.warning("일일 사용량 초과 (내일 리셋)")

    # 메인 영역
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📝 ASP 코드 입력")
        
        # 샘플 코드 버튼들
        sample_cols = st.columns(4)
        
        with sample_cols[0]:
            if st.button("🎯 기본", use_container_width=True):
                st.session_state.asp_sample = '''Dim isBizEvent : isBizEvent = False
Dim isBizEventTarget : isBizEventTarget = False
Dim isPersonEvent : isPersonEvent = False
Dim arrTarget
Dim arrMemberInfo, l_userid, l_userno, l_usertype, l_birthdt'''
        
        with sample_cols[1]:
            if st.button("🔄 반복문", use_container_width=True):
                st.session_state.asp_sample = '''Dim i, total : total = 0
For i = 1 To 10
    total = total + i
    Response.Write "숫자: " & i & ", 합계: " & total & "<br>"
Next
Response.Write "최종 합계: " & total'''
        
        with sample_cols[2]:
            if st.button("📊 함수", use_container_width=True):
                st.session_state.asp_sample = '''Function CalculateAge(birthYear)
    Dim currentYear
    currentYear = Year(Now())
    CalculateAge = currentYear - birthYear
End Function

Dim userAge
userAge = CalculateAge(1990)
Response.Write "나이: " & userAge'''
        
        with sample_cols[3]:
            if st.button("🌐 배열", use_container_width=True):
                st.session_state.asp_sample = '''If GLB_DEVICE = "IOS" Then
    Dim arrShowEvent
    arrShowEvent = SM_FLAG_CODE_TB_SEL_PROC()
    If IsArray(arrShowEvent) Then
        strEventOpenYN = UCase(arrShowEvent(0, 0))
        strIOSVersion = arrShowEvent(1, 0)
        If strEventOpenYN = "N" And GLB_VERSION = strIOSVersion Then
            strEventShowYN = "N"
        End If
    End If
End If'''
        
        # 코드 입력 영역
        asp_code = st.text_area(
            "Classic ASP 코드:",
            height=400,
            value=st.session_state.get('asp_sample', ''),
            placeholder="""예시:
Dim userName : userName = "홍길동"
Dim isActive : isActive = True
If userName <> "" Then
    Response.Write "Hello " & userName
End If""",
            key="asp_code_input"
        )
        
        # 토큰 예상 사용량
        if show_tokens and asp_code:
            safe_asp_code = cast(str, asp_code or "").strip()  # type: ignore
            if safe_asp_code:
                estimated_tokens = converter.estimate_tokens(safe_asp_code)
                st.info(f"💡 예상 토큰 사용량: ~{estimated_tokens:,}개")
        
        # 변환 버튼
        convert_button = st.button(
            "⚡ Groq으로 고품질 변환",
            type="primary",
            use_container_width=True,
            disabled=not groq_key or not asp_code or not cast(str, asp_code or "").strip()  # type: ignore
        )
        
        if st.button("🔄 코드 초기화", use_container_width=True):
            st.session_state.asp_sample = ''
            st.rerun()
    
    with col2:
        st.header("🎯 Groq 변환 결과")
        
        if not groq_key:
            st.warning("⚠️ 왼쪽에서 Groq API 키를 입력해주세요")
            
            st.info("""
            **🚀 Groq 장점:**
            - 유료급 변환 품질
            - 매우 빠른 응답 속도  
            - 정확한 타입 추론
            - ASP 문법 완벽 이해
            """)
        
        # 변환 실행
        elif convert_button and asp_code:
            safe_asp_code = cast(str, asp_code or "").strip()  # type: ignore
            
            if not safe_asp_code:
                st.error("❌ 입력된 ASP 코드가 없습니다.")
            else:
                with st.spinner("⚡ Groq LLaMA3-8B가 고품질 변환 중..."):
                    start_time = time.time()
                    
                    # 토큰 사용량 계산
                    input_tokens = converter.estimate_tokens(safe_asp_code)
                    
                    # Groq 변환 실행
                    result = converter.convert_with_groq(safe_asp_code, cast(str, groq_key))  # type: ignore
                    
                    end_time = time.time()
                    conversion_time = end_time - start_time
                
                # 결과 처리
                if result and not result.startswith(("⏰", "🔑", "❌")):
                    # 성공적인 변환
                    output_tokens = converter.estimate_tokens(result)
                    total_tokens = input_tokens + output_tokens
                    
                    # 사용량 업데이트
                    st.session_state.groq_conversions += 1
                    st.session_state.groq_tokens_used += total_tokens
                    
                    # using 문 추가
                    if add_using:
                        using_statements = """using System;
using System.Web;
using System.Web.UI;

"""
                        result = using_statements + result
                    
                    # 네임스페이스 추가
                    if add_namespace and 'namespace_name' in locals():
                        safe_result = cast(str, result)  # type: ignore
                        indented_code = '\n'.join(['    ' + line for line in safe_result.split('\n')])  # type: ignore
                        result = f"namespace {namespace_name}\n{{\n{indented_code}\n}}"
                    
                    # 성공 메시지
                    success_msg = f"✅ Groq 변환 완료! ({conversion_time:.1f}초)"
                    if show_tokens:
                        success_msg += f" | 토큰: {total_tokens:,}개"
                    
                    st.success(success_msg)
                    
                    # 변환된 코드 표시
                    st.code(result, language="csharp", line_numbers=True)
                    
                    # 액션 버튼들
                    col_action1, col_action2, col_action3 = st.columns(3)
                    
                    with col_action1:
                        st.download_button(
                            "📥 C# 파일 다운로드",
                            result,
                            file_name=f"groq_converted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.cs",
                            mime="text/x-csharp",
                            use_container_width=True
                        )
                    
                    with col_action2:
                        if st.button("📋 복사 안내", use_container_width=True):
                            st.info("💡 코드 블록 우상단의 복사 버튼을 사용하세요!")
                    
                    with col_action3:
                        if st.button("🔄 재변환", use_container_width=True):
                            st.rerun()
                    
                    # 상세 분석
                    with st.expander("📊 변환 품질 분석"):
                        col_detail1, col_detail2 = st.columns(2)
                        
                        with col_detail1:
                            st.metric("변환 시간", f"{conversion_time:.1f}초")
                            st.metric("입력 라인", len(safe_asp_code.split('\n')))  # type: ignore
                            
                        with col_detail2:
                            safe_result = cast(str, result)  # type: ignore
                            st.metric("출력 라인", len(safe_result.split('\n')))  # type: ignore
                            if show_tokens:
                                st.metric("토큰 사용량", f"{total_tokens:,}개")
                    
                    # Before & After 비교
                    with st.expander("🔍 변환 전후 비교"):
                        col_before, col_after = st.columns(2)
                        
                        with col_before:
                            st.write("**변환 전 (ASP):**")
                            st.code(safe_asp_code, language="vbscript")
                        
                        with col_after:
                            st.write("**변환 후 (C# by Groq):**")
                            st.code(cast(str, result), language="csharp")  # type: ignore
                    
                    # 품질 평가
                    st.subheader("⭐ 변환 품질 평가")
                    rating_cols = st.columns(5)
                    
                    for i, (emoji, desc) in enumerate([
                        ("😞", "나쁨"), ("😐", "보통"), ("🙂", "좋음"), 
                        ("😊", "매우좋음"), ("🤩", "완벽")
                    ]):
                        with rating_cols[i]:
                            if st.button(f"{emoji}\n{desc}", key=f"rating_{i}", use_container_width=True):
                                st.session_state.groq_rating = i + 1
                                st.success(f"평가 감사합니다! ({i+1}/5)")
                
                else:
                    # 변환 실패
                    if result:
                        st.error(cast(str, result))  # type: ignore
                        
                        result_str = cast(str, result)  # type: ignore
                        if "사용량 초과" in result_str:
                            st.info("💡 내일 다시 시도하거나, 다른 무료 AI를 사용해보세요.")
                        elif "API 키가 잘못" in result_str:
                            st.info("💡 API 키를 다시 확인하고 올바르게 입력해주세요.")
                    else:
                        st.error("❌ 알 수 없는 오류가 발생했습니다.")
        
        else:
            # 초기 화면
            st.info("👈 ASP 코드를 입력하고 변환을 시작하세요!")
            
            # Groq 품질 예시
            with st.expander("🏆 Groq 품질 예시"):
                st.markdown("**ASP 입력:**")
                st.code('''Dim isActive : isActive = True
Dim userName : userName = "홍길동"
If userName <> "" And isActive Then
    Response.Write "환영합니다 " & userName & "님!"
End If''', language="vbscript")
                
                st.markdown("**↓ Groq 변환 결과:**")
                st.code('''bool isActive = true;
string userName = "홍길동";
if (userName != "" && isActive) {
    Response.Write("환영합니다 " + userName + "님!");
}''', language="csharp")
                
                st.success("✅ 타입 추론, 연산자, 문법 모두 완벽!")

    # 하단 정보
    st.markdown("---")
    
    info_cols = st.columns(3)
    
    with info_cols[0]:
        st.info("""
        **⚡ Groq 사용 팁**
        - 복잡한 코드는 함수별로 나누어 변환
        - 일일 한도 초과 시 내일 다시 시도
        - 토큰 사용량을 확인하며 사용
        - 한 번에 너무 긴 코드는 피하기
        """)
    
    with info_cols[1]:
        st.warning("""
        **⚠️ 주의사항**
        - API 키는 절대 공유하지 마세요
        - 민감한 정보는 제거 후 변환
        - 변환 결과는 반드시 검토
        - 복잡한 DB 로직은 수동 확인
        """)
    
    with info_cols[2]:
        st.success("""
        **✅ 변환 후 작업**
        - Visual Studio에서 컴파일 테스트
        - using 문과 네임스페이스 확인
        - 에러 처리 로직 추가
        - 성능 최적화 검토
        """)

if __name__ == "__main__":
    # 세션 상태 초기화
    if 'groq_conversions' not in st.session_state:
        st.session_state.groq_conversions = 0
    if 'groq_tokens_used' not in st.session_state:
        st.session_state.groq_tokens_used = 0
    if 'asp_sample' not in st.session_state:
        st.session_state.asp_sample = ''
    if 'groq_token' not in st.session_state:
        st.session_state.groq_token = ''
    if 'groq_rating' not in st.session_state:
        st.session_state.groq_rating = 0
    
    # 메인 함수 실행
    main()