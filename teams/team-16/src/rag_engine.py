import os
import re
import pandas as pd
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_core.documents import Document

class LegalRAGEngine:
    def __init__(self, data_path: str = "data/bns_sections.csv", vector_store_path: str = "data/faiss_index"):
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.data_path = os.path.join(base_dir, data_path)
        self.vector_store_path = os.path.join(base_dir, vector_store_path)
        self.embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        self.vector_store = None

    def initialize_vector_store(self):
        if os.path.exists(self.vector_store_path):
            self.vector_store = FAISS.load_local(self.vector_store_path, self.embeddings, allow_dangerous_deserialization=True)
            return
        if not os.path.exists(self.data_path): raise FileNotFoundError(f"BNS Dataset not found at {self.data_path}. Please download it.")
        df = pd.read_csv(self.data_path)
        documents = []
        for _, row in df.iterrows():
            section = str(row.get('Section', row.get('section', 'Unknown')))
            title = str(row.get('Section _name', row.get('Section_name', 'Unknown')))
            desc = str(row.get('Description', row.get('description', 'No description')))
            documents.append(Document(page_content=f"Section: {section}\nOffense: {title}\nDescription: {desc}", metadata={"section": section, "title": title}))
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        self.vector_store.save_local(self.vector_store_path)

    def get_section_details(self, section_number: str) -> str:
        if not self.vector_store: self.initialize_vector_store()
        
        # SMART FIX: Extract only the digits (e.g. "BNS 318" -> "318")
        match_num = re.search(r'\d+[A-Z]?', str(section_number))
        clean_section = match_num.group() if match_num else str(section_number)
        
        df = pd.read_csv(self.data_path)
        # Use regex to find the exact number as a standalone word
        match = df[df.astype(str).apply(lambda x: x.str.contains(rf'\b{clean_section}\b', case=False, na=False, regex=True)).any(axis=1)]
        
        if not match.empty:
            row = match.iloc[0]
            return f"{row.get('Section', '')} - {row.get('Section _name', row.get('Section_name', ''))}: {row.get('Description', '')}"
        return f"Section {section_number} not found in database."

    def recommend_sections(self, narrative: str, k: int = 3) -> list:
        if not self.vector_store: self.initialize_vector_store()
        return [{"section": res.metadata.get("section"), "title": res.metadata.get("title"), "content": res.page_content} for res in self.vector_store.similarity_search(narrative, k=k)]
