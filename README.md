# Team 04
# 🏛️ BhoomiAI — AI Powered Land Mutation Application Generator

## 📌 Overview

BhoomiAI is a bilingual AI-powered governance platform designed to simplify the land mutation application process for rural citizens and landowners in Karnataka.

The system helps users:

* validate mutation requirements,
* upload supporting documents,
* generate official mutation applications,
* and download bilingual outputs in:

  * English
  * Kannada

The platform focuses on improving accessibility, reducing paperwork complexity, and simplifying legal workflows for rural users.

---

# 🚀 Problem Statement

Farmers and landowners in rural India often struggle with:

* understanding land mutation procedures,
* identifying required documents,
* preparing official applications,
* and language barriers.

BhoomiAI solves this problem through:

* AI-assisted document generation,
* bilingual accessibility,
* smart validation,
* and automated workflow support.

---

# ✨ Key Features

## ✅ AI-Powered Mutation Application Generation

Automatically generates formal government-style land mutation applications.

---

## ✅ Full Bilingual Support

Complete UI localization:

* English
* Kannada

Users can dynamically switch languages using the language toggle.

---

## ✅ Smart Validation Engine

Validates:

* required fields,
* Aadhaar number,
* mutation workflow completeness,
* and required supporting documents.

---

## ✅ Dynamic Document Checklist

Automatically identifies:

* required documents,
* uploaded documents,
* missing documents.

---

## ✅ PDF & DOCX Generation

Generate downloadable:

* PDF applications
* DOCX applications

---

## ✅ Premium Modern UI

Built using:

* Streamlit
* custom CSS
* glassmorphism UI
* modern dashboard design

---

# 🏗️ High Level Architecture

```text
                ┌─────────────────────────┐
                │      Streamlit UI       │
                │  (Frontend Interface)   │
                └──────────┬──────────────┘
                           │
                           ▼
               ┌──────────────────────────┐
               │  Input Collection Layer  │
               └──────────┬───────────────┘
                          │
                          ▼
               ┌──────────────────────────┐
               │   Validation Engine      │
               │  - Required fields       │
               │  - Aadhaar validation    │
               │  - Mutation checks       │
               └──────────┬───────────────┘
                          │
          ┌───────────────┴───────────────┐
          ▼                               ▼
┌────────────────────┐        ┌────────────────────┐
│ Checklist Generator │        │ AI Prompt Builder │
└─────────┬──────────┘        └─────────┬──────────┘
          │                              │
          ▼                              ▼
┌────────────────────┐        ┌────────────────────┐
│ Document Validation │        │ Open Source LLM   │
│ & Missing Docs      │        │ Application Draft │
└────────────────────┘        └─────────┬──────────┘
                                        │
                                        ▼
                         ┌────────────────────────┐
                         │ IndicTrans2 Translator │
                         │ English → Kannada      │
                         └──────────┬─────────────┘
                                    │
                                    ▼
                      ┌────────────────────────────┐
                      │ DOCX/PDF Generator         │
                      │ python-docx + reportlab    │
                      └──────────┬─────────────────┘
                                 │
                                 ▼
                     ┌─────────────────────────────┐
                     │ Download Center             │
                     │ PDF / DOCX / Text Outputs   │
                     └─────────────────────────────┘
```

---

# 🛠️ Technologies Used

## Frontend

* Streamlit
* Custom CSS
* HTML Components

## Backend

* Python

## AI & NLP

* Prompt Engineering
* Open-source LLM
* IndicTrans2

## Document Generation

* python-docx
* reportlab

## Data Handling

* Pandas
* JSON
* CSV

---

# 📂 Project Structure

```text
land-mutation-ai/
│
├── app.py
├── requirements.txt
├── README.md
│
├── data/
│   ├── karnataka_land_records_29495.csv
│   ├── karnataka_land_records_29495.json
│   ├── mutation_rules.json
│   ├── districts.json
│   └── villages.json
│
├── modules/
│   ├── validator.py
│   ├── checklist.py
│   ├── generator.py
│   ├── translator.py
│   ├── doc_generator.py
│   ├── pdf_generator.py
│   ├── language_manager.py
│   ├── translations.py
│   └── ui_styles.py
│
├── templates/
│   └── mutation_template.docx
│
├── outputs/
│
└── assets/
    ├── logo.png
    └── background.jpg
```

---

# 📊 Dataset Used

The project uses a realistic Karnataka land records dataset containing:

* 29,495 records
* 31 districts
* taluks
* villages
* survey numbers
* land ownership details
* mutation types

The dataset is used for:

* dropdown filtering,
* validation,
* realistic workflow simulation,
* and demo purposes.

---

# 🔄 Workflow

```text
User Input
    ↓
Validation Engine
    ↓
Checklist Generation
    ↓
Document Validation
    ↓
AI Prompt Builder
    ↓
Mutation Application Generation
    ↓
Kannada Translation
    ↓
DOCX/PDF Generation
    ↓
Download Center
```

---

# 🌐 Bilingual Accessibility

One of the major innovations of BhoomiAI is:

* complete bilingual accessibility.

Users can switch the entire interface between:

* English
* Kannada

This improves usability for rural Karnataka citizens.

---

# 📥 Installation & Setup

## 1️⃣ Clone Repository

```bash
git clone <repository-link>
cd BhoomiAI
```

---

## 2️⃣ Create Virtual Environment

```bash
py -3.11 -m venv .venv
```

Activate:

### Windows

```bash
.venv\Scripts\activate
```

---

## 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Run Application

```bash
streamlit run app.py
```

---

# 📌 Future Scope

Future improvements include:

* OCR document scanning
* voice input
* Bhoomi portal integration
* digital signature support
* mobile application deployment
* multilingual expansion

---

# 🎯 Key Innovation

BhoomiAI combines:

* AI-powered document automation,
* bilingual accessibility,
* smart validation,
* and governance workflow simplification

into a single integrated platform for rural citizens.

---

# 👨‍💻 Team

Hackathon Project — GenAI Hackathon 2026

Team 04

---

# 📜 License

This project is created for educational and hackathon purposes.
