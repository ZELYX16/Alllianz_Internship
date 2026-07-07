from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from langchain_ollama import ChatOllama
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.document_loaders import (
    DirectoryLoader, 
    TextLoader, 
    PyPDFLoader, 
    Docx2txtLoader,
    UnstructuredExcelLoader, 
    UnstructuredPowerPointLoader,
    CSVLoader
)
from langchain_community.vectorstores import Chroma
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_classic.agents import create_react_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os

app = FastAPI(title="Research Assistant API")

# Ollama chat 
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
llm = ChatOllama(model="mistral", base_url=OLLAMA_BASE_URL, temperature=0)

# fetch the docs folder
docs_dir = "./docs"
os.makedirs(docs_dir, exist_ok=True) 

# mapping of loaders for corresponding extension types
loader_mapping = {
    ".md": TextLoader,
    ".txt": TextLoader,
    ".pdf": PyPDFLoader,
    ".docx": Docx2txtLoader,
    ".csv": CSVLoader,
    ".xlsx": UnstructuredExcelLoader,
    ".xls": UnstructuredExcelLoader,
    ".pptx": UnstructuredPowerPointLoader,
    ".ppt": UnstructuredPowerPointLoader
}

documents = []
for ext, loader_cls in loader_mapping.items():
    try:
        loader = DirectoryLoader(docs_dir, glob=f"**/*{ext}", loader_cls=loader_cls, silent_errors=True)
        documents.extend(loader.load())
    except Exception as e:
        print(f"Skipping loading configuration for {ext}: {e}")

if not documents:
    from langchain_core.documents import Document
    documents = [Document(page_content="System Initialized. Awaiting document uploads.", metadata={"source": "system"})]


#splitting the data into manageable chunks for the llm.
text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
texts = text_splitter.split_documents(documents)

#embedding the split text and then storing to vector store
embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectorstore = Chroma.from_documents(texts, embeddings)
retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

#tool definitions for the llm 
@tool
def search_local_docs(query: str) -> str:
    """Useful for searching through local documents to find factual information. 
    Input should be a specific search query string."""
    try:
        if not isinstance(query, str):
            return f"Error: Expected a string, got {type(query)}."
        docs = retriever.invoke(query)
        if not docs:
            return "No relevant documents found."
        return "\n\n".join([d.page_content for d in docs])
    except Exception as e:
        return f"Search tool error: {str(e)}"

@tool
def summarize(text: str) -> str:
    """Useful for condensing long blocks of text into a concise summary.
    Input MUST be a valid string."""
    try:
        if not isinstance(text, str):
            return f"Error: Expected a string, got {type(text)}."
        prompt = f"Please provide a concise summary of the following text:\n\n{text}"
        response = llm.invoke(prompt)
        return response.content  
    except Exception as e:
        return f"Summarize tool error: {str(e)}"

tools = [search_local_docs, summarize]


prompt = ChatPromptTemplate.from_messages([
    ("system", """Answer the following questions as best you can. You have access to the following tools:

{tools}

Use the following format strictly:
Question: the input question you must answer
Thought: you should always think about what to do
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
... (this Thought/Action/Action Input/Observation can repeat N times)
Thought: I now know the final answer
Final Answer: the final answer to the original input question"""),
    
    # Placeholder for the rolling window of historical chat messages
    MessagesPlaceholder(variable_name="chat_history"),
    
    # Active query input and agent scratchpad for the ReAct execution trace
    ("human", "{input}\n\nThought: {agent_scratchpad}")
])

# Create the agent using the chat LLM and structured prompt
agent = create_react_agent(llm, tools, prompt)

agent_executor = AgentExecutor(
    agent=agent, 
    tools=tools, 
    verbose=True, 
    handle_parsing_errors=True,     
    max_iterations=3,              
    early_stopping_method="generate" 
)

# --- 5. API ENDPOINTS ---
class ChatRequest(BaseModel):
    query: str
    chat_history: list[dict] = []  

class ChatResponse(BaseModel):
    answer: str

@app.post("/chat", response_model=ChatResponse)
async def chat_endpoint(request: ChatRequest):
    try:
        
        active_history = request.chat_history[-6:] if len(request.chat_history) > 6 else request.chat_history
        
        # Convert the incoming JSON array into explicit LangChain message objects
        formatted_messages = []
        for msg in active_history:
            if msg["role"] == "user":
                formatted_messages.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                formatted_messages.append(AIMessage(content=msg["content"]))
        
        # Execute the agent chain
        response = agent_executor.invoke({
            "input": request.query,
            "chat_history": formatted_messages  # Passed as an object list instead of raw text strings
        })
        
        return ChatResponse(answer=response["output"])
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))