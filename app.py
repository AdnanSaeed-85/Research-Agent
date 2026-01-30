import gradio as gr
from main import main
from langchain_core.messages import HumanMessage, AIMessage

graph, config = main()

def chat(message, history):
    response = ""
    for chunk in graph.stream({'messages': HumanMessage(content=message)}, config, stream_mode="messages"):
        msg, _ = chunk
        if isinstance(msg, AIMessage) and hasattr(msg, 'content') and msg.content:
            response += msg.content
    return response

with gr.Blocks() as demo:
    gr.ChatInterface(chat)

demo.launch()