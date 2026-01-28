from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage

load_dotenv()

llm = ChatOpenAI(model="gpt-4o-mini")

for chunk in llm.stream([HumanMessage(content="write 2 line paragaph")]):
    if chunk.content:
        print(chunk.content, end="", flush=True)
