import streamlit as st
from utils.parser import extract_pdf_text
from agents.resume_agent import analyze_resume
from agents.jd_agent import analyze_jd
from agents.gap_agent import analyze_gap
from agents.evaluation_agent import evaluate_answer
from agents.report_agent import generate_report
from agents.planner_agent import PlannerAgent
from agents.question_generator_agent import QuestionGeneratorAgent

TOTAL_QUESTIONS = 10

# Badge styling per level
LEVEL_BADGES = {
    "Intern":           "🟢 Intern",
    "Junior Developer": "🔵 Junior Developer",
    "Senior Developer": "🔴 Senior Developer",
}

LEVEL_DESCRIPTIONS = {
    "Intern":           "Projects · Technologies · APIs · Frameworks · Implementation",
    "Junior Developer": "Architecture · Optimization · API Security · Deployment · Error Handling",
    "Senior Developer": "System Design · Scalability · Microservices · Cloud · Performance Engineering",
}

st.set_page_config(page_title="AI Interview Preparation Assistant", page_icon="🎯", layout="wide")
st.title("🎯 AI Interview Preparation Assistant")


def init_session():
    """Initialize all session state variables including candidate level."""
    defaults = {
        "stage":              "upload",   # upload | interview | report
        "candidate_level":    "Junior Developer",
        "resume_data":        None,
        "jd_data":            None,
        "gap_data":           None,
        "current_question":   None,
        "question_count":     0,
        "previous_questions": [],
        "previous_answers":   [],
        "evaluations":        [],
        "last_score":         5.0,
        "report":             None,
        "answer_submitted":   False,
        "current_evaluation": None,
        "interview_plan":     {},
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def render_upload_stage():
    """Render the file upload, level selection, and analysis step."""
    st.subheader("Step 1 — Upload Your Documents & Select Interview Level")

    # ── Candidate Level Selection ────────────────────────────────────────────
    st.markdown("#### 🎯 Select Your Interview Level")
    level_cols = st.columns(3)

    with level_cols[0]:
        with st.container(border=True):
            st.markdown("### 🟢 Intern")
            st.caption("Students · Freshers · Internship Candidates")
            st.markdown(
                "Focus: Projects, Technology choices, APIs, "
                "Frameworks, Implementation details"
            )
            if st.button("Select Intern", use_container_width=True,
                         type="primary" if st.session_state.candidate_level == "Intern" else "secondary"):
                st.session_state.candidate_level = "Intern"
                st.rerun()

    with level_cols[1]:
        with st.container(border=True):
            st.markdown("### 🔵 Junior Developer")
            st.caption("0–2 Years Experience")
            st.markdown(
                "Focus: Architecture, API Security, DB Optimization, "
                "Error Handling, Deployment"
            )
            if st.button("Select Junior Developer", use_container_width=True,
                         type="primary" if st.session_state.candidate_level == "Junior Developer" else "secondary"):
                st.session_state.candidate_level = "Junior Developer"
                st.rerun()

    with level_cols[2]:
        with st.container(border=True):
            st.markdown("### 🔴 Senior Developer")
            st.caption("3+ Years Experience")
            st.markdown(
                "Focus: System Design, Scalability, Microservices, "
                "Cloud, Performance Engineering"
            )
            if st.button("Select Senior Developer", use_container_width=True,
                         type="primary" if st.session_state.candidate_level == "Senior Developer" else "secondary"):
                st.session_state.candidate_level = "Senior Developer"
                st.rerun()

    st.info(
        f"**Selected Level:** {LEVEL_BADGES[st.session_state.candidate_level]}  |  "
        f"{LEVEL_DESCRIPTIONS[st.session_state.candidate_level]}"
    )
    st.divider()

    # ── Document Upload ───────────────────────────────────────────────────────
    st.markdown("#### 📂 Upload Documents")
    col1, col2 = st.columns(2)

    with col1:
        resume_file = st.file_uploader("📄 Upload Resume (PDF)", type=["pdf"], key="resume_upload")

    with col2:
        jd_option = st.radio("Job Description format:", ["Upload PDF", "Paste Text"], horizontal=True)
        if jd_option == "Upload PDF":
            jd_file = st.file_uploader("📋 Upload Job Description (PDF)", type=["pdf"], key="jd_upload")
            jd_text_input = None
        else:
            jd_file = None
            jd_text_input = st.text_area("Paste Job Description text:", height=200)

    if st.button("🚀 Start Interview", type="primary", use_container_width=True):
        if not resume_file:
            st.error("Please upload your resume.")
            return

        has_jd = (jd_option == "Upload PDF" and jd_file) or (jd_option == "Paste Text" and jd_text_input)
        if not has_jd:
            st.error("Please provide the job description.")
            return

        with st.spinner("Analyzing your resume and job description..."):
            try:
                # Parse documents
                resume_text = extract_pdf_text(resume_file)
                if not resume_text:
                    st.error("Could not extract text from resume PDF. Please ensure it is not scanned/image-based.")
                    return

                if jd_file:
                    jd_text = extract_pdf_text(jd_file)
                    if not jd_text:
                        st.error("Could not extract text from JD PDF.")
                        return
                else:
                    jd_text = jd_text_input

                # Run analysis agents
                st.session_state.resume_data = analyze_resume(resume_text)
                st.session_state.jd_data     = analyze_jd(jd_text)
                st.session_state.gap_data    = analyze_gap(
                    st.session_state.resume_data,
                    st.session_state.jd_data,
                )

                # PlannerAgent: build interview plan once after gap analysis
                planner = PlannerAgent(
                    st.session_state.resume_data,
                    st.session_state.jd_data,
                    st.session_state.gap_data,
                    st.session_state.candidate_level,
                )
                st.session_state.interview_plan = planner.run()

                # QuestionGeneratorAgent: generate first question using the plan
                qg_agent = QuestionGeneratorAgent(
                    st.session_state.resume_data,
                    st.session_state.jd_data,
                    st.session_state.gap_data,
                    st.session_state.interview_plan,
                    [],
                    [],
                    5.0,
                    st.session_state.candidate_level,
                    1,
                )
                st.session_state.current_question = qg_agent.run()
                st.session_state.stage = "interview"
                st.rerun()

            except EnvironmentError as e:
                st.error(f"⚠️ Configuration error: {e}")
            except ValueError as e:
                st.error(f"⚠️ Document error: {e}")
            except RuntimeError as e:
                st.error(f"⚠️ AI service error: {e}")


def render_gap_summary():
    """Display a compact gap analysis expander panel."""
    gap = st.session_state.gap_data
    with st.expander("📊 Profile Match Summary", expanded=False):
        st.metric("Match Score", f"{gap.get('match_percentage', 0)}%")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**✅ Matched Skills**")
            for s in gap.get("matched_skills", []):
                st.markdown(f"- {s}")
        with col2:
            st.markdown("**❌ Missing Skills**")
            for s in gap.get("missing_skills", []):
                st.markdown(f"- {s}")


def render_interview_stage():
    """Render the active interview Q&A flow."""
    level  = st.session_state.candidate_level
    q_num  = st.session_state.question_count + 1

    # Header with level badge
    header_col, badge_col = st.columns([3, 1])
    with header_col:
        st.subheader(f"Interview — Question {q_num} of {TOTAL_QUESTIONS}")
    with badge_col:
        st.markdown(f"**Level:** {LEVEL_BADGES[level]}")
        st.caption(LEVEL_DESCRIPTIONS[level])

    st.progress(st.session_state.question_count / TOTAL_QUESTIONS)
    render_gap_summary()
    st.divider()

    # Current question
    st.markdown(f"### 🤖 Question {q_num}")
    st.info(st.session_state.current_question)

    # Show evaluation after answer is submitted
    if st.session_state.answer_submitted and st.session_state.current_evaluation:
        ev = st.session_state.current_evaluation
        st.markdown("#### 📝 Evaluation")
        col1, col2, col3, col4, col5 = st.columns(5)
        col1.metric("Accuracy",      f"{ev['accuracy']}/10")
        col2.metric("Clarity",       f"{ev['clarity']}/10")
        col3.metric("Depth",         f"{ev['depth']}/10")
        col4.metric("Communication", f"{ev['communication']}/10")
        col5.metric("Overall",       f"{ev['overall_score']}/10")
        st.markdown(f"**Feedback:** {ev['feedback']}")
        st.divider()

        if st.session_state.question_count >= TOTAL_QUESTIONS:
            if st.button("📄 Generate Final Report", type="primary", use_container_width=True):
                with st.spinner("Generating your interview report..."):
                    try:
                        st.session_state.report = generate_report(
                            st.session_state.resume_data,
                            st.session_state.jd_data,
                            st.session_state.gap_data,
                            st.session_state.evaluations,
                            level,
                        )
                        st.session_state.stage = "report"
                        st.rerun()
                    except RuntimeError as e:
                        st.error(f"⚠️ Error generating report: {e}")
        else:
            if st.button("➡️ Next Question", type="primary", use_container_width=True):
                with st.spinner("Generating next question..."):
                    try:
                        next_q_num = st.session_state.question_count + 1
                        qg_agent   = QuestionGeneratorAgent(
                            st.session_state.resume_data,
                            st.session_state.jd_data,
                            st.session_state.gap_data,
                            st.session_state.interview_plan,
                            st.session_state.previous_questions,
                            st.session_state.previous_answers,
                            st.session_state.last_score,
                            level,
                            next_q_num,
                        )
                        next_q = qg_agent.run()
                        st.session_state.current_question   = next_q
                        st.session_state.answer_submitted   = False
                        st.session_state.current_evaluation = None
                        st.rerun()
                    except RuntimeError as e:
                        st.error(f"⚠️ Error generating question: {e}")
        return

    # Answer input form
    with st.form("answer_form", clear_on_submit=True):
        answer = st.text_area(
            "Your Answer:",
            height=180,
            placeholder="Type your answer here...",
        )
        submitted = st.form_submit_button("✅ Submit Answer", type="primary", use_container_width=True)

    if submitted:
        if not answer.strip():
            st.warning("Please enter an answer before submitting.")
            return

        with st.spinner("Evaluating your answer..."):
            try:
                evaluation = evaluate_answer(st.session_state.current_question, answer.strip())

                st.session_state.previous_questions.append(st.session_state.current_question)
                st.session_state.previous_answers.append(answer.strip())
                st.session_state.evaluations.append(evaluation)
                st.session_state.last_score         = evaluation.get("overall_score", 5.0)
                st.session_state.question_count    += 1
                st.session_state.answer_submitted   = True
                st.session_state.current_evaluation = evaluation
                st.rerun()

            except RuntimeError as e:
                st.error(f"⚠️ Evaluation error: {e}")


def render_report_stage():
    """Render the final interview report."""
    level = st.session_state.candidate_level

    st.subheader("📄 Final Interview Report")
    st.success("Interview complete! Here is your detailed performance report.")

    # Summary metrics
    evaluations = st.session_state.evaluations
    if evaluations:
        avg_overall = round(
            sum(e.get("overall_score", 0) for e in evaluations) / len(evaluations), 1
        )
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("Interview Level",    LEVEL_BADGES[level])
        col2.metric("Questions Answered", len(evaluations))
        col3.metric("Average Score",      f"{avg_overall}/10")
        col4.metric("Resume Match",       f"{st.session_state.gap_data.get('match_percentage', 0)}%")

    st.divider()
    st.markdown(st.session_state.report)
    st.divider()

    st.download_button(
        label="⬇️ Download Report",
        data=st.session_state.report,
        file_name=f"interview_report_{level.replace(' ', '_').lower()}.txt",
        mime="text/plain",
        use_container_width=True,
    )

    if st.button("🔄 Start New Interview", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()


# ── Main routing ──────────────────────────────────────────────────────────────
init_session()

if st.session_state.stage == "upload":
    render_upload_stage()
elif st.session_state.stage == "interview":
    render_interview_stage()
elif st.session_state.stage == "report":
    render_report_stage()
