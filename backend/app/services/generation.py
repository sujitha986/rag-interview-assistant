from app.services.roles import ROLES


def build_query(role: str, profile: dict, previous_answer: str | None = None) -> str:
    role_name = ROLES[role]["name"]
    terms = profile.get("skills", []) + profile.get("domains", [])
    if previous_answer:
        terms.append(previous_answer[:400])
    return f"{role_name} interview concepts {' '.join(terms)}"


def generate_question(role: str, profile: dict, contexts: list[dict], question_number: int) -> str:
    role_name = ROLES[role]["name"]
    focus = contexts[0]["title"] if contexts else "core role fundamentals"
    skill = (profile.get("skills") or ["your recent project"])[0]
    source_hint = contexts[0]["source"] if contexts else "the knowledge base"
    if question_number == 1:
        return (
            f"For the {role_name} role, connect your experience with {skill} to {focus}. "
            f"Using the idea from {source_hint}, how would you explain the tradeoff and apply it in a real project?"
        )
    if question_number == 2:
        return (
            f"Suppose a production system shows weak results around {focus}. "
            f"What evidence would you inspect first, and how would your background in {skill} shape the fix?"
        )
    if question_number == 3:
        return (
            f"Design a small experiment or backend flow that tests understanding of {focus}. "
            f"Name the data you would store and how you would decide whether the approach worked."
        )
    return (
        f"Based on {focus}, describe a failure mode an interviewer should watch for in a {role_name} candidate, "
        f"then answer how you would avoid that failure in your own implementation."
    )


def evaluate_answer(answer: str, contexts: list[dict]) -> dict:
    words = {word.strip(".,:;!?()[]{}").lower() for word in answer.split() if len(word) > 3}
    context_terms = set()
    for context in contexts:
        context_terms.update(
            word.strip(".,:;!?()[]{}").lower()
            for word in context["text"].split()
            if len(word) > 5
        )
    overlap = sorted(words & context_terms)[:10]
    depth = "strong" if len(answer.split()) >= 80 else "developing" if len(answer.split()) >= 35 else "thin"
    return {
        "depth": depth,
        "grounded_terms": overlap,
        "note": "Answer references retrieved concepts." if overlap else "Answer could connect more directly to retrieved context.",
    }

