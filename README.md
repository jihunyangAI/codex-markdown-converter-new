# 마크다운 → HTML 변환기

Python 3.12 이상에서 UTF-8 마크다운 파일 하나를 CSS가 포함된 HTML 문서로 변환합니다. Windows에서 별도 웹 서버 없이 생성된 HTML을 열 수 있습니다.

## 설치 (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

가상 환경을 활성화할 필요 없이 다음 명령을 그대로 사용합니다.

## 실행

```powershell
.\.venv\Scripts\python.exe md_to_html.py input.md
.\.venv\Scripts\python.exe md_to_html.py input.md -o output.html
.\.venv\Scripts\python.exe md_to_html.py input.md -o output.html --overwrite
```

공백이 있는 경로는 따옴표로 감쌉니다. 기본 출력은 입력 파일과 같은 폴더의 같은 이름 `.html` 파일입니다. 출력 폴더는 자동 생성합니다. 기존 출력 파일을 바꾸려면 `--overwrite`가 필요하며 입력과 출력은 같은 파일일 수 없습니다. 정상 종료 코드는 0, 변환 오류는 1, 명령줄 인자 오류는 2입니다.

## 지원 범위 및 선택한 라이브러리

- 제목, 문단, 강조, 목록, 링크, 이미지, 인용문, 구분선, 표, fenced code block을 지원합니다.
- `markdown-it-py`: CommonMark 파서이며 표 규칙을 별도로 활성화합니다. 원시 HTML은 실행되지 않도록 텍스트로 이스케이프합니다.
- `nh3`: Rust ammonia 기반 HTML 정제 라이브러리로 변환 결과에 태그·속성·URL 허용 목록을 적용합니다. 표와 코드 언어 class는 유지합니다.
- `mdit-py-plugins`: `$...$` 인라인 수식과 `$$...$$` 블록 수식을 구분합니다. 코드 안의 수식 문법은 변환하지 않습니다.
- `latex2mathml`: LaTeX 수식을 MathML로 변환합니다. 수식도 정제한 뒤 저장하며 JavaScript나 CDN 없이 최신 Chrome, Edge, Firefox, Safari에서 표시합니다.
- 표 정렬용 인라인 스타일은 제거합니다. 코드 구문 강조, GUI, 웹 서버, 폴더 일괄 변환, 각주 및 체크박스 확장은 구현 범위 밖입니다.

공식 API 참고: [markdown-it-py](https://markdown-it-py.readthedocs.io/en/latest/using.html), [nh3](https://nh3.readthedocs.io/en/latest/).

UTF-8 BOM이 있는 입력도 읽습니다. 상대 링크·이미지 경로는 HTML 기준으로 해석되므로 출력 위치를 옮기면 상대 경로 대상도 함께 배치해야 합니다. 변환기는 외부 자원을 다운로드하지 않습니다. 생성한 HTML을 열면 브라우저가 외부 이미지 등 자원을 요청할 수 있습니다. 외부 링크는 클릭 시 접근합니다. 이미지 파일 자체는 검사하지 않습니다.

## 수식 작성

문장 안에서는 `$...$`, 별도 줄에서는 `$$...$$` 안에 LaTeX 수식을 작성합니다.

```markdown
에너지 공식은 $E=mc^2$ 입니다.

$$
x = \frac{-b \pm \sqrt{b^2 - 4ac}}{2a}
$$

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2}
$$
```

분수, 위·아래첨자, 제곱근, 합, 적분, 행렬 등 `latex2mathml`이 지원하는 수식을 사용할 수 있습니다. 전체 LaTeX 문서나 사용자 정의 패키지를 실행하는 기능은 아닙니다. 지원하지 않는 명령은 문자로 남을 수 있으며, 파서가 감지한 잘못된 수식은 변환 오류로 보고하고 출력 파일을 쓰지 않습니다.

인라인 수식은 `$` 바로 안쪽에 공백을 넣지 않습니다(`$x$`). 일반 달러 기호는 `\$`로 작성하세요. 코드 블록과 인라인 코드 안의 `$`는 그대로 유지됩니다. `\(...\)`, `\[...\]`, 수식 번호는 지원하지 않습니다. 수식 표시는 브라우저의 MathML 지원과 설치된 글꼴에 따라 달라질 수 있습니다.

Linux/macOS에서는 다음과 같이 실행합니다.

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python md_to_html.py 예제.md -o 예제.html
.venv/bin/python -m unittest -v
```

## 테스트

```powershell
.\.venv\Scripts\python.exe -m unittest -v
```

한글과 HTML 구조, 표, 코드 보존, 상대 경로, 위험한 HTML 및 URL 처리, 빈 파일, 잘못된 경로, 인코딩 오류, 덮어쓰기, 입력 파일 보호, 권한 오류를 검증합니다. 권한 오류는 OS별 권한 차이를 피하기 위해 읽기·쓰기 실패를 모의합니다.
