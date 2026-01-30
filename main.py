# ---------------------------- ALL IMPORTS -----------------------------
from langchain_groq import ChatGroq
from langgraph.graph import START, END, StateGraph
from pydantic import Field, BaseModel
from langgraph.store.base import BaseStore
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from CONFIG import GROQ_MODEL, POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER
from typing import Annotated, TypedDict, List
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.prebuilt import ToolNode, tools_condition
from prompt import MEMORY_PROMPT, SYSTEM_PROMPT_TEMPLATE
import uuid
from tools import add_tool
from langgraph.store.postgres import PostgresStore
from langgraph.checkpoint.postgres import PostgresSaver
from langsmith import traceable
from RAG_Tool import rag_search

# --------------------------- Pydantic Classes -----------------------------
class pydantic_1(BaseModel):
    text: str
    is_new: bool = Field(description="True if new memory, False if already exist")
class pydantic_2(BaseModel):
    should_add_or_not: bool = Field(description="True if it's able to add in long-term-memory, False otherwise not able to add")
    memories: List[pydantic_1] = Field(default_factory=list)


# ------------------------- .env load, Tools & LLM init ----------------------------
load_dotenv()

tools = [add_tool, rag_search]

llm = ChatGroq(model=GROQ_MODEL, temperature=0.2)
pydantic_llm = llm.with_structured_output(pydantic_2)
llm_with_tools = llm.bind_tools(tools)


# ---------------------------- State define -----------------------------
class create_state(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]


# ---------------------------- ALL NODES -----------------------------
# ------------ Remember Node ------------
@traceable(name='Remember node (Search + Store)')
def remember_node(state: create_state, config: RunnableConfig, store: BaseStore):
    try:
        "this node is used for remember items from memory"
        config = config['configurable']['user_name']
        namespace = ('user', config, 'details')
        
        search = store.search(namespace)
        serached_items = "\n".join(i.value.get('data', '') for i in search)

        last_message = state['messages'][-1].content

        decision: pydantic_2 = pydantic_llm.invoke([
            SystemMessage(
                content=MEMORY_PROMPT.format(
                    user_details_content=serached_items
                )
            ),
            HumanMessage(
                content=last_message
            )]
        )

        if decision.should_add_or_not:
            for mem in decision.memories:
                if mem.is_new and mem.text.strip():
                    store.put(namespace, str(uuid.uuid4()), {'data': mem.text.strip()})
    
    except Exception as e:
        print(f"Memory Error:- {e}")
    
    return {'messages': []}

# ------------ Chat Node -----------
@traceable(name='Chat node with personalized response')
def chat_node(state: create_state, config: RunnableConfig, store: BaseStore):
    "This Chat Node is used for chatting with personalization"
    config = config['configurable']['user_name']
    namespace = ('user', config, 'details')
    load = store.search(namespace)
    loaded = '\n'.join(i.value.get('data', '') for i in load)

    system_message = SystemMessage(
        content=SYSTEM_PROMPT_TEMPLATE.format(
            user_details_content=loaded
        )
    )

    response = llm_with_tools.invoke([system_message] + state['messages'])

    return {'messages': [response]}

# ------------ Tool Node -----------    
tool_node = ToolNode(tools)

@traceable(name='Tool Node')
def tools_with_logging(state: create_state):
    print(f"⚙️ Executing tools...")
    result = tool_node.invoke(state)
    print(f"\n✅ Tool execution completed\n")
    return result


# ---------------------------- ALL NODES -----------------------------
def main():
    DB_URI = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"
    
    config = {'configurable': {'user_name': 'user_2', 'thread_id': 'thread_2'}}

    with PostgresStore.from_conn_string(DB_URI) as store, \
    PostgresSaver.from_conn_string(DB_URI) as checkpointer:
        
        store.setup()
        checkpointer.setup()

        builder = StateGraph(create_state)

        builder.add_node('remember_node', remember_node)
        builder.add_node('chat_node', chat_node)
        builder.add_node('tools', tools_with_logging)

        builder.add_edge(START, 'remember_node')
        builder.add_edge('remember_node', 'chat_node')
        builder.add_conditional_edges('chat_node', tools_condition)
        builder.add_edge('tools', 'chat_node')

        graph = builder.compile(store=store, checkpointer=checkpointer)

        while True:
            user_input = input('You: ')
            if user_input in ['exit', 'bye', 'clear']:
                print('Thanks for calling\n')
                break

            print("Assistant: ", end="", flush=True)
            
            for chunk in graph.stream({'messages': HumanMessage(content=user_input)}, config, stream_mode="messages"):
                msg, _ = chunk
                if isinstance(msg, AIMessage) and hasattr(msg, 'content') and msg.content:
                    print(msg.content, end="", flush=True)
            print()
            namespace = ('user', config['configurable']['user_name'], 'details')
            output = store.search(namespace)
            print('\nLong-Term-Memory has...')
            for i in output:
                print(i.value['data'])
            print()

if __name__ == '__main__':
    main()
    