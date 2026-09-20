from .router import route
from .state import AgentState
from src.generation.pipeline import GenerationPipeline
from src.agent.tools.calculator import calculate
from src.agent.tools.web_search import web_search


def run_workflow(query: str) -> AgentState:
    """Route a query and execute the corresponding workflow."""
    selected_route = route(query)

    state: AgentState = {
        "query": query,
        "route": selected_route,
        "answer": "",
        "citations": [],
        "retrieved_chunks": [],
    }

    if selected_route == "rag":
        result = GenerationPipeline().run(query)

        state["answer"] = result.answer
        state["citations"] = result.citations
        state["retrieved_chunks"] = result.retrieved_chunks

    elif selected_route == "calculator":
        try:
            result = calculate(query)
            state["answer"] = str(result)
        except NotImplementedError:
            state["answer"] = "Calculator backend is not configured yet."

    elif selected_route == "web_search":
        results = web_search(query)

        if results:
            state["answer"] = str(results)
        else:
            state["answer"] = "Web search backend is not configured yet."

    return state