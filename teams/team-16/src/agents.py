import os
from dotenv import load_dotenv
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI

load_dotenv()

class FIRProcessingAgents:
    def __init__(self, llm_provider="gemini"):
        self.llm = ChatGoogleGenerativeAI(model="gemini-flash-latest", temperature=0.1)

    def extract_fir_details(self, markdown_text: str) -> dict:
        prompt = PromptTemplate(
            template="""You are an expert legal extractor. Extract the following information from the FIR text provided.
            Output your response as a pure JSON object with the following keys:
            - date_filed (string)
            - police_station (string)
            - complainant_name (string)
            - accused_name (string or "Unknown")
            - sections_invoked (list of strings, e.g., ["BNS 318", "IPC 420"])
            - legal_narrative (string: the exact story/narrative written in the FIR)
            
            FIR Text:
            {text}
            Return ONLY the JSON. No markdown formatting blocks.""",
            input_variables=["text"]
        )
        try:
            return (prompt | self.llm | JsonOutputParser()).invoke({"text": markdown_text})
        except Exception:
            return {"error": "Extraction failed"}

    def simplify_narrative(self, legal_narrative: str) -> str:
        if not legal_narrative: return ""
        prompt = PromptTemplate(
            template="""Translate the following complex police FIR narrative into simple, easy-to-understand English at an 8th-grade reading level. Remove overly complex legal jargon but keep all the facts.\n\n{narrative}""",
            input_variables=["narrative"]
        )
        return (prompt | self.llm | StrOutputParser()).invoke({"narrative": legal_narrative})

    def check_discrepancies(self, complainant_statement: str, fir_narrative: str) -> str:
        if not complainant_statement or not complainant_statement.strip(): return "No complainant statement provided to check for discrepancies."
        prompt = PromptTemplate(
            template="""Compare the Complainant's original statement with what the police actually wrote in the FIR narrative.\nComplainant's Statement: {statement}\nFIR Narrative: {fir}\nPoint out any discrepancies (missing facts, added allegations).""",
            input_variables=["statement", "fir"]
        )
        return (prompt | self.llm | StrOutputParser()).invoke({"statement": complainant_statement, "fir": fir_narrative})
