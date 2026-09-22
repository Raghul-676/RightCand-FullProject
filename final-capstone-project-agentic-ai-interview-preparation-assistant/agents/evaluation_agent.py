import json
from utils.llm import generate_json_response


def evaluate_answer(question: str, answer: str) -> dict:
    """
    Evaluate a candidate's answer to an interview question.
    Returns scores (0-10) for accuracy, clarity, depth, communication, and overall,
    plus a feedback string.
    """
    prompt = f"""You are an expert technical interviewer. Evaluate the candidate's answer to the interview question below.

Question: {question}

Candidate's Answer: {answer}

Evaluate on these criteria (score each from 0 to 10):
- accuracy: Technical correctness of the answer
- clarity: How clearly the answer is communicated
- depth: Level of detail and depth of understanding shown
- communication: Overall communication quality and structure

Also provide brief, constructive feedback (2-3 sentences).

Return ONLY valid JSON with this exact structure (no markdown, no extra text):
{{
  "accuracy": 0,
  "clarity": 0,
  "depth": 0,
  "communication": 0,
  "overall_score": 0,
  "feedback": "Your feedback here"
}}

Calculate overall_score as the average of the four scores, rounded to 1 decimal place."""

    response = generate_json_response(prompt)

    cleaned = response.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.split("```")[1]
        if cleaned.startswith("json"):
            cleaned = cleaned[4:]
        cleaned = cleaned.strip()

    try:
        result = json.loads(cleaned)
        # Ensure overall_score is computed correctly if LLM miscalculates
        scores = [result.get("accuracy", 0), result.get("clarity", 0),
                  result.get("depth", 0), result.get("communication", 0)]
        result["overall_score"] = round(sum(scores) / len(scores), 1)
        return result
    except json.JSONDecodeError:
        return {
            "accuracy": 5,
            "clarity": 5,
            "depth": 5,
            "communication": 5,
            "overall_score": 5.0,
            "feedback": "Could not parse evaluation. Default scores assigned.",
        }
