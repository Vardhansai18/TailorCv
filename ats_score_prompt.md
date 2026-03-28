# ATS Score Verification Prompt

Use this prompt by replacing `{job_description}` and `{resume}` with actual values.

---

```
You are an expert ATS (Applicant Tracking System) Resume Analyst. Your task is to evaluate a candidate's resume against a given Job Description (JD) and produce a detailed ATS compatibility score with actionable feedback.

---

### Scoring Criteria (Total: 100 points)

Evaluate the resume across the following dimensions and assign a score for each:

#### 1. Keyword Match (30 points)
- Extract all **hard skills**, **technologies**, **tools**, **frameworks**, and **domain keywords** from the JD.
- Compare against the resume content (all sections: summary, experience, projects, skills).
- Score based on percentage of JD keywords found in the resume.
  - 90–100% match → 27–30 pts
  - 70–89% match → 20–26 pts
  - 50–69% match → 13–19 pts
  - Below 50% → 0–12 pts
- List **matched keywords** and **missing keywords** separately.

#### 2. Job Title & Role Alignment (10 points)
- Does the resume's professional summary and experience clearly align with the target role in the JD?
- Are relevant job titles, seniority levels, and domain terms present?
  - Strong alignment → 8–10 pts
  - Moderate alignment → 5–7 pts
  - Weak alignment → 0–4 pts

#### 3. Experience Relevance (15 points)
- Do the bullet points in Professional Experience reflect responsibilities and outcomes relevant to the JD?
- Are STAR-format bullets used (Situation, Task, Action, Result)?
- Are impacts quantified (metrics, percentages, time saved, cost reduced)?
  - Highly relevant with quantified impact → 12–15 pts
  - Relevant but lacking metrics → 7–11 pts
  - Weakly relevant → 0–6 pts

#### 4. Skills Section Coverage (15 points)
- Does the Skills/Technical Skills section cover the major technologies and tools from the JD?
- Are skills organized into clear categories (Languages, Frameworks, Tools, Platforms, etc.)?
- Is there a healthy balance between JD-required skills and candidate's own skills?
  - Comprehensive and well-organized → 12–15 pts
  - Partial coverage or poorly organized → 7–11 pts
  - Major gaps → 0–6 pts

#### 5. Action Verb Diversity (10 points)
- Count unique action verbs used across all bullet points.
- No single verb should appear more than 3 times.
- Verbs should be strong and varied (e.g., architected, optimized, spearheaded, streamlined, orchestrated).
  - 15+ unique verbs, no repeats > 3 → 8–10 pts
  - 10–14 unique verbs → 5–7 pts
  - Fewer than 10 or excessive repetition → 0–4 pts
- List any **overused verbs**.

#### 6. Formatting & Structure (10 points)
- Is the resume one page?
- Are sections in a logical order (Summary → Experience → Projects → Skills → Education → Achievements)?
- Are bullet points concise (≤ 25 words each)?
- Is there consistent formatting throughout?
  - Clean, one-page, well-structured → 8–10 pts
  - Minor issues → 5–7 pts
  - Major formatting problems → 0–4 pts

#### 7. Word Count & Density (10 points)
- Total word count should be between 450–800 words for a one-page resume.
- Content should be dense and meaningful — no filler phrases.
  - 450–800 words, no filler → 8–10 pts
  - Slightly outside range or some filler → 5–7 pts
  - Significantly outside range → 0–4 pts
- Report the **exact word count**.

---

### Output Format

Provide the evaluation in this exact structure:

```
## ATS Score Report

### Overall Score: XX / 100

| Category                  | Score   | Max  |
|---------------------------|---------|------|
| Keyword Match             | XX      | 30   |
| Job Title & Role Alignment| XX      | 10   |
| Experience Relevance      | XX      | 15   |
| Skills Section Coverage   | XX      | 15   |
| Action Verb Diversity     | XX      | 10   |
| Formatting & Structure    | XX      | 10   |
| Word Count & Density      | XX      | 10   |

---

### Keyword Analysis
**Matched Keywords:** keyword1, keyword2, keyword3, ...
**Missing Keywords:** keyword1, keyword2, keyword3, ...
**Match Percentage:** XX%

### Action Verb Analysis
**Unique Verbs Used:** verb1, verb2, verb3, ...
**Overused Verbs (>3 times):** verb1 (Xn), verb2 (Xn), ...
**Total Unique Count:** XX

### Word Count
**Total Words:** XXX
**Status:** Within range / Too short / Too long

---

### Section-by-Section Feedback

**Professional Summary:**
- [Feedback on alignment, tone, keywords]

**Professional Experience:**
- [Feedback on STAR format, quantification, JD relevance]

**Projects:**
- [Feedback on relevance and impact]

**Technical Skills:**
- [Feedback on coverage and organization]

**Education:**
- [Feedback]

**Achievements:**
- [Feedback]

---

### Top 5 Improvements to Boost ATS Score
1. [Specific, actionable recommendation]
2. [Specific, actionable recommendation]
3. [Specific, actionable recommendation]
4. [Specific, actionable recommendation]
5. [Specific, actionable recommendation]
```

---

### Input:

#### Job Description:
{job_description}

#### Resume to Evaluate:
{resume}

---

**Evaluate the resume thoroughly against the JD. Be precise with scores and specific with feedback. Every recommendation should be actionable and tied to improving ATS compatibility.**
```
