"""
Interview Engine — uses LangChain + OpenAI (langchain_openai)
Handles: question generation, answer evaluation, report generation
"""
import json
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage


SYSTEM_INTERVIEWER = """You are an expert technical interviewer at a top tech company.
Your job is to conduct a realistic, adaptive mock interview.

Rules:
- Ask ONE clear question at a time
- Adapt difficulty based on previous answers
- Build on prior answers with relevant follow-up questions
- Do NOT repeat questions already asked
- Be professional and concise
- Questions should match the role and level specified
"""

SYSTEM_EVALUATOR = """You are an expert interview evaluator.
Evaluate the candidate's answer and return ONLY valid JSON — no markdown, no explanation.
"""


def _llm(api_key: str, temperature: float = 0.7):
    return ChatOpenAI(model="gpt-4o-mini", temperature=temperature, openai_api_key=api_key)


def generate_first_question(role: str, level: str, api_key: str) -> str:
    llm = _llm(api_key)
    messages = [
        SystemMessage(content=SYSTEM_INTERVIEWER),
        HumanMessage(content=f"""
Start a mock interview.
Role: {role}
Level: {level}

Greet the candidate briefly (1 sentence), then ask your first interview question.
Keep it natural and professional.
""")
    ]
    return llm.invoke(messages).content.strip()


def generate_next_question(role: str, level: str, history: list, api_key: str) -> str:
    """
    history: list of {"question": ..., "answer": ..., "score": ...}
    """
    llm = _llm(api_key)
    history_text = "\n\n".join([
        f"Q: {h['question']}\nA: {h['answer']}\nScore: {h.get('score', 'N/A')}/10"
        for h in history
    ])
    messages = [
        SystemMessage(content=SYSTEM_INTERVIEWER),
        HumanMessage(content=f"""
Role: {role}
Level: {level}

Interview history so far:
{history_text}

Based on the candidate's performance, generate the NEXT interview question.
- If they struggled, clarify or simplify
- If they did well, increase complexity or ask a follow-up
- Vary between technical, conceptual, and practical questions
- Return ONLY the question text, nothing else.
""")
    ]
    return llm.invoke(messages).content.strip()


def evaluate_answer(question: str, answer: str, role: str, level: str, api_key: str) -> dict:
    """
    Returns: {score: float, feedback: str, technical_accuracy: str, communication: str}
    """
    llm = _llm(api_key, temperature=0.3)
    messages = [
        SystemMessage(content=SYSTEM_EVALUATOR),
        HumanMessage(content=f"""
Role: {role}
Level: {level}
Question: {question}
Candidate's Answer: {answer}

Evaluate and return ONLY this JSON (no backticks):
{{
  "score": <0-10 float>,
  "feedback": "<1-2 sentence constructive feedback>",
  "technical_accuracy": "<poor|fair|good|excellent>",
  "communication": "<poor|fair|good|excellent>"
}}
""")
    ]
    raw = llm.invoke(messages).content.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {"score": 5.0, "feedback": raw, "technical_accuracy": "fair", "communication": "fair"}


def generate_report(role: str, level: str, responses: list, api_key: str) -> dict:
    """
    responses: list of {question, answer, score, feedback}
    Returns full report dict
    """
    llm = _llm(api_key, temperature=0.4)
    qa_text = "\n\n".join([
        f"Q{i+1}: {r['question']}\nA: {r['answer']}\nScore: {r.get('score',0)}/10\nFeedback: {r.get('feedback','')}"
        for i, r in enumerate(responses)
    ])
    avg_score = sum(r.get("score", 0) for r in responses) / max(len(responses), 1)

    messages = [
        SystemMessage(content="You are an expert interview coach. Return ONLY valid JSON."),
        HumanMessage(content=f"""
Role: {role}
Level: {level}
Total Questions: {len(responses)}
Average Score: {avg_score:.1f}/10

Full Interview Transcript:
{qa_text}

Generate a comprehensive performance report. Return ONLY this JSON (no backticks, no markdown):
{{
  "technical_score": <0-100 float>,
  "communication_score": <0-100 float>,
  "overall_score": <0-100 float>,
  "strengths": "<bullet list of 3-4 strengths separated by |>",
  "weaknesses": "<bullet list of 3-4 weak areas separated by |>",
  "recommendations": "<bullet list of 3-4 actionable tips separated by |>",
  "summary": "<2-3 sentence overall performance summary>"
}}
""")
    ]
    raw = llm.invoke(messages).content.strip()
    try:
        return json.loads(raw)
    except Exception:
        return {
            "technical_score": avg_score * 10,
            "communication_score": avg_score * 10,
            "overall_score": avg_score * 10,
            "strengths": "Shows effort|Attempted all questions",
            "weaknesses": "Needs more depth|Review core concepts",
            "recommendations": "Practice more|Study fundamentals",
            "summary": "The candidate completed the interview. Review individual responses for detailed feedback."
        }
