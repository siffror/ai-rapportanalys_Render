# AI Rapportanalys – Streamlit-app

Detta repo innehåller en AI-driven analysapp för finansiella rapporter, byggd med Streamlit, OpenAI och EasyOCR.

## 🧠 Funktioner
- Ladda upp PDF, HTML eller bild
- OCR för bilder
- Embedding-baserad frågesökning
- Fullständig AI-analys
- Export till PDF och text

## 🚀 Deployment med Render

1. Skapa ett konto på https://render.com
2. Skapa ett nytt "Web Service" och koppla ditt GitHub-repo
3. Ange:
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `streamlit run app.py --server.port=$PORT --server.enableCORS=false`
4. Klart! Appen deployas automatiskt.

## 🗂 Filstruktur
- `app.py` – huvudappen
- `core/gpt_logic.py` – GPT och embedding-logik
- `ocr_utils.py` – bild- och textutvinning
- `requirements.txt` – beroenden
- `Procfile` – för Render startkommandot
