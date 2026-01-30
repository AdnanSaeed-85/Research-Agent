import gradio as gr
from main import main
from langchain_core.messages import HumanMessage, AIMessage

# --- 1. Setup Graph ---
graph, config = main()

# ⚠️ FIX: Added 'history' argument here to match Gradio's requirement
def chat(message, history):
    full_response = ""
    tool_calls_seen = set()
    tool_status = ""
    
    # We ignore 'history' here because LangGraph manages its own memory
    for chunk in graph.stream({'messages': HumanMessage(content=message)}, config, stream_mode="updates"):
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

custom_css = """
#chatbot {
    height: 600px;
}
"""

# --- 2. UI with Sidebar ---
# ⚠️ FIX: Removed theme/css from here to fix the UserWarning
with gr.Blocks() as demo:
    
    with gr.Sidebar():
        gr.Markdown("## ℹ️ Agent Info")
        gr.Markdown(
            """
            This agent is powered by **LangGraph**.
            
            **Capabilities:**
            * Search documents
            * Execute Tools
            """
        )
        gr.Markdown("---")
        gr.Markdown("💡 **Tip**: Refresh the page to reset.")

    gr.Markdown("# 🤖 AI Research Agent")
    
    gr.ChatInterface(
        chat,
        chatbot=gr.Chatbot(elem_id="chatbot"),
        textbox=gr.Textbox(placeholder="Type your message here...", scale=7)
    )

# ⚠️ FIX: Moved theme and css here
demo.launch(theme=gr.themes.Soft(), css=custom_css, share=True)