import os
import json
import uuid
import re
import random
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
from docx import Document
from io import BytesIO
from fpdf import FPDF
from PIL import Image
import pytesseract

app = Flask(__name__)
app.secret_key = "supersecretkey"

UPLOAD_FOLDER = "uploads"
ATTEMPT_FOLDER = "attempts"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(ATTEMPT_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'png', 'jpg', 'jpeg'}


# ---------- Helper Functions ----------
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def extract_text(file_path):
    ext = file_path.rsplit('.', 1)[1].lower()
    text = ""
    if ext == 'pdf':
        reader = PdfReader(file_path)
        for page in reader.pages:
            text += page.extract_text() + "\n"
    elif ext in ['doc', 'docx']:
        doc = Document(file_path)
        for para in doc.paragraphs:
            text += para.text + "\n"
    elif ext in ['png', 'jpg', 'jpeg']:
        img = Image.open(file_path)
        text = pytesseract.image_to_string(img)
    return text


def generate_questions(text, mcq_count=6, desc_count=3):
    """Generate meaningful, topic-focused, non-repeating questions with varied formats.
    MCQs:
      - Definition-based questions from key concepts
      - Application and scenario-based questions
      - Comparison questions
      - Options: 1 correct + 3 plausible, context-relevant distractors
    Descriptive:
      - Prompts built from top key terms of the lesson
    """
    # Basic preprocessing
    sentences = [s.strip() for s in re.split(r'[.!?]\s+', text) if len(s.strip()) > 25]
    paragraphs = [p.strip() for p in re.split(r'\n\n+', text) if len(p.strip()) > 50]

    # Stopwords for filtering
    stop = set("""
        the a an and or of to in on for with from by is are was were be been being as at that this those these it
        into over under through about between within without against into than then there here their his her its our
        your they them we you i do does did done such suchlike may might can could should would will must not no yes
    """.split())

    # Tokens and frequency
    tokens = re.findall(r'\b[A-Za-z][A-Za-z\-]+\b', text)
    freq = {}
    for w in tokens:
        wl = w.lower()
        if len(wl) <= 3 or wl in stop:
            continue
        freq[wl] = freq.get(wl, 0) + 1

    # Candidate terms
    capitalized = list({w for w in re.findall(r'\b[A-Z][a-zA-Z\-]+\b', text) if len(w) > 3})
    top_terms = [t for t, _ in sorted(freq.items(), key=lambda x: (-x[1], x[0]))][:50]
    key_terms = list(dict.fromkeys(capitalized + top_terms))

    # Definition sentences
    def_sentences = [
        s for s in sentences
        if re.search(r'\b(is|means|refers to|defined as|involves|consists of|includes|enables|focuses on)\b', s, re.IGNORECASE)
    ]

    # Extract subject and definition
    def extract_def(s):
        # More flexible pattern matching
        patterns = [
            r'^(?P<subject>[A-Z][a-zA-Z\s\-]+?)\s+(is|means|refers to|defined as)\s+(?P<def>.+)$',
            r'^(?P<subject>[A-Z][a-zA-Z\s\-]+?)\s+(involves|consists of|includes|enables)\s+(?P<def>.+)$',
            r'^(?P<subject>[A-Z][a-zA-Z\s\-]+?)[,:]\s+(?P<def>.+)$'
        ]
        for pattern in patterns:
            m = re.search(pattern, s)
            if m:
                subject = re.sub(r'^\b(the|a|an)\b\s*', '', m.group('subject')).strip()
                definition = m.group('def').strip()
                if len(subject) > 2 and len(definition) > 20:
                    return subject, definition
        return None, None

    # Distractors: topic-related but contextually different
    def pick_distractors(correct, context_text, k=3):
        # Candidates from other definition subjects
        subject_candidates = []
        for s in def_sentences:
            subj, _ = extract_def(s)
            if subj and subj.lower() != correct.lower() and subj.lower() not in context_text.lower():
                subject_candidates.append(subj)
        
        # Candidates from key terms with reasonable frequency
        pool_candidates = []
        for t in key_terms:
            tl = t.lower()
            if tl != correct.lower() and tl not in context_text.lower() and freq.get(tl, 0) >= 1 and len(t) > 3:
                pool_candidates.append(t)
        
        # Add all key terms as fallback
        all_candidates = []
        for t in key_terms:
            if t.lower() != correct.lower() and t not in subject_candidates and t not in pool_candidates:
                all_candidates.append(t)
        
        # Merge and randomize
        merged = list(dict.fromkeys(subject_candidates + pool_candidates + all_candidates))
        random.shuffle(merged)
        
        # Return k distinct distractors
        result = []
        for item in merged:
            if len(result) >= k:
                break
            # Ensure distractor is meaningfully different
            if item.lower() != correct.lower():
                result.append(item)
        
        return result

    mcqs = []
    used_q = set()
    used_concepts = set()

    # MCQ Type 1: Definition-based questions ("What is X?")
    for s in def_sentences:
        if len(mcqs) >= mcq_count:
            break
        subj, definition = extract_def(s)
        if not subj or not definition or subj.lower() in used_concepts:
            continue
        
        # Truncate long definitions
        if len(definition) > 150:
            definition = definition[:147] + "..."
        
        qtext = f"What is {subj}?"
        if qtext in used_q:
            continue
        
        distractors = pick_distractors(subj, s, k=3)
        
        # Create meaningful distractor definitions
        distractor_defs = []
        for dist in distractors[:3]:
            # Find if distractor has a definition in text
            for sent in def_sentences:
                d_subj, d_def = extract_def(sent)
                if d_subj and d_subj.lower() == dist.lower() and d_def:
                    distractor_defs.append(d_def[:100])
                    break
        
        # If we have good distractors, create option-based question
        if len(distractor_defs) >= 2:
            all_options = [(definition, True)] + [(d, False) for d in distractor_defs[:3]]
            random.shuffle(all_options)
            options = [opt[0] for opt in all_options]
            correct_answer = definition
            
            mcqs.append({
                "question": qtext,
                "options": options,
                "answer": correct_answer,
                "difficulty": "medium"
            })
            used_q.add(qtext)
            used_concepts.add(subj.lower())
        else:
            # Fall back to simple term-based question
            distractors = pick_distractors(subj, s, k=3)
            # Add generic options if needed
            while len(distractors) < 3 and len(key_terms) > 0:
                for t in key_terms:
                    if t.lower() != subj.lower() and t not in distractors:
                        distractors.append(t)
                        if len(distractors) >= 3:
                            break
                break
            
            if len(distractors) >= 3:
                options = [subj] + distractors[:3]
                options = list(dict.fromkeys(options))
                if len(options) >= 4:
                    options = options[:4]
                    random.shuffle(options)
                    qtext = f"Which term best describes: '{definition[:100]}...'?" if len(definition) > 100 else f"Which term refers to: '{definition}'?"
                    mcqs.append({
                        "question": qtext,
                        "options": options,
                        "answer": subj,
                        "difficulty": "medium"
                    })
                    used_q.add(qtext)
                    used_concepts.add(subj.lower())

    # MCQ Type 2: Context and application questions
    if len(mcqs) < mcq_count:
        application_sentences = [s for s in sentences if any(word in s.lower() for word in ['used for', 'application', 'example', 'such as', 'including', 'enables', 'allows'])]
        
        for s in application_sentences:
            if len(mcqs) >= mcq_count:
                break
            
            terms_in_s = [t for t in key_terms if t.lower() in s.lower() and len(t) > 3 and t.lower() not in used_concepts]
            if not terms_in_s:
                continue
            
            correct = max(terms_in_s, key=lambda t: freq.get(t.lower(), 1))
            snippet = s[:120] + ("..." if len(s) > 120 else "")
            
            question_templates = [
                f"According to the text, which concept is related to: '{snippet}'?",
                f"Which of the following is mentioned in context of: '{snippet}'?",
                f"What is discussed in the statement: '{snippet}'?"
            ]
            qtext = random.choice(question_templates)
            
            if qtext in used_q:
                continue
            
            distractors = pick_distractors(correct, s, k=3)
            # Ensure we have enough distractors
            while len(distractors) < 3 and len(key_terms) > 0:
                for t in key_terms:
                    if t.lower() != correct.lower() and t not in distractors:
                        distractors.append(t)
                        if len(distractors) >= 3:
                            break
                break
            
            if len(distractors) >= 3:
                options = [correct] + distractors[:3]
                options = list(dict.fromkeys(options))
                if len(options) >= 4:
                    options = options[:4]
                    random.shuffle(options)
                    mcqs.append({
                        "question": qtext,
                        "options": options,
                        "answer": correct,
                        "difficulty": "easy"
                    })
                    used_q.add(qtext)
                    used_concepts.add(correct.lower())

    # MCQ Type 3: Fill in the blanks from key sentences
    if len(mcqs) < mcq_count:
        for s in sentences:
            if len(mcqs) >= mcq_count:
                break
            
            # Find sentences with key terms
            terms_in_s = [t for t in key_terms[:20] if t.lower() in s.lower() and len(t) > 4 and t.lower() not in used_concepts]
            if not terms_in_s:
                continue
            
            correct = random.choice(terms_in_s)
            
            # Create fill-in-the-blank
            blank_sentence = s.replace(correct, "_____", 1)
            if blank_sentence == s:  # No replacement happened
                continue
            
            qtext = f"Fill in the blank: '{blank_sentence[:150]}{'...' if len(blank_sentence) > 150 else ''}'"
            
            if qtext in used_q:
                continue
            
            distractors = pick_distractors(correct, s, k=3)
            # Ensure we have enough distractors
            while len(distractors) < 3 and len(key_terms) > 0:
                for t in key_terms:
                    if t.lower() != correct.lower() and t not in distractors:
                        distractors.append(t)
                        if len(distractors) >= 3:
                            break
                break
            
            if len(distractors) >= 3:
                options = [correct] + distractors[:3]
                options = list(dict.fromkeys(options))
                if len(options) >= 4:
                    options = options[:4]
                    random.shuffle(options)
                    mcqs.append({
                        "question": qtext,
                        "options": options,
                        "answer": correct,
                        "difficulty": "hard"
                    })
                    used_q.add(qtext)
                    used_concepts.add(correct.lower())

    # Ensure we have the requested count (if possible)
    # Fallback: If we still don't have enough MCQs, create simple ones from any sentences
    if len(mcqs) < mcq_count and len(key_terms) >= 4:
        remaining = mcq_count - len(mcqs)
        fallback_sentences = [s for s in sentences if len(s) > 40 and s not in [q.get('question', '') for q in mcqs]]
        
        for idx, s in enumerate(fallback_sentences):
            if len(mcqs) >= mcq_count:
                break
            
            # Find a term from this sentence that hasn't been used
            available_terms = [t for t in key_terms if t.lower() in s.lower() and len(t) > 4 and t.lower() not in used_concepts]
            if not available_terms:
                continue
            
            correct = available_terms[0]
            
            # Create a simple comprehension question
            snippet = s[:100] + ("..." if len(s) > 100 else "")
            qtext = f"According to the lesson, which term is associated with: '{snippet}'?"
            
            if qtext in used_q:
                continue
            
            # Get 3 random other terms as distractors
            distractors = [t for t in key_terms if t.lower() != correct.lower() and t not in [correct]][:10]
            random.shuffle(distractors)
            distractors = distractors[:3]
            
            if len(distractors) >= 3:
                options = [correct] + distractors
                options = list(dict.fromkeys(options))[:4]
                random.shuffle(options)
                
                mcqs.append({
                    "question": qtext,
                    "options": options,
                    "answer": correct,
                    "difficulty": "easy"
                })
                used_q.add(qtext)
                used_concepts.add(correct.lower())
    
    mcqs = mcqs[:mcq_count]
    
    # FINAL FALLBACK: If still no MCQs, create simple keyword-based MCQs
    if len(mcqs) == 0 and len(key_terms) >= 8:
        print("WARNING: Using final fallback MCQ generation")
        simple_questions = [
            "What is one of the key concepts discussed in the lesson?",
            "Which term is relevant to the main topic?",
            "According to the text, which concept is important?",
            "What topic is covered in this lesson?",
            "Which of the following is mentioned in the text?"
        ]
        
        for i in range(min(mcq_count, len(simple_questions))):
            if len(mcqs) >= mcq_count:
                break
            
            # Pick 4 random key terms
            if len(key_terms) >= 4:
                options = random.sample(key_terms[:20], min(4, len(key_terms[:20])))
                correct = options[0]
                random.shuffle(options)
                
                mcqs.append({
                    "question": simple_questions[i],
                    "options": options,
                    "answer": correct,
                    "difficulty": "easy"
                })

    # Descriptive prompts from key terms
    def pick_terms(n):
        terms = [t for t in key_terms if t[0].isalpha() and len(t) > 3][:max(n, 1)]
        return terms if terms else ["topic"]

    descriptive = []
    used_desc = set()
    pool = key_terms[:15] if len(key_terms) >= 15 else key_terms
    
    # Question templates for variety
    question_templates = [
        (lambda t: f"Explain {t} in detail with examples from the text.", "medium"),
        (lambda t: f"Describe the significance of {t} and its applications.", "medium"),
        (lambda t: f"How does {t} contribute to the main topic? Provide a detailed explanation.", "hard"),
        (lambda t: f"Discuss the key aspects of {t} mentioned in the lesson.", "easy"),
        (lambda t: f"What role does {t} play according to the text? Explain thoroughly.", "medium"),
    ]
    
    for i in range(desc_count):
        if len(descriptive) >= desc_count:
            break
        
        # Every third question: comparison question
        if i % 3 == 2 and len(pool) >= 2:
            a, b = pool[i % len(pool)], pool[(i + 1) % len(pool)]
            q = f"Compare and contrast {a} and {b}. Explain their relationship and differences based on the text."
            kws = list(dict.fromkeys(([a, b] + pick_terms(5))))
            diff = "hard"
        else:
            # Select a unique term from the pool
            term_index = i % len(pool) if pool else 0
            t = pool[term_index] if pool else "the main topic"
            
            # Use different question templates
            template_func, diff = question_templates[i % len(question_templates)]
            q = template_func(t)
            kws = list(dict.fromkeys(([t] + pick_terms(5))))
        
        if q in used_desc:
            # Try alternate phrasing if duplicate
            q = f"Provide a comprehensive explanation of {pool[i % len(pool)] if pool else 'the main concept'} with supporting details from the text."
            if q in used_desc:
                continue
        
        used_desc.add(q)
        descriptive.append({
            "question": q,
            "keywords": kws,
            "difficulty": diff
        })

    descriptive = descriptive[:desc_count]
    return mcqs, descriptive


def calculate_score(mcq_answers, descriptive_answers, mcqs, descriptives):
    """Calculate score with detailed breakdown"""
    mcq_score = 0
    mcq_correct = 0
    desc_score = 0
    
    # MCQ scoring - 2 points each
    for i, ans in enumerate(mcq_answers):
        if ans and ans == mcqs[i]['answer']:
            mcq_score += 2
            mcq_correct += 1
    
    # Descriptive scoring - keyword matching with partial credit
    for i, ans in enumerate(descriptive_answers):
        if ans:
            keywords = descriptives[i].get('keywords', [])
            if keywords:
                match_count = sum(1 for kw in keywords if kw.lower() in ans.lower())
                # Give more points for hard questions
                difficulty_multiplier = 1.5 if descriptives[i].get('difficulty') == 'hard' else 1.2 if descriptives[i].get('difficulty') == 'medium' else 1.0
                points = (match_count / len(keywords)) * 3 * difficulty_multiplier
                desc_score += points
    
    total_score = mcq_score + desc_score
    max_score = len(mcqs) * 2 + len(descriptives) * 3
    percentage = round((total_score / max_score) * 100, 2) if max_score > 0 else 0
    
    return {
        'total_score': round(total_score, 2),
        'max_score': max_score,
        'percentage': percentage,
        'mcq_score': mcq_score,
        'mcq_correct': mcq_correct,
        'desc_score': round(desc_score, 2)
    }


def generate_pdf(student_name, mcqs, mcq_answers, descriptives, desc_answers, score_data, timestamp):
    """Generate beautiful PDF report with detailed results"""
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 20)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 15, "Smart Learning App - Exam Report", ln=True, align='C')
    pdf.ln(5)
    
    # Student Info
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 0, 0)
    pdf.cell(0, 10, f"Student: {student_name}", ln=True)
    pdf.cell(0, 10, f"Date: {timestamp}", ln=True)
    pdf.ln(5)
    
    # Score Summary
    pdf.set_fill_color(230, 247, 255)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "Score Summary", ln=True, fill=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"Total Score: {score_data['total_score']}/{score_data['max_score']} ({score_data['percentage']}%)", ln=True)
    pdf.cell(0, 8, f"MCQ Score: {score_data['mcq_score']} ({score_data['mcq_correct']} correct)", ln=True)
    pdf.cell(0, 8, f"Descriptive Score: {score_data['desc_score']}", ln=True)
    pdf.ln(10)
    
    # MCQs Section
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Multiple Choice Questions", ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", '', 10)
    
    for i, q in enumerate(mcqs):
        is_correct = mcq_answers[i] == q['answer']
        
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 6, f"Q{i+1}. {q['question']} [Difficulty: {q.get('difficulty', 'medium')}]")
        pdf.set_font("Arial", '', 10)
        
        for option in q['options']:
            prefix = "[*] " if option == q['answer'] else "[ ] "
            pdf.multi_cell(0, 5, f"  {prefix}{option}")
        
        pdf.set_font("Arial", 'I', 10)
        if is_correct:
            pdf.set_text_color(0, 150, 0)
            pdf.multi_cell(0, 5, f"Your answer: {mcq_answers[i]} - CORRECT!")
        else:
            pdf.set_text_color(255, 0, 0)
            pdf.multi_cell(0, 5, f"Your answer: {mcq_answers[i] or 'Not answered'} - Correct answer: {q['answer']}")
        pdf.set_text_color(0, 0, 0)
        pdf.ln(3)
    
    # Descriptive Section
    pdf.add_page()
    pdf.set_font("Arial", 'B', 14)
    pdf.set_text_color(0, 102, 204)
    pdf.cell(0, 10, "Descriptive Questions", ln=True)
    pdf.set_text_color(0, 0, 0)
    
    for i, q in enumerate(descriptives):
        pdf.set_font("Arial", 'B', 11)
        pdf.multi_cell(0, 6, f"Q{i+1}. {q['question']} [Difficulty: {q.get('difficulty', 'medium')}]")
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, f"Your Answer: {desc_answers[i] or 'Not answered'}")
        pdf.set_font("Arial", 'I', 9)
        pdf.multi_cell(0, 5, f"Keywords to include: {', '.join(q.get('keywords', []))}")
        pdf.ln(5)
    
    pdf_output = BytesIO()
    pdf_string = pdf.output(dest='S').encode('latin-1')
    pdf_output.write(pdf_string)
    pdf_output.seek(0)
    return pdf_output


# ---------- Routes ----------
@app.route("/", methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        student_name = request.form.get("student_name")
        mcq_count = int(request.form.get("mcq_count", 6))
        desc_count = int(request.form.get("desc_count", 3))
        lesson_text = request.form.get("lesson_text", "").strip()
        file = request.files.get("lesson_file")
        text = ""

        # Try to get text from file first
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(UPLOAD_FOLDER, filename)
            file.save(filepath)
            try:
                text = extract_text(filepath)
            except Exception as e:
                return f"Error extracting text from file: {str(e)}", 400
        
        # If no text from file, use the pasted text
        if not text.strip() and lesson_text:
            text = lesson_text

        if not text.strip():
            return "No lesson content found! Please provide text or upload a file.", 400

        mcqs, descriptives = generate_questions(text, mcq_count, desc_count)
        
        # Debug: Log what was generated
        print(f"DEBUG: Generated {len(mcqs)} MCQs and {len(descriptives)} descriptive questions")
        if len(mcqs) == 0:
            print(f"WARNING: No MCQs generated for text length: {len(text)} characters")
            print(f"First 200 chars: {text[:200]}")
        
        # Save questions in session (mock session using JSON)
        session_id = str(uuid.uuid4())
        session_file = os.path.join(UPLOAD_FOLDER, f"{session_id}.json")
        with open(session_file, 'w') as f:
            json.dump({
                "student_name": student_name,
                "mcqs": mcqs,
                "descriptives": descriptives
            }, f)
        return redirect(url_for('exam', session_id=session_id))
    return render_template("index.html")


@app.route("/exam/<session_id>", methods=['GET', 'POST'])
def exam(session_id):
    session_file = os.path.join(UPLOAD_FOLDER, f"{session_id}.json")
    if not os.path.exists(session_file):
        return "Session not found!", 404
    with open(session_file) as f:
        session_data = json.load(f)

    mcqs = session_data['mcqs']
    descriptives = session_data['descriptives']
    student_name = session_data['student_name']

    if request.method == 'POST':
        mcq_answers = [request.form.get(f"mcq_{i}", "") for i in range(len(mcqs))]
        desc_answers = [request.form.get(f"desc_{i}", "") for i in range(len(descriptives))]
        score_data = calculate_score(mcq_answers, desc_answers, mcqs, descriptives)

        attempt_id = str(uuid.uuid4())
        attempt_file = os.path.join(ATTEMPT_FOLDER, f"{attempt_id}.json")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        with open(attempt_file, 'w') as f:
            json.dump({
                "student_name": student_name,
                "timestamp": timestamp,
                "mcqs": mcqs,
                "mcq_answers": mcq_answers,
                "descriptives": descriptives,
                "desc_answers": desc_answers,
                "score_data": score_data
            }, f, indent=2)

        return redirect(url_for("result", attempt_id=attempt_id))

    return render_template("exam.html", 
                         mcqs=mcqs, 
                         descriptives=descriptives, 
                         student_name=student_name, 
                         session_id=session_id,
                         total_questions=len(mcqs) + len(descriptives))


@app.route("/result/<attempt_id>")
def result(attempt_id):
    attempt_file = os.path.join(ATTEMPT_FOLDER, f"{attempt_id}.json")
    if not os.path.exists(attempt_file):
        return "Attempt not found!", 404
    with open(attempt_file) as f:
        attempt_data = json.load(f)
    return render_template("result.html", attempt=attempt_data, attempt_id=attempt_id)


@app.route("/download_pdf/<attempt_id>")
def download_pdf(attempt_id):
    attempt_file = os.path.join(ATTEMPT_FOLDER, f"{attempt_id}.json")
    if not os.path.exists(attempt_file):
        return "Attempt not found!", 404
    with open(attempt_file) as f:
        attempt_data = json.load(f)

    pdf_file = generate_pdf(
        attempt_data["student_name"],
        attempt_data["mcqs"],
        attempt_data["mcq_answers"],
        attempt_data["descriptives"],
        attempt_data["desc_answers"],
        attempt_data["score_data"],
        attempt_data["timestamp"]
    )
    return send_file(pdf_file, download_name=f"{attempt_data['student_name']}_result.pdf", as_attachment=True)


@app.route("/results")
def results_list():
    """View all attempts"""
    attempts = []
    for filename in os.listdir(ATTEMPT_FOLDER):
        if filename.endswith('.json'):
            with open(os.path.join(ATTEMPT_FOLDER, filename)) as f:
                data = json.load(f)
                attempts.append({
                    'id': filename.replace('.json', ''),
                    'student_name': data.get('student_name', 'Unknown'),
                    'timestamp': data.get('timestamp', 'N/A'),
                    'score_data': data.get('score_data', {})
                })
    # Sort by timestamp descending
    attempts.sort(key=lambda x: x['timestamp'], reverse=True)
    return render_template("results_list.html", attempts=attempts)


if __name__ == "__main__":
    app.run(debug=True)
