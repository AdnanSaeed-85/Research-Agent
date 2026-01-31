import gradio as gr
from main import main
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.postgres import PostgresSaver
from CONFIG import POSTGRES_DB, POSTGRES_PASSWORD, POSTGRES_USER
import uuid

DB_PATH = f"postgresql://{POSTGRES_USER}:{POSTGRES_PASSWORD}@localhost:5442/{POSTGRES_DB}?sslmode=disable"

current_thread_id = None
current_user_id = None

def chat(message, history):
    global current_thread_id, current_user_id
    
    graph, config = main()
    config['configurable']['thread_id'] = current_thread_id
    config['configurable']['user_name'] = current_user_id
    
    full_response = ""
    tool_calls_seen = set()
    tool_status = ""
    
    for chunk in graph.stream({'messages': HumanMessage(content=message)}, config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            for msg in node_output.get('messages', []):
                if isinstance(msg, AIMessage):
                    if hasattr(msg, 'tool_calls') and msg.tool_calls:
                        for tool_call in msg.tool_calls:
                            if tool_call.get('id') not in tool_calls_seen:
                                tool_calls_seen.add(tool_call.get('id'))
                                tool_status += f"🔧 **Using tool**: `{tool_call.get('name', 'Unknown')}`\n"
                    elif msg.content:
                        full_response = msg.content
    
    final_response = (tool_status + "\n" + full_response) if tool_status else full_response
    history.append({"role": "user", "content": message})
    history.append({"role": "assistant", "content": final_response})
    
    return history, ""

def load_thread_history(thread_id):
    global current_thread_id
    current_thread_id = thread_id
    
    graph, config = main()
    config['configurable']['thread_id'] = thread_id
    config['configurable']['user_name'] = current_user_id
    
    history = []
    state = graph.get_state(config)
    
    if state and 'messages' in state.values:
        for msg in state.values['messages']:
            if isinstance(msg, HumanMessage):
                history.append({"role": "user", "content": msg.content})
            elif isinstance(msg, AIMessage) and msg.content:
                history.append({"role": "assistant", "content": msg.content})
    
    return history

def get_users():
    users = set()
    with PostgresSaver.from_conn_string(DB_PATH) as saver:
        for check in saver.list({}):
            config = check.config.get("configurable", {})
            user_name = config.get("user_name") or check.metadata.get("user_name") or "Unknown User"
            users.add(user_name)
    return sorted(list(users))

def get_threads_for_user(user_id):
    threads = []
    with PostgresSaver.from_conn_string(DB_PATH) as saver:
        for check in saver.list({}):
            config = check.config.get("configurable", {})
            user_name = config.get("user_name") or check.metadata.get("user_name") or "Unknown User"
            thread_id = config.get("thread_id")
            
            if user_name == user_id and thread_id and thread_id not in threads:
                threads.append(thread_id)
    return threads

def on_user_select(user_id):
    global current_user_id
    current_user_id = user_id
    threads = get_threads_for_user(user_id)
    return gr.update(choices=threads, value=threads[0] if threads else None), []

def create_new_thread():
    global current_thread_id
    
    new_thread_id = f"thread_{uuid.uuid4().hex[:8]}"
    current_thread_id = new_thread_id
    
    threads = get_threads_for_user(current_user_id) if current_user_id else []
    threads.insert(0, new_thread_id)
    
    return gr.update(choices=threads, value=new_thread_id), []

users = get_users()
current_user_id = users[0] if users else None
initial_threads = get_threads_for_user(current_user_id) if current_user_id else []
current_thread_id = initial_threads[0] if initial_threads else None

with gr.Blocks(css="#chatbot {height: 600px;}", theme=gr.themes.Soft()) as demo:
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("## 👤 Users")
            user_dropdown = gr.Dropdown(choices=users, label="Select User", value=current_user_id)
            
            gr.Markdown("## 📂 Threads")
            thread_dropdown = gr.Dropdown(choices=initial_threads, label="Select Thread", value=current_thread_id)
            
            with gr.Row():
                load_btn = gr.Button("Load", variant="primary", scale=1)
                new_thread_btn = gr.Button("➕ New", variant="secondary", scale=1)
        
        with gr.Column(scale=4):
            gr.Markdown("# 🤖 AI Research Agent")
            chatbot = gr.Chatbot(elem_id="chatbot", height=600)
            msg_box = gr.Textbox(placeholder="Type your message here...", show_label=False)
            send_btn = gr.Button("Send", variant="primary")
    
    user_dropdown.change(on_user_select, [user_dropdown], [thread_dropdown, chatbot])
    send_btn.click(chat, [msg_box, chatbot], [chatbot, msg_box])
    msg_box.submit(chat, [msg_box, chatbot], [chatbot, msg_box])
    load_btn.click(load_thread_history, [thread_dropdown], [chatbot])
    new_thread_btn.click(create_new_thread, [], [thread_dropdown, chatbot])

demo.launch()