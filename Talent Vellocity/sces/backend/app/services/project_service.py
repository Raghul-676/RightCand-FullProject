import sys
import os
import json
from dotenv import load_dotenv

# Define paths relative to the current file
WORKSPACE_ROOT = os.path.abspath(
    os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..')
)
AGENT_BACKEND_PATH = os.path.join(WORKSPACE_ROOT, "github-analyzer-agent", "backend")

# Insert agent backend to sys.path so we can import modules directly
if AGENT_BACKEND_PATH not in sys.path:
    sys.path.insert(0, AGENT_BACKEND_PATH)

# Load environment variables from both workspace root and agent backend to ensure keys are loaded
root_env = os.path.join(WORKSPACE_ROOT, ".env")
if os.path.exists(root_env):
    load_dotenv(root_env)

agent_env = os.path.join(AGENT_BACKEND_PATH, ".env")
if os.path.exists(agent_env):
    load_dotenv(agent_env)

from github_client import parse_repo_url, get_repo_meta, get_languages, get_tree
from extractors import build_tech_stack, compute_complexity
from evidence import select_evidence_files
from llm_agent import synthesize
from validator import validate_report




def analyse_repo(repo_url: str) -> dict:
    # Step 1: Parse repo URL into owner/repo
    owner, repo = parse_repo_url(repo_url)

    # Step 2: Fetch metadata, languages, and repo tree (deterministic REST calls)
    meta_raw = get_repo_meta(owner, repo)
    branch = meta_raw.get("default_branch", "main")
    languages = get_languages(owner, repo)
    tree = get_tree(owner, repo, branch)

    # Step 3: Extract tech stack and compute complexity tier (deterministic)
    tech_stack = build_tech_stack(owner, repo, branch, tree, languages)
    complexity = compute_complexity(tree, tech_stack, meta_raw)

    # Step 4: Retrieve evidence files (agentic sampling)
    evidence = select_evidence_files(owner, repo, branch, tree, tech_stack.manifests_found)

    # Step 5: Synthesize grounded domain & summary claims via LLM agent
    domain_claim, summary_claim, frameworks = synthesize(tech_stack, complexity, evidence)
    tech_stack.frameworks_detected = frameworks

    # Validate report claims against retrieved evidence bundle
    validate_report(domain_claim, summary_claim, evidence)

    # Map the complexity tier to Talent Vellocity expected categories: Beginner, Intermediate, Advanced
    COMPLEXITY_MAP = {
        "simple": "Beginner",
        "moderate": "Intermediate",
        "complex": "Advanced",
        "advanced": "Advanced"
    }
    mapped_complexity = COMPLEXITY_MAP.get(complexity.tier, "Beginner")

    # Combine summary and domain classification for unified summary output
    summary_text = summary_claim.text
    if getattr(domain_claim, "categories", None):
        summary_text += f"\n\nDomain Categories: {', '.join(domain_claim.categories)}"
    if domain_claim.text:
        summary_text += f"\n\nDomain Details: {domain_claim.text}"

    return {
        "project_name": meta_raw.get("name", repo),
        "complexity": mapped_complexity,
        "stack_breakdown": json.dumps(tech_stack.languages),
        "summary": summary_text,
        "categories": getattr(domain_claim, "categories", []),
        "complexity_score": complexity.score,
    }

