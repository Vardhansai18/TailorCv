# TailorCv

ATS-optimized resume generator powered by **LangGraph**. Compares your resume against a job description, iteratively refines the output using an ATS scoring feedback loop, and produces a finalized single-page LaTeX document.

## Features

- **Multi-LLM Support** — Use Anthropic Claude, OpenAI GPT, Google Gemini, or any OpenAI-compatible endpoint
- **LangGraph Pipeline** — Stateful graph with parse → generate → assemble → score → feedback loop
- **ATS Scoring Loop** — Automatically re-generates if the ATS score is below threshold (default: 85/100)
- **STAR Format Enforcement** — Every bullet follows Situation → Task → Action → Result
- **Keyword Optimization** — Aligns resume keywords with JD while limiting changes to 20–30% per bullet
- **LaTeX Output** — Produces a clean, compilable `.tex` file ready for `pdflatex`
- **Web Interface** — Beautiful UI with real-time progress tracking

## Project Structure

```
TailorCv/
├── main.py                  # CLI entry point
├── requirements.txt
├── ats_resume_prompt.md     # Resume generation prompt rules
├── ats_score_prompt.md      # ATS scoring prompt rules
├── src/
│   ├── __init__.py
│   ├── state.py             # LangGraph state definition
│   ├── prompts.py           # Prompt templates & LaTeX preamble
│   ├── nodes.py             # Graph node functions
│   └── graph.py             # LangGraph graph builder
├── data/
│   ├── sample_resume.txt    # Example resume
│   └── sample_jd.txt        # Example job description
└── output/                  # Generated files land here
```

## Setup

```bash
cd TailorCv
pip install -r requirements.txt
```

### API Keys

TailorCv supports multiple LLM providers. Set the appropriate API key based on your choice:

**Anthropic Claude** (default):
```bash
export ANTHROPIC_API_KEY="your-anthropic-api-key"
```

**OpenAI GPT**:
```bash
export OPENAI_API_KEY="your-openai-api-key"
```

**Google Gemini**:
```bash
export GOOGLE_API_KEY="your-google-api-key"
```

**Custom Endpoint** (e.g., Azure, F5 proxy, local LLMs):
```bash
export OPENAI_API_KEY="your-api-key"  # Or provide via --api-key flag
```

> 📖 **See [LLM_CONFIGURATION.md](LLM_CONFIGURATION.md) for detailed provider setup, model options, and advanced configuration.**

## Usage

### Basic (uses sample data)

```bash
python main.py
```

### With specific LLM provider

**Anthropic Claude:**
```bash
python main.py --model anthropic:claude-sonnet-4-6
```

**OpenAI GPT:**
```bash
python main.py --model openai:gpt-4o
```

**Google Gemini:**
```bash
python main.py --model google_genai:gemini-2.5-flash
```

**Custom endpoint:**
```bash
python main.py --model your-model-name --base-url https://your-endpoint.com/v1
```
```

### Custom resume and JD

```bash
python main.py --resume path/to/resume.txt --jd path/to/jd.txt
```

### With custom instructions

```bash
python main.py --resume data/sample_resume.txt --jd data/sample_jd.txt \
    --instructions "Emphasize distributed systems and Kafka experience"
```

### Adjust threshold and iterations

```bash
python main.py --threshold 85 --max-iterations 3
```

### Custom output path

```bash
python main.py --output my_resume.tex
```

## Output

- `output/resume.tex` — Compilable LaTeX document

Compile to PDF:

```bash
pdflatex output/resume.tex
```

## How It Works

```
START → parse_inputs → generate_resume → assemble_latex → score_resume
                ↑                                              │
                │                                              ▼
                └──── prepare_feedback ◄──── evaluate_score ───┘
                        (if score < 80)       (if score ≥ 80) → finalize → END
```

1. **Parse Inputs** — Validates resume and JD text, initializes iteration tracking
2. **Generate Resume** — Calls Gemini with the ATS resume prompt (including any feedback from previous iterations)
3. **Assemble LaTeX** — Wraps generated sections in the full LaTeX document template
4. **Score Resume** — Evaluates the generated resume against the JD across 7 ATS dimensions
5. **Evaluate Score** — If score ≥ threshold or max iterations reached → finalize; otherwise → retry with feedback
6. **Prepare Feedback** — Extracts the ATS report as feedback for the next generation pass
