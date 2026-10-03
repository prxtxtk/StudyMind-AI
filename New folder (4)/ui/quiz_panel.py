"""
Quiz Panel — auto-generates multiple-choice quizzes from study materials
"""

import streamlit as st
import re
import datetime


def render_quiz():
    st.markdown("## 🧪 Quiz Generator")

    if not st.session_state.model_configured:
        st.info("🔌 Configure your AI model in the sidebar to use the quiz generator.")
        return

    # ── Quiz Configuration ─────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    with col1:
        topic = st.text_input(
            "Quiz topic",
            placeholder="e.g., 'photosynthesis', 'World War II', 'machine learning'",
            help="Enter a topic from your uploaded documents or any subject"
        )
    with col2:
        num_q = st.slider("Number of questions", 3, 15, 5)
    with col3:
        difficulty = st.select_slider(
            "Difficulty",
            options=["easy", "medium", "hard", "expert"],
            value="medium"
        )

    col1, col2 = st.columns([3, 1])
    with col1:
        generate_btn = st.button("🧪 Generate Quiz", use_container_width=True, type="primary",
                                  disabled=not topic)
    with col2:
        if st.session_state.current_quiz:
            if st.button("🔄 New Quiz", use_container_width=True):
                st.session_state.current_quiz = None
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.quiz_score = None
                st.rerun()

    if generate_btn and topic:
        engine = st.session_state.rag_engine
        with st.spinner(f"Generating {num_q} questions about '{topic}'…"):
            try:
                raw_quiz = engine.generate_quiz(topic, num_q, difficulty)
                st.session_state.current_quiz = _parse_quiz(raw_quiz, topic, difficulty)
                st.session_state.quiz_answers = {}
                st.session_state.quiz_submitted = False
                st.session_state.quiz_score = None
                st.rerun()
            except Exception as e:
                st.error(f"Quiz generation failed: {e}")

    # ── Render Quiz ────────────────────────────────────────────────────────────
    if st.session_state.current_quiz:
        quiz = st.session_state.current_quiz
        st.divider()
        st.markdown(f"""
        <div class="quiz-header">
            <h3>📋 {quiz['topic']}</h3>
            <span class="difficulty-badge {quiz['difficulty']}">{quiz['difficulty'].upper()}</span>
        </div>
        """, unsafe_allow_html=True)

        # Raw text fallback if parsing fails
        if not quiz.get("questions"):
            st.markdown(quiz.get("raw", "No quiz content available."))
        else:
            for i, q in enumerate(quiz["questions"]):
                _render_question(i, q)

            # Submit button
            if not st.session_state.quiz_submitted:
                if st.button("✅ Submit Quiz", use_container_width=True, type="primary"):
                    _grade_quiz(quiz)
            else:
                _render_results(quiz)


# ── Helpers ────────────────────────────────────────────────────────────────────

def _render_question(idx: int, q: dict):
    submitted = st.session_state.quiz_submitted
    correct = q.get("correct", "")
    user_ans = st.session_state.quiz_answers.get(idx, "")

    st.markdown(f"""
    <div class="quiz-question">
        <div class="q-number">Q{idx + 1}</div>
        <div class="q-text">{q['question']}</div>
    </div>
    """, unsafe_allow_html=True)

    if not submitted:
        choice = st.radio(
            f"q_{idx}",
            options=q.get("options", []),
            index=None,
            key=f"quiz_ans_{idx}",
            label_visibility="collapsed",
        )
        if choice:
            st.session_state.quiz_answers[idx] = choice[0]  # store letter
    else:
        # Show results
        for opt in q.get("options", []):
            letter = opt[0]
            is_correct = letter == correct
            is_user = letter == user_ans
            icon = "✅" if is_correct else ("❌" if is_user else "  ")
            style = "correct" if is_correct else ("wrong" if is_user and not is_correct else "")
            st.markdown(f"""
            <div class="quiz-option {style}">
                {icon} {opt}
            </div>
            """, unsafe_allow_html=True)

        if q.get("explanation"):
            st.markdown(f"""
            <div class="quiz-explanation">
                💡 <strong>Explanation:</strong> {q['explanation']}
            </div>
            """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)


def _grade_quiz(quiz: dict):
    score = 0
    total = len(quiz.get("questions", []))
    for i, q in enumerate(quiz.get("questions", [])):
        user = st.session_state.quiz_answers.get(i, "")
        if user.upper() == q.get("correct", "").upper():
            score += 1
    st.session_state.quiz_score = (score, total)
    st.session_state.quiz_submitted = True
    st.rerun()


def _render_results(quiz: dict):
    score, total = st.session_state.quiz_score or (0, 1)
    pct = int(score / total * 100) if total else 0
    grade = "🏆 Excellent!" if pct >= 90 else "👍 Good job!" if pct >= 70 else "📚 Keep studying!" if pct >= 50 else "💪 More practice needed"

    st.markdown(f"""
    <div class="quiz-results">
        <div class="result-score">{score}/{total}</div>
        <div class="result-pct">{pct}%</div>
        <div class="result-grade">{grade}</div>
        <div class="result-bar">
            <div class="result-fill" style="width:{pct}%"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Download quiz results
    result_text = f"# Quiz Results — {quiz['topic']}\nScore: {score}/{total} ({pct}%)\n\n"
    for i, q in enumerate(quiz.get("questions", [])):
        user_ans = st.session_state.quiz_answers.get(i, "?")
        correct = q.get("correct", "?")
        status = "✅" if user_ans.upper() == correct.upper() else "❌"
        result_text += f"{status} Q{i+1}: {q['question']}\n   Your answer: {user_ans} | Correct: {correct}\n\n"

    st.download_button(
        "💾 Save Quiz Results",
        data=result_text,
        file_name=f"quiz_{quiz['topic'][:20]}_{datetime.datetime.now().strftime('%Y%m%d')}.md",
        mime="text/markdown",
    )


def _parse_quiz(raw: str, topic: str, difficulty: str) -> dict:
    """Parse LLM quiz output into structured format."""
    questions = []
    # Split on question boundaries
    q_blocks = re.split(r'\*\*Q\d+:', raw)
    q_blocks = [b for b in q_blocks if b.strip()]

    for block in q_blocks:
        try:
            lines = block.strip().split('\n')
            question_text = lines[0].strip().rstrip('*').strip()
            options = []
            correct = ""
            explanation = ""

            for line in lines[1:]:
                line = line.strip()
                if re.match(r'^[A-D]\)', line):
                    options.append(line)
                elif '✅' in line or 'Correct Answer:' in line:
                    m = re.search(r'([A-D])\)', line)
                    if m:
                        correct = m.group(1)
                elif 'Explanation:' in line or '💡' in line:
                    explanation = re.sub(r'[💡\*]|Explanation:', '', line).strip()

            if question_text and options:
                questions.append({
                    "question": question_text,
                    "options": options,
                    "correct": correct,
                    "explanation": explanation,
                })
        except Exception:
            continue

    return {
        "topic": topic,
        "difficulty": difficulty,
        "questions": questions,
        "raw": raw,  # keep raw as fallback
    }
