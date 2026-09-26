from src.agent.tools.calculator import calculate
from src.agent.tools.web_search import web_search
from src.generation.pipeline import GenerationPipeline

from .router import route
from .state import AgentState


def run_workflow(query: str) -> AgentState:
    """Route a query and execute the corresponding workflow."""
    query = query.strip()

    if not query:
        raise ValueError("Query must not be empty.")

    selected_route = route(query)

    state: AgentState = {
        "query": query,
        "route": selected_route,
        "answer": "",
        "citations": [],
        "retrieved_chunks": [],
        "error": None,
    }

    if selected_route == "rag":
        result = GenerationPipeline().run(query)

        state["answer"] = result.answer
        state["citations"] = result.citations
        state["retrieved_chunks"] = result.retrieved_chunks
        state["complexity"] = result.complexity
        state["retrieval_budget"] = result.retrieval_budget

    elif selected_route == "calculator":
        try:
            result = calculate(query)
            state["answer"] = str(result)
            state["tool_result"] = result

        except NotImplementedError as exc:
            state["error"] = str(exc)
            state["answer"] = "Calculator backend is not configured yet."

    elif selected_route == "web_search":
        try:
            results = web_search(query)

            if results:
                state["tool_result"] = results
                state["answer"] = str(results)
            else:
                state["error"] = "Web search returned no results."
                state["answer"] = "No search results were found."

        except NotImplementedError as exc:
            state["error"] = str(exc)
            state["answer"] = "Web search backend is not configured yet."

    else:
        state["error"] = f"Unsupported route: {selected_route}"
        state["answer"] = "The requested route is not supported."

    return state