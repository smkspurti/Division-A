# 🚚 Last-Mile Fleet Route Optimiser (Team 09)

A production-ready logistics optimization engine built specifically to solve the **Multi-Vehicle Capacitated Vehicle Routing Problem (CVRP)** for last-mile deliveries in Hubli, Karnataka. 

This application combines operations research mathematics, open-source geospatial routing engines, and lightweight large language models (LLMs) to maximize fleet efficiency, reduce total fuel costs, and automate communication workflows.

---

## 🎯 Project Overview

Managing a fleet of delivery vehicles manually leads to suboptimal paths, uneven cargo load distribution, and missed time windows. This project implements an automated, data-driven pipeline that takes a central depot address and exactly 10 delivery stops with varying package weights, then computes the absolute most efficient routing architecture under specific capacity constraints.

### The Engineering Stack
* **Frontend UI:** Streamlit (Features a multi-vehicle color-coded interactive tracking map, live manifest tables, and isolated driver briefing viewports).
* **Backend Framework:** FastAPI (Asynchronous REST API orchestrating the geocoding, matrix generation, CVRP optimization, and narrative pipelines).
* **Optimization Solver:** Google OR-Tools (Utilizing a soft-drop disjunction constraint model running **Guided Local Search** heuristics to solve complex combinatorial matrices under 5 seconds).
* **Geospatial Processing:** Nominatim (OpenStreetMap) for forward address geocoding and **OSRM (Open Source Routing Machine)** for pulling live real-world travel durations and network distances.
* **Logistics Communications:** Google Gemini 2.5 Flash via LangChain for compiling structured, landmark-specific driver briefs in English/Kannada and decoupled communication message layouts.

---

## 💡 Strategic Architectural Choice: Open-Source vs. Commercial APIs

A key architectural milestone of this project is its deliberate independence from proprietary commercial platforms like the Google Maps Platform or Mapbox. 

During the development phase, our engineering team evaluated commercial integrations but intentionally chose to build this platform entirely on top of the open-source **OpenStreetMap (OSM) ecosystem (OSRM & Nominatim)**. 

### Why this is a better engineering layout:
1. **No Corporate API Vendor Lock-in:** By running on OSRM, the routing engine is fully independent of corporate licensing policy shifts or breaking changes in closed-source SDKs.
2. **Absolute Cost Optimization:** Commercial mapping APIs enforce aggressive, multi-tiered pay-per-request monetization schemes (charging separate micro-fees for every single geocoding look-up, matrix cells generated, and routing step calculated). This open-source stack can be containerized using Docker and self-hosted on private infrastructure, dropping external runtime API operational overhead to **zero**.
3. **Privacy Compliance:** Customer coordinates and destination matrices are processed via an open-source pipeline instead of being streamed over to commercial aggregators, providing a robust layer of data privacy control.

---

## 🛠️ System Architecture & Data Pipeline

1. **Spatial Translation Layer:** Nominatim captures raw string addresses input into the Streamlit sidebar, appends a fallback geographic context loop (`Hubli, Karnataka, India`), and returns exact latitude/longitude coordinates.
2. **Cost Matrix Assembly:** Coordinates are bound into an array and submitted to the OSRM Table API, which returns an $N \times N$ matrix mapping precise real-world driving distances (meters) and times (seconds).
3. **Mathematical Optimization:** The matrix, vehicle fleet parameters, and package load weight arrays are processed by Google OR-Tools. It builds structural vehicle capacity limits and optimizes travel paths using advanced path-cheapest-arc constraint rules.
4. **Dynamic ETA Mapping:** Calculated node sequences pass through a custom speed table checking hour-of-day traffic weights (e.g., peak-hour restrictions vs. late-night speeds) and inject a mandatory 10-minute service time buffer at each stop. The final arrival time is dynamically grouped into highly professional, customer-friendly **15-minute ETA windows**.
5. **Data-Isolated Communications:** The structured schedule metadata passes to Gemini 2.5 Flash with a strict zero-hallucination prompt framework (no invented turn directions). It compiles high-density landmark check-points in English and natural Hubli-dialect Kannada. Real customer names are paired locally via Python loop parameters to prevent data tracking leaks to the LLM cloud layer.

---

## 🚀 Installation & Local Deployment

### Prerequisites
* Python 3.10 or higher
* A valid Google AI Studio Gemini API Key

### 1. Setup the Environment
Clone your fork locally, navigate into your project folder, and spin up a python virtual environment:
```bash
cd teams/team-09
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt
```
### 2. Configure Environment Variables
Create a file named `.env` in the root of the `team-09` directory and insert your Gemini API Key configuration:
```bash
GEMINI_API_KEY=your_actual_gemini_api_key_here
```
### 3. Launch the backend server
```bash
uvicorn main:app --reload --port 8000
```
### 4. Run the StreamLit frontend
```bash
streamlit run app.py
