# Exam Integrity Checker

A Flask-based web application that transforms study materials into interactive, integrity-verified exams. Upload a document (PDF, Word, or image) or paste text — the system automatically generates MCQs and descriptive questions, administers a timed exam, scores the submission, and produces a downloadable PDF report.

---

## Problem Statement

Educators and self-learners often struggle to quickly verify whether a student has genuinely understood study material, rather than simply memorising it. Manually writing varied exam questions for every lesson is time-consuming. **Exam Integrity Checker** automates this process: given any lesson content, it generates contextually relevant questions with plausible distractors, administers a timed exam, and provides transparent scoring that shows which keywords were matched — ensuring the evaluation reflects real comprehension.

---

## Features

| Category | Detail |
|---|---|
| **Multi-format Input** | Paste raw text, upload PDF, Word (DOCX/DOC), or image (PNG/JPG/JPEG with OCR) |
| **Question Generation** | Automatic MCQs (definition-based, application, fill-in-the-blank) + descriptive prompts |
| **Difficulty Levels** | Easy / Medium / Hard assigned per question based on extraction type |
| **Timed Exam** | 30-minute countdown with visual colour warnings (yellow at 5 min, red at 1 min) and auto-submit |
| **Progress Tracking** | Real-time progress bar, unanswered question count, scroll-to-next helper |
| **Text-to-Speech** | Browser SpeechSynthesis reads all questions and options aloud |
| **Auto-Save** | Answers saved to `localStorage` every 30 seconds; restored on accidental reload |
| **Scoring Engine** | MCQ: 2 pts each (exact match); Descriptive: keyword-matching with difficulty multipliers |
| **PDF Report** | Downloadable FPDF report with score summary, per-question breakdown, correct/incorrect highlighting |
| **Attempt History** | All attempts persisted as JSON; statistics dashboard shows total attempts, average score, excellent count |
| **Keyboard Shortcuts** | `Ctrl+S` save progress, `Ctrl+Enter` submit exam |

---

## Technologies Used

| Layer | Library / Technology |
|---|---|
| Web framework | [Flask 3.0](https://flask.palletsprojects.com/) |
| PDF extraction | [PyPDF2 3.0](https://pypdf2.readthedocs.io/) |
| Word document parsing | [python-docx 1.1](https://python-docx.readthedocs.io/) |
| Image OCR | [Pillow 10.1](https://pillow.readthedocs.io/) + [pytesseract 0.3](https://github.com/madmaze/pytesseract) |
| PDF generation | [fpdf 1.7](http://www.fpdf.org/) |
| Frontend | HTML5, CSS3 (custom), Vanilla JavaScript (no frameworks) |
| Storage | JSON files (no database required) |
| Runtime | Python 3.8+ |

---

## Project Structure

```
Exam Integrity Checker/
├── app.py                      # Flask application — all routes and business logic
├── requirements.txt            # Python dependencies
├── README.md                   # This file
├── .gitignore                  # Files excluded from version control
│
├── templates/                  # Jinja2 HTML templates
│   ├── index.html              # Landing page: upload form and input options
│   ├── exam.html               # Timed exam page with MCQs and descriptive questions
│   ├── result.html             # Individual result with score circle and per-question review
│   └── results_list.html       # Attempt history with statistics dashboard
│
├── static/                     # Frontend assets
│   ├── style.css               # Full application styling
│   └── main.js                 # Timer, TTS, auto-save, keyboard shortcuts
│
├── data/
│   └── sample/
│       └── sample_lesson.txt   # Sample AI lesson for testing
│
├── tests/
│   ├── test_questions.py       # Tests MCQ generation with various question counts
│   └── test_short.py           # Tests fallback generation on short input text
│
├── uploads/                    # Session JSON files (auto-created, git-ignored)
└── attempts/                   # Exam result JSON files (auto-created, git-ignored)
```

---

## Installation

### Prerequisites

- Python 3.8 or higher
- pip
- *(Optional)* [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) — required only if you want to upload image files (PNG/JPG)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/<your-username>/exam-integrity-checker.git
cd exam-integrity-checker

# 2. Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS / Linux
source venv/bin/activate

# 3. Install dependencies
pip install -r requirements.txt
```

#### Tesseract (optional — for image OCR)

| Platform | Command |
|---|---|
| Windows | Download installer from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki) and add to `PATH` |
| macOS | `brew install tesseract` |
| Linux | `sudo apt-get install tesseract-ocr` |

If Tesseract is not installed, PDF and text/Word upload still work fine; only image uploads will fail.

---

## Running the Application

```bash
python app.py
```

Then open your browser at **[http://127.0.0.1:5000/](http://127.0.0.1:5000/)**.

---

## How to Use

### Step 1 — Provide Lesson Content

1. Enter your name.
2. Select number of MCQ and descriptive questions.
3. Choose **Paste Text** (paste lesson text directly) or **Upload File** (PDF, DOCX, or image).
4. Click **Generate Integrity Check Exam**.

### Step 2 — Take the Exam

- A 30-minute timer starts automatically.
- Answer all MCQs (radio buttons) and descriptive questions (text areas).
- Use **Highlight Unanswered**, **Next Question**, and **Read Aloud** helper buttons.
- Click **Submit Exam** (or wait for the timer to auto-submit).

### Step 3 — View and Download Results

- Your score percentage is shown in an animated circle graphic.
- Detailed MCQ breakdown shows correct/incorrect per question.
- Descriptive answers show which keywords were found vs. missing.
- Click **Download PDF Report** to get a formatted report.

---

## Example Input

Paste the contents of `data/sample/sample_lesson.txt` (Introduction to Artificial Intelligence) into the text area, enter your name, and click **Generate**.

**Expected output (6 MCQs, 3 Descriptive):**
- 6 multiple-choice questions drawn from AI definitions and applications
- 3 descriptive prompts (e.g. "Explain Machine Learning in detail with examples from the text.")
- After answering and submitting: a percentage score, per-question feedback, and a downloadable PDF report

---

## Running Tests

The tests run the question generation engine directly (no browser needed):

```bash
# From the project root:
python tests/test_questions.py
python tests/test_short.py
```

**`test_questions.py`** — generates 3, 6, and 10 MCQs from a sample AI text and prints the first question, options, answer, and difficulty for each batch.

**`test_short.py`** — verifies the fallback question generation path using a very short input text.

---

## Scoring Method

| Question type | Points | Grading method |
|---|---|---|
| MCQ | 2 pts | Exact match against stored correct answer |
| Descriptive | Up to 3 pts × difficulty multiplier | Keyword presence in student answer (easy ×1.0, medium ×1.2, hard ×1.5) |

**Performance bands:**
- 🏆 Excellent: ≥ 80%
- 👍 Good: 60–79%
- 💪 Keep Studying: < 60%

---

## Limitations

- **Question quality depends on input length and structure.** Very short or unstructured text (< 5 sentences) may yield generic or fallback questions.
- **Descriptive scoring is keyword-based**, not semantic — a technically correct answer using different wording may score lower than expected.
- **OCR accuracy** depends on the Tesseract installation and image quality; scanned or low-resolution images may yield poor text extraction.
- **No user authentication** — all attempts are stored locally in the `attempts/` folder without access control.
- **Single-server deployment** — uses Flask's development server; for production use, deploy behind Gunicorn/uWSGI + nginx.
- **Timer is browser-side** — refreshing the page resets the timer (saved answers will be restored from `localStorage`, but the timer restarts).

---

## Configuration

| Setting | Location | Default |
|---|---|---|
| Exam timer duration | `templates/exam.html` → `startTimer(30, ...)` | 30 minutes |
| Upload folder | `app.py` → `UPLOAD_FOLDER` | `uploads/` |
| Attempts folder | `app.py` → `ATTEMPT_FOLDER` | `attempts/` |
| MCQ points | `app.py` → `calculate_score()` | 2 per question |
| Descriptive points | `app.py` → `calculate_score()` | 3 per question |

---

## Files Safe for GitHub Upload

The following files/folders should be committed:

```
app.py
requirements.txt
README.md
.gitignore
templates/
static/
data/
tests/
```

The following are **excluded by `.gitignore`** and should NOT be committed:

```
venv/          # Virtual environment
uploads/       # Session data (may contain personal documents)
attempts/      # Student exam results (personal data)
__pycache__/
*.pyc
.env
e/             # Old development subdirectory
```

---

## License

Open source — available for educational and personal use.
