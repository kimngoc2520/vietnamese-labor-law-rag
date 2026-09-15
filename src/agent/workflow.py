from .state import AgentState


def run_workflow(query: str) -> AgentState:
    return {"query": query, "answer": "", "citations": []}
