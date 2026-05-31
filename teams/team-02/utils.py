import io
import difflib
from pypdf import PdfReader

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts plain text from the given PDF bytes.
    """
    try:
        pdf_file = io.BytesIO(file_bytes)
        reader = PdfReader(pdf_file)
        text = ""
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        return text.strip()
    except Exception as e:
        raise ValueError(f"Failed to extract text from PDF: {str(e)}")

def generate_diff_html(original: str, improved: str) -> str:
    """
    Generates a word-level visual diff between the original and improved text,
    wrapping edits in styled <ins> and <del> HTML tags.
    """
    if not original:
        return f'<ins class="diff-ins">{improved}</ins>'
    if not improved:
        return f'<del class="diff-del">{original}</del>'

    # Normalize newlines
    original = original.replace("\r\n", "\n")
    improved = improved.replace("\r\n", "\n")

    # Word-level split (retaining spaces and newlines would be ideal, 
    # but word-by-word matching is cleaner. Let's do list of words)
    orig_words = original.split()
    imp_words = improved.split()

    matcher = difflib.SequenceMatcher(None, orig_words, imp_words)
    html_parts = []

    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            html_parts.append(" ".join(orig_words[i1:i2]))
        elif tag == 'replace':
            del_text = " ".join(orig_words[i1:i2])
            ins_text = " ".join(imp_words[j1:j2])
            html_parts.append(f'<del class="diff-del">{del_text}</del> <ins class="diff-ins">{ins_text}</ins>')
        elif tag == 'delete':
            del_text = " ".join(orig_words[i1:i2])
            html_parts.append(f'<del class="diff-del">{del_text}</del>')
        elif tag == 'insert':
            ins_text = " ".join(imp_words[j1:j2])
            html_parts.append(f'<ins class="diff-ins">{ins_text}</ins>')

    # Convert space tokens back to single string
    diff_text = " ".join(html_parts)
    # Replace standard newline representations with HTML breaks for beautiful rendering
    diff_text = diff_text.replace("\n", "<br>")
    return diff_text

def get_random_asap_essay() -> dict:
    """
    Loads the ASAP dataset (training_set_rel3.tsv) and extracts a random student essay
    along with its metadata (prompt set, score).
    """
    import os
    import pandas as pd
    
    # Locate dataset file in current directory
    tsv_path = os.path.join(".", "DATASET", "training_set_rel3.tsv")
    if not os.path.exists(tsv_path):
        return None
    try:
        # Load using pandas
        df = pd.read_csv(tsv_path, sep="\t", encoding="ISO-8859-1")
        row = df.sample(n=1).iloc[0]
        asap_max_scores = {1: 12, 2: 6, 3: 3, 4: 3, 5: 4, 6: 4, 7: 24, 8: 60}
        essay_set = int(row["essay_set"])
        return {
            "essay_id": int(row["essay_id"]),
            "essay_set": essay_set,
            "essay_text": str(row["essay"]),
            "human_score": int(row["domain1_score"]),
            "max_score": asap_max_scores.get(essay_set, 10)
        }
    except Exception:
        return None

def fetch_wikipedia_content(query: str) -> dict:
    """
    Queries the public Wikipedia API for the best matching article,
    returning its title, plain text extract, and official URL.
    (Pure standard library implementation - zero external dependencies).
    """
    import urllib.request
    import urllib.parse
    import json
    
    if not query or not query.strip():
        return {"title": "", "extract": "", "url": ""}
        
    try:
        # Step 1: Search Wikipedia for the top matching page title
        search_url = (
            "https://en.wikipedia.org/w/api.php?action=query&list=search"
            f"&srsearch={urllib.parse.quote(query)}&format=json&utf8=1"
        )
        req = urllib.request.Request(search_url, headers={'User-Agent': 'EssayCoach/1.0'})
        with urllib.request.urlopen(req) as response:
            search_data = json.loads(response.read().decode('utf-8'))
            
        search_results = search_data.get("query", {}).get("search", [])
        if not search_results:
            return {"title": "", "extract": "", "url": ""}
            
        top_title = search_results[0]["title"]
        page_url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(top_title.replace(' ', '_'))}"
        
        # Step 2: Fetch the plain text summary extract of this page
        extract_url = (
            "https://en.wikipedia.org/w/api.php?action=query&prop=extracts"
            f"&exintro=1&explaintext=1&titles={urllib.parse.quote(top_title)}&format=json"
        )
        req2 = urllib.request.Request(extract_url, headers={'User-Agent': 'EssayCoach/1.0'})
        with urllib.request.urlopen(req2) as response2:
            extract_data = json.loads(response2.read().decode('utf-8'))
            
        pages = extract_data.get("query", {}).get("pages", {})
        extract = ""
        for page_id in pages:
            extract = pages[page_id].get("extract", "")
            break
            
        return {
            "title": top_title,
            "extract": extract,
            "url": page_url
        }
    except Exception:
        return {"title": "", "extract": "", "url": ""}


