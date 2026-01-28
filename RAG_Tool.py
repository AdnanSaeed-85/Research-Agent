from langchain_core.tools import tool
from langchain_openai import OpenAIEmbeddings
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from CONFIG import OPENAI_EMBEDDED_MODEL

load_dotenv()
llm = OpenAIEmbeddings(model=OPENAI_EMBEDDED_MODEL)

# document loader
pdf = PyPDFLoader(file_path="AI_Agent.pdf")
pages = pdf.load()
print(f"Total pages: {len(pages)}")
print(pages[0])  # Show first page

# document splitting
# document chunking
# generate embedding
# load embedding in database

# user query
# generate embedding

# semantic serach

# get output