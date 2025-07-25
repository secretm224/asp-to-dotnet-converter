import streamlit as st
import re
from datetime import datetime
from typing import Callable, Union

# 페이지 설정
st.set_page_config(
    page_title="Classic ASP to C# Syntax Converter",
    page_icon="🔄",
    layout="wide"
)

class AspToCSharpConverter:
    def __init__(self):
        self.conversion_rules: list[tuple[str, Union[str, Callable[[re.Match], str]]]] = [
            (r'<%\s*', ''),
            (r'\s*%>', ''),
            (r'CStr\s*\(\s*Date\s*\(\s*\)\s*\)', r'DateTime.Now.ToString("yyyy-MM-dd")'),
            (r'DateTime\\.Now\\.ToString\("yyyy-MM-dd"\)\\s*<=\\s*"([0-9\\-]+)"', r'DateTime.Now <= DateTime.Parse("\1")'),
            (r'RequestQ\("([^\"]+)"\)', r'(Request.QueryString["\1"] ?? "")'),
            (r'Len\(([^)]+)\)', r'\1.Length'),
            (r'Left\(([^,]+),\s*(\d+)\)', r'\1.Substring(0, \2)'),
            (r'Right\(([^,]+),\s*(\d+)\)', r'\1.Substring(\1.Length - \2)'),
            (r'If\s+(.+?)\s+Then', r'if (\1) {'),
            (r'ElseIf\s+(.+?)\s+Then', r'} else if (\1) {'),
            (r'Else(?!\s+if)', r'} else {'),
            (r'End\s+If', r'}'),
            (r'\bTrue\b', r'true'),
            (r'\bFalse\b', r'false'),
            (r'\s+<>\s+', r' != '),
            (r'\s+=\s+', r' == '),
            (r'\s+And\s+', r' && '),
            (r'\s+Or\s+', r' || '),
            (r'\bNot\s+', r'!'),
            (r'\s+&\s+', r' + '),
            # 주석 변환
            (r"'\s*(.+?)$", r'// \1'),
            # Select Case 변환
            (r'Select\s+Case\s+(.+)', r'switch (\1) {'),
            (r'Case\s+"?([^\"]+)"?', r'case "\1":'),
            (r'Case\s+Else', r'default:'),
            (r'End\s+Select', r'}'),
            # 변수 선언 확장 변환
            (r'Dim\s+(\w+)\s*:\s*\1\s*=\s*(True|False)', lambda m: f"bool {m.group(1)} = {m.group(2).lower()};"),
            (r'Dim\s+(\w+)\s*:\s*\1\s*=\s*\"([^\"]*)\"', r'string \1 = "\2";'),
            (r'Dim\s+(\w+)\s*:\s*\1\s*=\s*([0-9]+\.[0-9]+)', r'double \1 = \2;'),
            (r'Dim\s+(\w+)\s*:\s*\1\s*=\s*([0-9]+)', r'int \1 = \2;'),
            (r'Dim\s+([^:=]+)', lambda m: '\n'.join([f'string {v.strip()} = "";' for v in m.group(1).split(',')])),
            # 변수 값 할당 처리 (== -> =) + 세미콜론 추가
            (r'^(\s*)(\w+)\s*==\s*(.+)', r'\1\2 = \3;')
        ]

    def convert_asp_to_csharp(self, asp_code: str) -> str:
        result_lines = []
        for line in asp_code.splitlines():
            original_line = line
            line = line.strip()
            is_if_condition = line.lower().startswith("if ") or line.lower().startswith("else if ")

            for pattern, replacement in self.conversion_rules:
                if ('== true' in pattern or '== false' in pattern) and is_if_condition:
                    continue
                if callable(replacement):
                    line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)
                else:
                    line = re.sub(pattern, replacement, line, flags=re.IGNORECASE)

            if not is_if_condition:
                line = re.sub(r'\b(\w+)\s*==\s*true\b', r'\1 = true;', line)
                line = re.sub(r'\b(\w+)\s*==\s*false\b', r'\1 = false;', line)

            result_lines.append(line)

        return "\n".join(result_lines)


def main():
    st.title("🔄 ASP to C# Converter with Full Variable & Case Support")
    converter = AspToCSharpConverter()
    asp_code = st.text_area("ASP 코드 입력", height=300)

    if st.button("변환하기"):
        converted = converter.convert_asp_to_csharp(asp_code)
        converted_lines = []
        indent_level = 0
        for line in converted.splitlines():
            line = line.strip()
            if line == '}':
                indent_level = max(0, indent_level - 1)
            converted_lines.append('    ' * indent_level + line)
            if line.endswith('{') or line.endswith(':'):
                indent_level += 1
        formatted_code = '\n'.join(converted_lines)

        st.subheader("변환된 C# 코드")
        st.code(formatted_code, language="csharp")

if __name__ == "__main__":
    main()
