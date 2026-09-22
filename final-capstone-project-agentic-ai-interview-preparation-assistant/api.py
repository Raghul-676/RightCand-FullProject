from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import io

from utils.parser import extract_pdf_text
from agents.resume_agent import analyze_resume
from agents.jd_agent import analyze_jd
from agents.gap_agent import analyze_gap
from agents.evaluation_agent import evaluate_answer
from agents.report_agent import generate_report
from agents.planner_agent import PlannerAgent
from agents.question_generator_agent import QuestionGeneratorAgent

app = FastAPI(title="AI Interview Preparation API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)



# ── Request / Response Models ─────────────────────────────────────────────────

class GenerateQuestionRequest(BaseModel):
    resume_data:        dict
    jd_data:            dict
    gap_data:           dict
    interview_plan:     dict
    previous_questions: list[str]
    previous_answers:   list[str]
    last_score:         float
    candidate_level:    str
    question_number:    int


class EvaluateRequest(BaseModel):
    question: str
    answer:   str


class ReportRequest(BaseModel):
    resume_data:     dict
    jd_data:         dict
    gap_data:        dict
    evaluations:     list[dict]
    candidate_level: str


# ── Endpoints ─────────────────────────────────────────────────────────────────

@app.post("/analyze")
async def analyze(
    candidate_level: str       = Form(...),
    resume_file:     UploadFile = File(...),
    jd_file:         Optional[UploadFile] = File(None),
    jd_text:         Optional[str]        = Form(None),
):
    """
    Parse resume + JD, run gap analysis, build interview plan, generate Q1.
    Returns: resume_data, jd_data, gap_data, interview_plan, first_question
    """
    try:
        # Parse resume
        resume_bytes = await resume_file.read()
        resume_text  = extract_pdf_text(io.BytesIO(resume_bytes))
        if not resume_text:
            raise HTTPException(status_code=400, detail="Could not extract text from resume PDF.")

        # Parse JD
        if jd_file:
            jd_bytes = await jd_file.read()
            jd_text  = extract_pdf_text(io.BytesIO(jd_bytes))
            if not jd_text:
                raise HTTPException(status_code=400, detail="Could not extract text from JD PDF.")
        elif jd_text:
            jd_text = jd_text
        else:
            raise HTTPException(status_code=400, detail="Job description is required.")

        # Run agents
        resume_data = analyze_resume(resume_text)
        jd_data     = analyze_jd(jd_text)
        gap_data    = analyze_gap(resume_data, jd_data)

        # PlannerAgent
        planner        = PlannerAgent(resume_data, jd_data, gap_data, candidate_level)
        interview_plan = planner.run()

        # QuestionGeneratorAgent — Q1
        qg = QuestionGeneratorAgent(
            resume_data, jd_data, gap_data,
            interview_plan, [], [], 5.0, candidate_level, 1,
        )
        first_question = qg.run()

        return {
            "resume_data":     resume_data,
            "jd_data":         jd_data,
            "gap_data":        gap_data,
            "interview_plan":  interview_plan,
            "first_question":  first_question,
        }

    except HTTPException:
        raise
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Document error: {e}")
    except RuntimeError as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=502, detail=f"AI service error: {str(e)}")


@app.post("/generate-question")
def generate_question_endpoint(req: GenerateQuestionRequest):
    """
    Generate the next interview question using QuestionGeneratorAgent.
    """
    try:
        qg = QuestionGeneratorAgent(
            req.resume_data,
            req.jd_data,
            req.gap_data,
            req.interview_plan,
            req.previous_questions,
            req.previous_answers,
            req.last_score,
            req.candidate_level,
            req.question_number,
        )
        question = qg.run()
        return {"question": question}

    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")


@app.post("/evaluate")
def evaluate_endpoint(req: EvaluateRequest):
    """
    Evaluate a candidate's answer. Returns accuracy, clarity, depth,
    communication, overall_score, and feedback.
    """
    try:
        result = evaluate_answer(req.question, req.answer)
        return result
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")


@app.post("/report")
def report_endpoint(req: ReportRequest):
    """
    Generate the final interview report.
    """
    try:
        report = generate_report(
            req.resume_data,
            req.jd_data,
            req.gap_data,
            req.evaluations,
            req.candidate_level,
        )
        return {"report": report}
    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=f"Configuration error: {e}")
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=f"AI service error: {e}")
