import app as gr
from main import main
from langchain_core.messages import HumanMessage, AIMessage

graph, config, store, checkpointer = main()

def chat(graph, config, store):
    user_input = input()
    for chunk in graph.stream({'messages': HumanMessage(content=user_input)}, config, stream_mode="messages"):
        msg, _ = chunk
        if isinstance(msg, AIMessage) and hasattr(msg, 'content') and msg.content:
            print(msg.content, end="", flush=True)

    namespace = ('user', config['configurable']['user_name'], 'details')
    output = store.search(namespace)
    print('\nLong-Term-Memory has...')
    for i in output:
        print(i.value['data'])

with gr.Blocks() as demo:
    chatbot = gr.Chatbot()
    msg = gr.Textbox(label="Message")
    
    msg.submit(chat, [msg, chatbot], chatbot)

demo.launch(share=True)