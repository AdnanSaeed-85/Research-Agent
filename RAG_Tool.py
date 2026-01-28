from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from dotenv import load_dotenv
from langchain_community.document_loaders import PyPDFLoader
from langsmith import traceable
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain_core.tools import tool

load_dotenv()

@traceable(name='PDF Loading')
def pdf_loaded(file_path):
    loader = PyPDFLoader(file_path=file_path)
    return loader.load()

@traceable(name='PDF Splitting')
def pdf_splitting(pdf, chunk_size, chunk_overlap):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    return splitter.split_documents(pdf)

@traceable(name='Stored in Vector Database')
def vector_database(splitted, llm):
    vectors = OpenAIEmbeddings(model=llm)
    return FAISS.from_documents(splitted, vectors)

def build_vector_store(file_path: str, chunk_size: int = 1000, chunk_overlap: int = 200):
    pdf = pdf_loaded(file_path)
    splitted = pdf_splitting(pdf, chunk_size, chunk_overlap)
    vector_store = vector_database(splitted, 'text-embedding-3-small')
    return vector_store

# Build once at module load
VECTOR_STORE = build_vector_store('AI_Agent.pdf')

# Now create the tool
@tool
def rag_search(query: str) -> str:
    """
    Use this tool to answer questions using retrieved documents.
    Call this when the user asks about specific facts, documents,
    past data, research papers, or information not guaranteed
    to be in your training data.
    """
    docs = VECTOR_STORE.similarity_search(query, k=3)
    context = "\n\n".join([doc.page_content for doc in docs])
    llm = ChatOpenAI(model='gpt-4o-mini')
    prompt = f"""Answer the question based on the context below.
    Context:
    {context}
    Question: {query}
    Answer:"""
    
    response = llm.invoke(prompt)
    return response.content