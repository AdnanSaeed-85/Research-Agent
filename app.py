import gradio as gr
from main import main
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres import PostgresSaver
from CONFIG import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER

DB_PATH = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"
graph, config = main()

# Global variable to track current thread
active_thread_id = config["configurable"]["thread_id"]

def load_thread_chat(thread_id):
    global active_thread_id
    active_thread_id = thread_id  # Update active thread
    
    chat_history = []
    with PostgresSaver.from_conn_string(DB_PATH) as saver:
        checkpoints = saver.list({})
        for check in checkpoints:
            if check.config['configurable']['thread_id'] == thread_id:
                messages = check.checkpoint['channel_values'].get('messages', [])
                for msg in messages:
                    if isinstance(msg, HumanMessage):
                        chat_history.append({"role": "user", "content": msg.content})
                    elif isinstance(msg, AIMessage):
                        chat_history.append({"role": "assistant", "content": msg.content})
                break
    return chat_history

def chat(message, history):
    global active_thread_id
    
    # Create config with active thread AND user_name
    current_config = {
        "configurable": {
            "thread_id": active_thread_id,
            "user_name": config["configurable"]["user_name"]  # ✅ Add this
        }
    }
    
    full_response = ""
    tool_calls_seen = set()
    tool_status = ""
    
    for chunk in graph.stream({'messages': HumanMessage(content=message)}, current_config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            messages = node_output.get('messages', [])
            
            for msg in messages:
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_id = tool_call.get('id')
                        if tool_id not in tool_calls_seen:
                            tool_calls_seen.add(tool_id)
                            tool_name = tool_call.get('name', 'Unknown')
                            tool_status += f"🔧 **Using tool**: `{tool_name}`\n"
                
                elif isinstance(msg, AIMessage) and msg.content:
                    full_response = msg.content
    
    final_response = (tool_status + "\n" + full_response) if tool_status else full_response
    return final_response

with gr.Blocks() as demo:
    
    chatbot_display = gr.Chatbot(elem_id="chatbot")
    
    with gr.Sidebar():
        gr.Markdown("## ℹ️ Agent")
        gr.Markdown("---")

        with PostgresSaver.from_conn_string(DB_PATH) as saver:
            checkpinter = saver.list({})
            threads = []
            for check in checkpinter:
                thread_id = check.config['configurable']['thread_id']
                if thread_id not in threads:
                    threads.append(thread_id)
            
            for thread in threads:
                btn = gr.Button(thread)
                btn.click(
                    fn=lambda t=thread: load_thread_chat(t), 
                    inputs=None,
                    outputs=chatbot_display,
                    queue=False
                )

    gr.Markdown("# 🤖 AI Research Agent")
    
    gr.ChatInterface(
        chat,
        chatbot=chatbot_display,
        textbox=gr.Textbox(placeholder="Type your message here...", scale=7)
    )

demo.launch(theme=gr.themes.Soft())