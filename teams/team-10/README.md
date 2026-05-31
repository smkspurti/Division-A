# Urban Heat Island (UHI) Analysis and Mitigation Report Generator

## Team A10
| Name | Roll No | USN |
|------|---------|-----|
| Sharan | 106 | 01FE23BCS027 |
| Sukanya | 110 | 01FE23BCS053 |
| Akshay Jalawadi | 127 | 01FE23BCS099 |
| Ankit | 128 | 01FE23BCS127 |

## Problem Statement
Indian cities are experiencing rising urban heat island effects that increase energy consumption and health risks. This GenAI system takes satellite land surface temperature data for Hubballi-Dharwad, identifies hot-spot zones, analyses contributing factors, and generates a mitigation strategy report.

## Dataset Used
- **NASA ECOSTRESS Tiled Land Surface Temperature and Emissivity (ECO_L2T_LSTE.002)**
  - Source: NASA AppEEARS (appeears.earthdatacloud.nasa.gov)
  - Resolution: 70m
  - Coverage: Hubballi-Dharwad, Karnataka
  - Period: April–June 2023 (peak summer)
  - Citation: Hook, S., & Hulley, G. (2022). ECOSTRESS Tiled Land Surface Temperature and Emissivity Instantaneous L2 Global 70 m v002. NASA LP DAAC. https://doi.org/10.5067/ECOSTRESS/ECO_L2T_LSTE.002

## Tech Stack
- **Python** — core language
- **Streamlit** — web application framework
- **Folium** — interactive heatmap visualisation
- **Rasterio** — geospatial data processing
- **Pandas / NumPy** — data analysis
- **GeoPandas** — spatial data handling
- **Google Gemini AI (gemini-2.0-flash)** — mitigation report generation
- **python-docx** — DOCX report export
- **Plotly** — interactive charts

## Architecture Flow

NASA ECOSTRESS CSV Data
↓
Data Loading & Preprocessing
(Kelvin → Celsius conversion, cloud filtering)
↓
Hotspot Detection
(Statistical zoning: Critical / High / Moderate / Normal)
↓
Contributing Factor Analysis
(Built-up density, green cover, impervious surfaces)
↓
Folium Heatmap Visualisation
↓
Gemini AI → Mitigation Strategy Generation
↓
python-docx → DOCX Report Export
↑
All wrapped in Streamlit Web App

## Features
- Upload NASA LST CSV data
- Automatic hotspot zone detection using statistical thresholds
- Interactive heatmap on real Hubballi-Dharwad map
- Location-wise temperature analysis with charts
- AI-generated mitigation report (tree plantation, reflective surfaces, water bodies)
- Downloadable DOCX report

## How to Run
```bash
git clone <repo-url>
cd uhi_project
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## How to Use
1. Get a free Gemini API key from aistudio.google.com
2. Enter the API key in the sidebar
3. Upload the NASA ECOSTRESS CSV file
4. Explore the Heatmap, Analysis, and Report tabs
5. Click "Generate Report" to get AI mitigation strategy
6. Download the DOCX report

## Domain
Environment & Sustainability (CO5)