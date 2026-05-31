from typing import List, Tuple
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq

class FlaggedPhrase(BaseModel):
    phrase: str = Field(
        ...,
        description="The EXACT sentence or phrase from the original essay to flag. Must match word-for-word, case-sensitive, including punctuation."
    )
    reason: str = Field(
        ...,
        description="Educational explanation of why this phrase is flagged (e.g., robotic, repetitive, lacks evidence, or matches common unoriginal templates)."
    )
    suggestions: List[str] = Field(
        ...,
        description="Exactly 3 natural, high-quality, and engaging paraphrased alternatives that the student can choose to replace the original phrase with."
    )

class DimensionFeedback(BaseModel):
    score: int = Field(
        ...,
        description="Score from 1 to 100 for this dimension."
    )
    strengths: List[str] = Field(
        ...,
        description="List of positive aspects identified in the essay for this dimension."
    )
    improvements: List[str] = Field(
        ...,
        description="List of concrete, constructive suggestions for improvement in this dimension."
    )

class WikipediaMatch(BaseModel):
    student_phrase: str = Field(
        ...,
        description="A sentence or phrase from the student essay that resembles or copies the Wikipedia content."
    )
    wikipedia_fact: str = Field(
        ...,
        description="The corresponding matched text/sentence or fact extracted from the Wikipedia page."
    )
    similarity_type: str = Field(
        ...,
        description="Plagiarism classification: 'Direct Copy' (verbatim text matches) or 'Paraphrased Match' (concepts and structure copied using synonyms)."
    )

class WikipediaPlagiarismReport(BaseModel):
    similarity_score: int = Field(
        ...,
        description="A calculated similarity index from 0 to 100 representing direct matches or heavy paraphrasing from the Wikipedia page."
    )
    verdict: str = Field(
        ...,
        description="Verdict, e.g., 'Low Similarity (Original)', 'Moderate Paraphrasing (Review recommended)', or 'High Similarity Risk'."
    )
    summary: str = Field(
        ...,
        description="Stylistic overview summarizing whether the student copied, patchworked, or correctly rephrased Wikipedia content."
    )
    matches: List[WikipediaMatch] = Field(
        ...,
        description="List of specific sentence-level matches found during cross-referencing."
    )

class EssayAnalysis(BaseModel):
    clarity: DimensionFeedback = Field(
        ...,
        description="Feedback and score for Clarity, readability, and sentence flow."
    )
    argument: DimensionFeedback = Field(
        ...,
        description="Feedback and score for Thesis strength, logic, and structure."
    )
    evidence: DimensionFeedback = Field(
        ...,
        description="Feedback and score for factual backing, citations, and critical reasoning."
    )
    grammar: DimensionFeedback = Field(
        ...,
        description="Feedback and score for spelling, punctuation, passive voice, and style consistency."
    )
    flagged_phrases: List[FlaggedPhrase] = Field(
        ...,
        description="List of specific phrases flagged in the original essay for plagiarism, unoriginality, or poor styling."
    )
    improved_draft: str = Field(
        ...,
        description="A completely rewritten, premium, and polished draft of the essay that resolves the identified shortcomings while retaining the student's core argument."
    )
    wikipedia_report: WikipediaPlagiarismReport = Field(
        ...,
        description="Cross-reference plagiarism audit result against a live Wikipedia article matching the essay topic."
    )

def extract_wikipedia_query(essay_text: str, api_key: str) -> str:
    """
    Pass 1: Invokes a quick LLM call to extract a clean 2-4 word search term representing the essay's core topic.
    """
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.1,
        api_key=api_key
    )
    prompt = (
        "You are a search engine keyword parser. Extract exactly one short, clean Wikipedia search query "
        "(2-4 words) that represents the main topic of the following student essay. Do not include quotes, "
        "punctuation, explanation, or introductions. Return ONLY the search terms (e.g., 'Censorship in libraries' or 'Computers in education').\n\n"
        f"Essay Text:\n\"\"\"\n{essay_text[:500]}\n\"\"\""
    )
    response = llm.invoke(prompt)
    return response.content.strip().replace('"', '').replace("'", "")

def analyze_essay(essay_text: str, groq_api_key: str) -> Tuple[EssayAnalysis, str, str]:
    """
    Pass 2: Pulls Wikipedia context, merges it with the essay prompt, and executes the structured essay coach audit.
    """
    if not groq_api_key.strip():
        raise ValueError("Groq API Key is empty. Please enter your key in the sidebar.")

    # 1. Extract clean Wikipedia Search Term
    try:
        wiki_query = extract_wikipedia_query(essay_text, groq_api_key)
    except Exception:
        wiki_query = "Computers in society"

    # 2. Fetch Wikipedia content dynamically using standard library helper
    import utils
    wiki_data = utils.fetch_wikipedia_content(wiki_query)
    wiki_title = wiki_data.get("title", "")
    wiki_extract = wiki_data.get("extract", "")
    wiki_url = wiki_data.get("url", "")

    # Set up safe fallback text if Wikipedia search yields empty results
    if not wiki_title or not wiki_extract.strip():
        wiki_title = "Academic Essay Composition"
        wiki_extract = "General academic essay writing best practices, referencing proper evidence, sentence clarity, structured arguments, and robust spelling rules."
        wiki_url = "https://en.wikipedia.org/wiki/Essay"

    # 3. Initialize ChatGroq for Main Orchestration
    llm = ChatGroq(
        model="llama-3.3-70b-versatile",
        temperature=0.3,
        api_key=groq_api_key
    )

    # Bind the structured output schema
    structured_llm = llm.with_structured_output(EssayAnalysis)

    system_prompt = (
        "You are an elite academic writing coach, writing professor, and editor.\n"
        "Your task is to analyze the student's essay and return structured, highly detailed feedback in the specified JSON format.\n"
        "Be constructive, professional, and educational. Keep in mind:\n"
        "1. Identify plagiarized, unoriginal, robotic, or poorly styled phrases.\n"
        "2. IMPORTANT: For each FlaggedPhrase, the 'phrase' field MUST match a contiguous substring of the student's essay EXACTLY (including punctuation, capitalization, and spaces). If it does not match exactly, the system will not be able to highlight it. Double-check that your extracted string is a character-for-character match in the original text.\n"
        "3. Provide exactly 3 high-quality paraphrased suggestions for each flagged phrase.\n"
        "4. Perform a semantic plagiarism check comparing the student essay against the provided Wikipedia reference text.\n"
        "   - Calculate the semantic similarity score (0 to 100) between the student essay and the Wikipedia content.\n"
        "   - Identify any sentences or parts in the student essay that are direct copies or heavily paraphrased matching blocks of the Wikipedia text.\n"
        "   - Populate these matched pairs in the `wikipedia_report` schema."
    )

    user_prompt = f"""Please analyze the following student essay.

Cross-Reference Reference Source (Wikipedia page: "{wiki_title}"):
\"\"\"
{wiki_extract}
\"\"\"

Student Essay:
\"\"\"
{essay_text}
\"\"\"
"""
    messages = [
        ("system", system_prompt),
        ("user", user_prompt)
    ]

    result = structured_llm.invoke(messages)
    return result, wiki_title, wiki_url



