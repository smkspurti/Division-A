# 🧹 DataCleanAgent

**Autonomous AI-Powered Data Quality Profiling & Restoration System**

DataCleanAgent is an agentic Generative AI system built for data science workflows. It autonomously ingests raw, messy CSV datasets, profiles quality errors across 6 core dimensions, executes self-healing data cleaning code using an LLM ReAct loop, compares before-and-after statistical states, and compiles comprehensive, professional audit reports in Microsoft Word (DOCX) format.

Built during the 2026 GenAI Hackathon.

---

## 🚀 Key Features & Deliverables

1. **Automated CSV Ingestion & Encoding Profiling**  
   Intelligently parses raw files by automatically detecting encodings (via `chardet`) and separators (via `csv.Sniffer`). Normalizes text-based sentinel null values (e.g., `'?'`, `'N/A'`, `'-'`, `'NULL'`) into standard numerical missing states.
   
2. **6-Dimension ISO-Inspired Statistical Profiling**  
   Assesses data health against a formal quality framework, scoring each dimension 0–100% and aggregating them into a single score using the weighted **harmonic mean** (to heavily penalize single-dimension failures):
   * **Completeness**: Missing values & sentinel patterns.
   * **Uniqueness**: Exact and near-duplicate row detection.
   * **Validity**: Conformance to schema types and logical boundaries (e.g., age range `[0, 120]`).
   * **Consistency**: Unifies categorical labeling variations (e.g., `M`/`male`/`Male`) using difflib fuzzy string distance grouping.
   * **Accuracy**: Flags numerical outliers via consensus IQR, Z-scores, and Isolation Forest.
   * **Integrity**: Evaluates logical constraint violations across columns.

3. **ReAct Autonomous Agent Cleaning Loop**  
   Uses Google Gemini 2.5 Flash inside a custom **Reason-Act-Observe** loop:
   * **Reason (Think)**: The agent analyzes statistical issues and plans appropriate actions.
   * **Act (Write Code)**: Writes precise pandas/numpy data-cleaning operations.
   * **Observe (Sandbox Exec)**: Code is run inside a secure sandbox copy of the DataFrame.
   * **Self-Heal (Correct Errors)**: If code fails, the agent parses traceback errors and automatically rewrites the code (up to 3 retries).
   
4. **Before-and-After Metrics Comparison**  
   Displays side-by-side performance cards, delta tables showing quality improvements per feature, and overlays interactive Plotly distribution histograms (raw vs restored values) for key variables.

5. **Professional Word (DOCX) Audit Report**  
   Generates a formal, printable Microsoft Word document complete with:
   * Cover details and executive summaries.
   * Explanations of statistical quality methodologies.
   * Embedded high-resolution bar charts of scores.
   * Tables mapping columns, types, nulls, and outliers.
   * A full audit trail table logging the reasoning and code behind every step.

---

## 🛠️ System Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                  Streamlit Interface (app.py)                │
│   📊 Profile View  │  🤖 Clean Console  │  📈 Compare  │  📄 Report │
└───────────────────────────────┬──────────────────────────────┘
                                │ (session_state DataFrames)
 ┌──────────────────────────────┼──────────────────────────────┐
 │                         LOGIC LAYER                         │
 │  ┌───────────────────────┐   ┌───────────────────────────┐  │
 │  │      profiler.py      │   │         agent.py          │  │
 │  │ • 6-Dimension Scoring │   │ • ReAct Reasoning Loop    │  │
 │  │ • Outlier & Type scan │   │ • Safe exec() Sandbox     │  │
 │  │ • Fuzzy Consistency   │   │ • Self-healing Correction │  │
 │  └──────────┬────────────┘   └─────────────┬─────────────┘  │
 │             │                              │                │
 │  ┌──────────▼────────────┐   ┌─────────────▼─────────────┐  │
 │  │        utils.py       │   │    report_generator.py    │  │
 │  │ • Smart CSV Load      │   │ • Compile DOCX Reports   │  │
 │  │ • Sentinel Null Strip │   │ • Render Chart Images    │  │
 │  └───────────────────────┘   └───────────────────────────┘  │
 └─────────────────────────────────────────────────────────────┘
                                │
                 ┌──────────────▼──────────────┐
                 │       Google Gemini API     │
                 │     (Gemini 2.5 Flash)      │
                 └─────────────────────────────┘
```

---

## ⚙️ Setup & Installation

Ensure you have Anaconda or standard Python 3.10+ installed.

1. **Clone/Move to the project directory**:
   ```bash
   cd s:\GenAi_hackthon
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set your Google Gemini API Key**:
   * You can set it as an environment variable:
     ```powershell
     $env:GOOGLE_API_KEY="YOUR_GEMINI_API_KEY"
     ```
   * Or simply enter it directly into the secure input box in the sidebar of the web application.

4. **Launch the Streamlit web dashboard**:
   ```bash
   streamlit run app.py
   ```
   Access the dashboard in your browser at `http://localhost:8501`.

---

## 📂 Project Structure

* **`app.py`**: Streamlit dashboard layout, widgets, charts, and streaming console integration.
* **`agent.py`**: The agentic heart. Implements the ReAct loop, Gemini model API handler, and execution sandbox.
* **`profiler.py`**: Complete statistical data profiling functions (IQR, Z-Score, Isolation Forest, fuzzy clustering).
* **`report_generator.py`**: Word DOCX report compilation functions, matplotlib chart renders, and layout styles.
* **`sample_data.py`**: Synthetic messy dataset generator (Titanic schema) for offline/demo use.
* **`utils.py`**: Delimiter detection, encoding detection, and sentinel null normalization helper functions.
* **`requirements.txt`**: List of Python package requirements.

---

## ⚖️ Open-Source Attributions & Dataset Credits

### Core Libraries
* **pandas** (BSD-3): Structuring, subsetting, and updating in-memory DataFrames.
* **NumPy** (BSD-3): Array operations and scientific NaN mapping.
* **scikit-learn** (BSD-3): Outlier isolation (Isolation Forest).
* **SciPy** (BSD-3): Descriptive and distribution statistics.
* **Streamlit** (Apache-2.0): Layout rendering, sliders, buttons, and state containers.
* **Plotly** (MIT): Interactive polar radar charts and overlaid histograms.
* **python-docx** (MIT): Programmatic Microsoft Word layout formatting.
* **matplotlib** (PSF) / **seaborn** (BSD-3): Static vector chart rendering for docx embedding.
* **chardet** (LGPL-2.1): Text encoding diagnostics.

### Dataset Attributions
* **Titanic Survival Dataset** (Public Domain): Real-world passenger logs from the 1912 Titanic disaster, demonstrating genuine missing values, categorical differences, and fare variances. Obtained from the Kaggle competition *Titanic: Machine Learning from Disaster*.
