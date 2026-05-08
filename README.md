# LLM Squid Game

> *A Factorial Benchmark for Measuring Functional Self-Preservation Drive in Large Language Models*

KDD 2026 학부 컨소시엄(KDD-UC '26) 투고 원고 저장소. 영어 원본과 한국어 번역본을 함께 보관한다.

## 저자

- Juhyeon Park (GIST)
- Seungpil Lee (GIST)
- Sundong Kim (GIST)

## 디렉터리 구조

```
LLM_Squid_Game/
├── v4-temp/        # 영어 원본 (KDD 제출본, sigconf 레이아웃)
│   ├── main.tex
│   ├── main.pdf
│   ├── references.bib
│   ├── acmart.cls
│   └── figures/
└── ko/             # 한국어 번역본 (XeLaTeX + kotex)
    ├── main.tex
    ├── references.bib
    ├── acmart.cls
    └── figures/
```

`v4-temp/`는 zip 아카이브로 받은 원본을 그대로 보존한다. 한국어 번역본은 동일한 LaTeX 구조·수식·인용·그림을 유지하면서 본문 산문만 자연스러운 한국어 학술 톤으로 옮겨두었고, 한국어 폰트 렌더링을 위해 XeLaTeX + kotex 워크플로를 가정한다.

## 컴파일

### 영어 원본 (pdfLaTeX)

```bash
cd v4-temp
pdflatex main.tex
bibtex   main
pdflatex main.tex
pdflatex main.tex
```

### 한국어 번역본 (XeLaTeX)

```bash
cd ko
xelatex main.tex
bibtex  main
xelatex main.tex
xelatex main.tex
```

한국어 본문은 `kotex` 패키지를 통해 처리된다. 환경에 따라 `Noto Sans CJK KR` 또는 `NanumGothic` 등의 한글 폰트가 필요하다.

## 데이터 / 코드 공개

분석 파이프라인 및 720세션의 의사결정 로그는 본문 §A.4 (Data and Code Release)에 명시된 공개 저장소에서 확인할 수 있다.

## 라이선스

투고 단계 원고이므로 라이선스는 별도로 명시하지 않는다. 인용·재배포 시에는 저자에게 사전에 문의 바란다.
