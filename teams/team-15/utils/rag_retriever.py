"""
utils/rag_retriever.py
RAG (Retrieval-Augmented Generation) with ChromaDB
"""

import os
import pandas as pd
import streamlit as st

# Updated imports for newer langchain versions
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_community.vectorstores import Chroma
    from langchain_core.documents import Document
except ImportError:
    try:
        from langchain.embeddings import HuggingFaceEmbeddings
        from langchain.vectorstores import Chroma
        from langchain.schema import Document
    except ImportError:
        from langchain_community.embeddings import HuggingFaceEmbeddings
        from langchain_community.vectorstores import Chroma
        from langchain.schema import Document

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")
CHROMA_DIR = os.path.join(os.path.dirname(__file__), "..", "chroma_db")

@st.cache_resource
def load_embeddings():
    """Load sentence transformer embeddings"""
    return HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={'device': 'cpu'},
        encode_kwargs={'normalize_embeddings': True}
    )

def create_documents_from_fao():
    """Convert FAO CSV data into LangChain documents"""
    try:
        df = pd.read_csv(os.path.join(DATA_DIR, "Data.csv"), low_memory=False)
    except Exception as e:
        print(f"Error loading FAO data: {e}")
        return []
    
    documents = []
    for _, row in df.head(50).iterrows():
        commodity = str(row.get('commodity', ''))
        loss_pct = str(row.get('loss_percentage', ''))
        stage = str(row.get('food_supply_stage', row.get('activity', 'Processing')))
        
        if commodity and loss_pct and loss_pct != 'nan':
            content = f"""
            Crop: {commodity}
            Post-harvest Stage: {stage}
            Loss Percentage: {loss_pct}%
            Source: FAO Food Loss & Waste Database
            """
            metadata = {"source": "FAO", "crop": commodity.lower()}
            documents.append(Document(page_content=content, metadata=metadata))
    return documents

def create_documents_from_pest_data():
    """Convert pest calendar into documents"""
    pest_data = {
        "Rice": [
            {"pest": "Stem Borer", "season": "Jun-Sep", "risk": "High", "control": "Cartap hydrochloride 4G"},
            {"pest": "Brown Plant Hopper", "season": "Aug-Oct", "risk": "Severe", "control": "Pymetrozine 50WG"},
            {"pest": "Rice Weevil", "season": "Year-round", "risk": "Medium", "control": "Aluminum phosphide"},
        ],
        "Wheat": [
            {"pest": "Termites", "season": "Nov-Jan", "risk": "High", "control": "Chlorpyriphos 20EC"},
            {"pest": "Khapra Beetle", "season": "Storage", "risk": "Severe", "control": "Methyl bromide"},
        ],
        "Maize": [
            {"pest": "Stem Borer", "season": "Jul-Sep", "risk": "High", "control": "Granular carbofuran"},
            {"pest": "Weevils", "season": "Year-round", "risk": "Medium", "control": "Neem leaves"},
        ],
        "Pulses": [
            {"pest": "Bruchids", "season": "Apr-Jun", "risk": "Severe", "control": "Vegetable oil 5ml/kg"},
        ],
        "Groundnut": [
            {"pest": "Groundnut Beetle", "season": "First 3 months", "risk": "High", "control": "CO2 fumigation"},
        ]
    }
    
    documents = []
    for crop, pests in pest_data.items():
        for pest in pests:
            content = f"""
            Crop: {crop}
            Pest: {pest['pest']}
            Peak Season: {pest['season']}
            Risk Level: {pest['risk']}
            Control Method: {pest['control']}
            Source: ICAR Post-Harvest Bulletins
            """
            metadata = {"source": "ICAR", "crop": crop.lower()}
            documents.append(Document(page_content=content, metadata=metadata))
    return documents

def build_vectorstore():
    """Build or load ChromaDB vector store"""
    try:
        embeddings = load_embeddings()
        
        # Check if vector store already exists
        if os.path.exists(CHROMA_DIR) and len(os.listdir(CHROMA_DIR)) > 0:
            print("Loading existing vector store...")
            vectorstore = Chroma(persist_directory=CHROMA_DIR, embedding_function=embeddings)
            return vectorstore
        
        print("Creating new vector store...")
        documents = []
        documents.extend(create_documents_from_fao())
        documents.extend(create_documents_from_pest_data())
        
        if not documents:
            print("No documents created! Using minimal fallback data.")
            # Fallback documents
            fallback_docs = [
                "Rice post-harvest loss: 2.5% at processing stage. Store at 12-14% moisture.",
                "Wheat post-harvest loss: 1% at processing stage. Store at 10-12% moisture.",
                "Maize post-harvest loss: 0.5-2% at processing stage. Store in hermetic bags.",
                "Pest control for grains: Use aluminum phosphide fumigation for weevils.",
                "Government schemes: AMIF offers 25% subsidy for warehouse construction.",
            ]
            for text in fallback_docs:
                documents.append(Document(page_content=text, metadata={"source": "Fallback"}))
        
        vectorstore = Chroma.from_documents(
            documents=documents,
            embedding=embeddings,
            persist_directory=CHROMA_DIR
        )
        vectorstore.persist()
        print(f"Vector store created with {len(documents)} documents!")
        return vectorstore
        
    except Exception as e:
        print(f"Error building vector store: {e}")
        return None

def retrieve_context(query: str, crop: str = None, k: int = 3) -> str:
    """Retrieve relevant context from vector database"""
    try:
        vectorstore = build_vectorstore()
        if not vectorstore:
            return ""
        
        results = vectorstore.similarity_search(query, k=k)
        
        context_parts = []
        for doc in results:
            context_parts.append(f"- {doc.page_content.strip()}")
        
        return "\n".join(context_parts) if context_parts else ""
    
    except Exception as e:
        return ""

def get_rag_prompt_context(crop: str, query_type: str = "storage") -> str:
    """Get RAG context for specific query types"""
    if query_type == "storage":
        query = f"What are the best storage practices for {crop} crops?"
    elif query_type == "pest":
        query = f"What pests affect {crop} and how to control them during storage?"
    else:
        query = f"Post-harvest management and loss prevention for {crop}"
    
    return retrieve_context(query, crop=crop, k=3)