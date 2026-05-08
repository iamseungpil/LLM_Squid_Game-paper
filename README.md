# LLM Squid Game

> *A Factorial Benchmark for Measuring Functional Self-Preservation Drive in Large Language Models*

KDD 2026 학부 컨소시엄(KDD-UC '26) 투고 원고 저장소. 영어 원본과 한국어 번역본이 동일한 LaTeX 골격을 공유하고, `\paperLang` 한 줄을 바꿔 두 버전을 빌드한다.

## 저자

- Juhyeon Park (GIST)
- Seungpil Lee (GIST)
- Sundong Kim (GIST)

## 디렉터리 구조

```
LLM_Squid_Game-paper/
├── main.tex              # 공유 preamble + 언어 스위치 (\paperLang)
├── acmart.cls            # ACM SIG 클래스 (sigconf)
├── references.bib        # BibTeX 참고문헌 (en/ko 공통)
├── figures/              # 그림 파일 (en/ko 공통)
├── en/
│   ├── content.tex       # \input 오케스트레이터 (영어)
│   └── sections/
│       ├── 00_frontmatter.tex
│       ├── 01_introduction.tex
│       ├── 02_related_work.tex
│       ├── 03_benchmark.tex
│       ├── 04_empirical_findings.tex
│       ├── 05_discussion.tex
│       ├── 06_conclusion.tex
│       └── 07_appendix.tex
├── ko/
│   ├── content.tex       # \input 오케스트레이터 (한국어)
│   └── sections/         # 영어와 동일한 0~7 구성, 본문만 한국어
└── dist/
    ├── en_main.pdf       # 영어판 렌더 결과 (XeLaTeX)
    └── ko_main.pdf       # 한국어판 렌더 결과 (XeLaTeX)
```

본문·표·그림 캡션·섹션 제목·키워드만 한국어로 옮겼고, 수식·인용 키(`\citep`/`\citet`)·`\label`/`\ref`·테이블 구조·그림 경로는 한 글자도 변경하지 않았다.

## 컴파일

기본 엔진은 **XeLaTeX**이다. acmart 클래스가 양쪽 언어를 모두 받아내며, 한국어판은 `kotex` 패키지가 자동으로 로드된다(`\paperLang`이 `ko`일 때만).

### 영어판 빌드

```bash
# main.tex 안의 \paperLang을 en으로 둔 채로
xelatex main.tex
bibtex  main
xelatex main.tex
xelatex main.tex
```

### 한국어판 빌드

```bash
# main.tex 안의 \paperLang을 ko로 변경한 뒤
xelatex main.tex
bibtex  main
xelatex main.tex
xelatex main.tex
```

`dist/`에 들어 있는 PDF는 위 명령으로 빌드해 둔 결과이며, BibTeX 단계는 시스템에 `ACM-Reference-Format.bst`가 설치되어 있을 때 참고문헌 목록까지 정상 렌더한다 (`tlmgr install acmart` 또는 ACM 사이트의 `acmart.zip`에서 받아 설치).

## 데이터 / 코드 공개

분석 파이프라인 및 720세션의 의사결정 로그는 본문 §A.4(Data and Code Release)에 명시된 대로 별도 레포에서 공개된다 (https://github.com/GIST-DSLab/LLM-Squid-Game).

## 라이선스

투고 단계 원고이므로 라이선스는 별도로 명시하지 않는다. 인용·재배포 시에는 저자에게 사전에 문의 바란다.
