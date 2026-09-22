from __future__ import annotations
import os
from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from github_client import parse_repo_url, get_repo_meta, get_languages, get_tree, GitHubClientError
from extractors import build_tech_stack, compute_complexity
from evidence import select_evidence_files
from llm_agent import synthesize
from validator import validate_report
from models import AnalysisReport, RepoMeta

app = FastAPI(title="GitHub Repo Analyzer Agent")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    repo_url: str


@app.get("/api/health")
def health():
    return {"status": "ok"}


@app.post("/api/analyze", response_model=AnalysisReport)
def analyze(req: AnalyzeRequest):
    try:
        owner, repo = parse_repo_url(req.repo_url)

        # Step 1: fetch metadata & tree (deterministic)
        meta_raw = get_repo_meta(owner, repo)
        branch = meta_raw.get("default_branch", "main")
        languages = get_languages(owner, repo)
        tree = get_tree(owner, repo, branch)

        meta = RepoMeta(
            full_name=meta_raw.get("full_name", f"{owner}/{repo}"),
            description=meta_raw.get("description"),
            stars=meta_raw.get("stargazers_count", 0),
            forks=meta_raw.get("forks_count", 0),
            default_branch=branch,
            size_kb=meta_raw.get("size", 0),
            created_at=meta_raw.get("created_at"),
            pushed_at=meta_raw.get("pushed_at"),
        )

        # Step 2: deterministic extraction (tech stack + complexity rubric)
        tech_stack = build_tech_stack(owner, repo, branch, tree, languages)
        complexity = compute_complexity(tree, tech_stack, meta_raw)

        # Step 3: evidence retrieval (agentic decision: what to show the LLM)
        evidence = select_evidence_files(owner, repo, branch, tree, tech_stack.manifests_found)

        # Step 4: grounded LLM synthesis
        domain_claim, summary_claim, frameworks = synthesize(tech_stack, complexity, evidence)
        tech_stack.frameworks_detected = frameworks

        # Step 5: validation pass
        notes, low_confidence = validate_report(domain_claim, summary_claim, evidence)

        return AnalysisReport(
            repo_url=req.repo_url,
            meta=meta,
            tech_stack=tech_stack,
            complexity=complexity,
            domain_claim=domain_claim,
            summary_claim=summary_claim,
            evidence_used=evidence,
            validation_notes=notes,
            low_confidence=low_confidence,
        )

    except GitHubClientError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=500, detail=str(e))
