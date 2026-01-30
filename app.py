import gradio as gr
from main import main
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

graph, config = main()

def chat(message):
    full_response = ""
    tool_calls_seen = set()
    tool_status = ""
    
    for chunk in graph.stream({'messages': HumanMessage(content=message)}, config, stream_mode="updates"):
        for node_name, node_output in chunk.items():
            messages = node_output.get('messages', [])
            
            for msg in messages:
                # Check for tool calls
                if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
                    for tool_call in msg.tool_calls:
                        tool_id = tool_call.get('id')
                        if tool_id not in tool_calls_seen:
                            tool_calls_seen.add(tool_id)
                            tool_name = tool_call.get('name', 'Unknown')
                            tool_status += f"🔧 **Using tool**: `{tool_name}`\n"
                
                # Get AI response
                elif isinstance(msg, AIMessage) and msg.content:
                    full_response = msg.content
    
    # Combine tool status with response
    final_response = (tool_status + "\n" + full_response) if tool_status else full_response
    return final_response

custom_css = """
#chatbot {
    height: 600px;
}
"""

with gr.Blocks() as demo:
    gr.Markdown(
        """
        # 🤖 AI Research Agent
        ### Powered by LangGraph with Long-Term Memory
        Ask me anything! I can search documents and remember our conversations.
        """
    )
    
    gr.ChatInterface(
        chat,
        chatbot=gr.Chatbot(elem_id="chatbot"),
        textbox=gr.Textbox(placeholder="Type your message here...", scale=7)
    )
    
    gr.Markdown("---")
    gr.Markdown("💡 **Tip**: This agent has access to tools and maintains conversation memory.")

demo.launch(theme=gr.themes.Soft(), css=custom_css)