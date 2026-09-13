from langgraph.graph import StateGraph, END
from src.state import AgentState
from src.agent import (
    investigate_node,
    execute_patch_node,
    verify_tests_node,
    resolve_node
)

def route_after_verification(state: AgentState) -> str:
    """
    Conditional edge router after running verification tests.
    """
    if state["tests_passed"] and state.get("modified_files"):
        return "resolve"
    elif state["tests_passed"]:
        # A passing baseline does not mean the reported issue has been addressed.
        # Generate a patch before attempting to open a PR.
        return "execute_patch"
    elif state["retry_count"] >= state["max_retries"]:
        return END
    else:
        return "execute_patch"

def build_issue_resolver_graph():
    """
    Assembles the LangGraph StateGraph state machine for the GitHub Issue Resolver.
    """
    workflow = StateGraph(AgentState)
    
    # 1. Add Nodes
    workflow.add_node("investigate", investigate_node)
    workflow.add_node("execute_patch", execute_patch_node)
    workflow.add_node("verify_tests", verify_tests_node)
    workflow.add_node("resolve", resolve_node)
    
    # 2. Set Entry Point
    workflow.set_entry_point("investigate")
    
    # 3. Add Edges
    workflow.add_edge("investigate", "verify_tests")  # Initial test verification before patch
    workflow.add_edge("execute_patch", "verify_tests")
    
    # 4. Conditional Edges
    workflow.add_conditional_edges(
        "verify_tests",
        route_after_verification,
        {
            "resolve": "resolve",
            "execute_patch": "execute_patch",
            END: END
        }
    )
    
    workflow.add_edge("resolve", END)
    
    return workflow.compile()
