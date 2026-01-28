from typing import Annotated, TypedDict, Literal
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI # Or your preferred LLM

# 1. Define the State (The "Short-term Memory")
class AgentState(TypedDict):
    query: str
    decision: str
    data: str

# 2. Define the Nodes (The "Workers")
def supervisor(state: AgentState):
    """The Brain: Decides which DB to use."""
    # Logic: LLM analyzes query and returns 'chroma', 'postgres', 'mongo', or 'neo4j'
    return {"decision": "postgres"} # Mocking a decision

def chroma_node(state: AgentState):
    return {"data": "Fetched semantic vectors from ChromaDB"}

def postgres_node(state: AgentState):
    return {"data": "Fetched relational rows from PostgreSQL"}

def mongo_node(state: AgentState):
    return {"data": "Fetched JSON documents from MongoDB"}

def neo4j_node(state: AgentState):
    return {"data": "Fetched graph relationships from Neo4j"}

# 3. Define the Router Logic
def router(state: AgentState) -> Literal["chroma", "postgres", "mongo", "neo4j"]:
    return state["decision"]

# 4. Build the Graph
workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("supervisor", supervisor)
workflow.add_node("chroma", chroma_node)
workflow.add_node("postgres", postgres_node)
workflow.add_node("mongo", mongo_node)
workflow.add_node("neo4j", neo4j_node)

# Add Edges (The Flow)
workflow.set_entry_point("supervisor")

workflow.add_conditional_edges(
    "supervisor",
    router,
    {
        "chroma": "chroma",
        "postgres": "postgres",
        "mongo": "mongo",
        "neo4j": "neo4j"
    }
)

# All DB nodes go to END
workflow.add_edge("chroma", END)
workflow.add_edge("postgres", END)
workflow.add_edge("mongo", END)
workflow.add_edge("neo4j", END)

# Compile
app = workflow.compile()