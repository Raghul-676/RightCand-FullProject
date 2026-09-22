import os
import sqlite3
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from verdict_agent import DocumentExtractor, VerdictAgent

app = FastAPI(title="Readiness Verdict Agent Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Get path of documents directory
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
STATIC_DIR = os.path.join(BASE_DIR, "static")

# Create static directory if it doesn't exist
os.makedirs(STATIC_DIR, exist_ok=True)

class AnalyzeTextRequest(BaseModel):
    text: str

class AnalyzeStudentRequest(BaseModel):
    username: str
    interview_history: list[dict]

@app.get("/", response_class=HTMLResponse)
async def serve_dashboard():
    index_file = os.path.join(STATIC_DIR, "index.html")
    if not os.path.exists(index_file):
        raise HTTPException(status_code=404, detail="Frontend HTML file not found.")
    with open(index_file, "r", encoding="utf-8") as f:
        return f.read()

@app.get("/api/samples")
async def list_samples():
    """
    Lists the 6 sample profiles in the documents folder with their filenames and text content
    """
    if not os.path.exists(DOCUMENTS_DIR):
        return []
    
    samples = []
    # Sort files to ensure stable order Alice -> Bob -> Charlie -> Diana -> Ethan -> Fiona
    files = sorted([f for f in os.listdir(DOCUMENTS_DIR) if f.endswith(".md") or f.endswith(".txt")])
    
    for filename in files:
        file_path = os.path.join(DOCUMENTS_DIR, filename)
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
            # Generate a user-friendly name from the filename
            # e.g., student_1_alice_smith.md -> Alice Smith
            name_parts = filename.replace(".md", "").replace(".txt", "").split("_")
            # If names have student_1_ prefix, strip it
            if len(name_parts) > 2 and name_parts[0] == "student":
                name_parts = name_parts[2:]
            elif len(name_parts) > 1 and name_parts[0].isdigit():
                name_parts = name_parts[1:]
            
            display_name = " ".join([p.capitalize() for p in name_parts])
            
            samples.append({
                "filename": filename,
                "display_name": display_name,
                "content": content
            })
        except Exception as e:
            continue
            
    return samples

@app.post("/api/analyze-text")
async def analyze_text(request: AnalyzeTextRequest):
    """
    Extracts metrics from raw text, runs the agent, and returns the verdict and execution details
    """
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="Text content cannot be empty.")
    
    try:
        # Step 1: Extract structured data from document text
        extractor = DocumentExtractor()
        extracted_data = extractor.extract(request.text)
        
        # Step 2: Initialize agent with extracted custom data
        student_name = extracted_data.get("student_name", "Uploaded Student")
        agent = VerdictAgent(student_id=student_name, custom_data=extracted_data)
        
        # Step 3: Run analysis
        verdict = agent.run()
        
        return {
            "success": True,
            "extracted_data": extracted_data,
            "verdict": verdict
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

@app.post("/api/analyze-file")
async def analyze_file(file: UploadFile = File(...)):
    """
    Extracts metrics from an uploaded text/markdown file and evaluates it
    """
    contents = await file.read()
    text = contents.decode("utf-8", errors="ignore")
    
    return await analyze_text(AnalyzeTextRequest(text=text))


@app.post("/api/analyze-student")
async def analyze_student(request: AnalyzeStudentRequest):
    if not request.username.strip():
        raise HTTPException(status_code=400, detail="Username cannot be empty.")
    
    # Locate DB
    db_path = os.path.join(BASE_DIR, "..", "Talent Vellocity", "sces", "backend", "sces.db")
    if not os.path.exists(db_path):
        db_path = os.path.join(BASE_DIR, "sces.db")
        if not os.path.exists(db_path):
            raise HTTPException(status_code=500, detail="Database file not found.")

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # 1. Get user_id from username
        c.execute("SELECT id FROM users WHERE username = ?", (request.username,))
        user_row = c.fetchone()
        if not user_row:
            raise HTTPException(status_code=404, detail=f"Student profile '{request.username}' not found in database.")
        
        user_id = user_row[0]
        
        # 2. Get coding stats
        c.execute(
            """
            SELECT leetcode_solved, leetcode_hard_solved, leetcode_rating, leetcode_contests, 
                   codeforces_rating, codeforces_contests, last_active_at 
            FROM coding_stats 
            WHERE student_id = ?
            """,
            (user_id,)
        )
        stats_row = c.fetchone()
        
        # 3. Get domain scores
        c.execute(
            """
            SELECT domain, domain_score, project_count 
            FROM domain_scores 
            WHERE student_id = ?
            """,
            (user_id,)
        )
        domain_rows = c.fetchall()
        
        conn.close()
        
        # Format custom_data
        coding_stats = {
            "leetcode_solved": stats_row[0] if (stats_row and stats_row[0] is not None) else 0,
            "leetcode_hard_solved": stats_row[1] if (stats_row and stats_row[1] is not None) else 0,
            "leetcode_rating": stats_row[2] if (stats_row and stats_row[2] is not None) else 0,
            "leetcode_contests": stats_row[3] if (stats_row and stats_row[3] is not None) else 0,
            "codeforces_rating": stats_row[4] if (stats_row and stats_row[4] is not None) else 0,
            "codeforces_contests": stats_row[5] if (stats_row and stats_row[5] is not None) else 0,
            "last_active_at": stats_row[6] if (stats_row and stats_row[6] is not None) else None
        }
        
        domain_scores = [
            {
                "domain": row[0],
                "domain_score": row[1] if row[1] is not None else 0,
                "project_count": row[2] if row[2] is not None else 0
            }
            for row in domain_rows
        ]
        
        # Format interview history
        interview_history = []
        for index, item in enumerate(request.interview_history):
            q_type = item.get("question_type") or item.get("type") or "matched_skill"
            if q_type not in ["project", "behavioral", "gap", "matched_skill"]:
                q_type = "matched_skill"
                
            interview_history.append({
                "question_type": q_type,
                "topic": item.get("topic") or item.get("question") or f"Question {index+1}",
                "overall_score": float(item.get("overall_score") or item.get("score") or 0.0),
                "feedback": item.get("feedback") or item.get("comments") or "Completed."
            })
            
        custom_data = {
            "coding_stats": coding_stats,
            "domain_scores": domain_scores,
            "interview_history": interview_history
        }
        
        # Step 4: Run Verdict Agent
        agent = VerdictAgent(student_id=request.username, custom_data=custom_data)
        verdict = agent.run()
        
        return {
            "success": True,
            "extracted_data": custom_data,
            "verdict": verdict
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Student analysis failed: {str(e)}")
