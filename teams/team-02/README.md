# 🎓 Plagiarism-Aware Student Essay Coach

Welcome to the official repository of the **Plagiarism-Aware Student Essay Coach** built by **Team A2** under **Domain 2: Education & Learning (CO4/CO5)**. 

This application is a state-of-the-art GenAI writing assistant that empowers students to refine their academic writing, correct stylistic and grammatical issues, and perform deep semantic checks against peer databases and live Wikipedia articles.

---

## 🎨 Core Features

* **💎 Premium Midnight-Glow Glassmorphism UI**: 
  A fully overhauled user interface with glowing cards, custom neon badges, styled tab routes, and visual performance scorecards.
* **🔍 Interactive Originality Coach**: 
  Highlights repetitive, clichéd, or robotic text. Hovering over a highlight opens a **zero-latency, pure-CSS tooltip** showing an assessment and **3 custom, human-sounding rephrasings**.
* **🌐 Dynamic Wikipedia Plagiarism Audit**: 
  Performs a real-time, double-pass semantic search. The app retrieves matching Wikipedia summaries, runs a cross-reference check via Groq, and displays direct copies and semantic paraphrases with links to source materials.
* **🎲 ASAP Dataset Sampler**: 
  Directly integrates the Hewlett Foundation ASAP training corpus. You can load random student essays with their original metadata (ID, Prompt Set, Rater Score) for live testing.
* **✨ Coached Essay Diff**: 
  Renders a word-level visual comparison between the original student draft and the AI-polished draft using standard library `difflib`.
* **🔑 Persistent API Configuration**: 
  Set your Groq key once in a local configuration file (`api_key.txt`) and run the app seamlessly without copy-pasting keys again.

---

## 🛠️ Technology Stack

* **LLM Core**: Meta Llama 3.3 (`llama-3.3-70b-versatile`) hosted on Groq Cloud.
* **Orchestration**: LangChain (Pydantic schemas with `with_structured_output` native tool-calling).
* **Interface**: Streamlit (with complete raw CSS overrides).
* **Data Processing**: Pandas & PyPDF.
* **Comparison Engine**: Python Standard `difflib` (SequenceMatcher).

---

## 📁 Project Structure

```
d:\HACKATHON\
├── app.py                # Streamlit controller, routes, page structures
├── essay_analyzer.py     # LangChain orchestrator & Pydantic output schemas
├── ui_components.py      # Premium glassmorphic styles & interactive tooltip generator
├── utils.py              # PDF extraction, difflib generators, and Wikipedia API parser
├── requirements.txt      # Python dependencies
├── api_key.txt           # Persistent Groq API Key storage file
└── DATASET/              
    └── training_set_rel3.tsv   # ASAP dataset (12,976 annotated student essays)
```

---

## 🚀 Installation & Local Setup

Get the application up and running locally in three quick steps:

### Step 1: Install Dependencies
Open your local terminal inside `d:\HACKATHON` and run:
```bash
pip install -r requirements.txt
```

### Step 2: Configure Your API Key
1. Locate the `api_key.txt` file in the root directory.
2. Open it and paste your **Groq Developer API Key** inside:
   ```text
   gsk_xxxxxxxxxxxxxxxxxxxxxxxxxxxx
   ```
3. Save and close the file.

### Step 3: Run the Streamlit Dashboard
Launch the dashboard via the Python module flag:
```bash
python -m streamlit run app.py
```
This will start your local development server and open the app in your default web browser (usually at `http://localhost:8501`).

---

## 👥 Team A2 Members
* 🎓 **Amogh Annigeri** (Roll No. 146, USN: `01fe23bcs210`)
* 🎓 **Yashaswini M** (Roll No. 163, USN: `01fe23bcs288`)
* 🎓 **Raveesh N** (Roll No. 160, USN: `01fe23bcs295`)

---
*Created for the GenAI Hackathon - Domain 2: Education & Learning.*
