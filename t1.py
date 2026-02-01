from langchain_openai import ChatOpenAI
from dotenv import load_dotenv

load_dotenv()

llm = ChatOpenAI(model='gpt-4o-mini')

print(llm.invoke("Hi, my self adnan saeed").content)
print(llm.invoke("What's my name?").content)