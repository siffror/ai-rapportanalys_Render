import os
import pickle
import hashlib
import requests
import re
from bs4 import BeautifulSoup
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from fpdf import FPDF
from core.gpt_logic import search_relevant_chunks, generate_gpt_answer, get_embedding, chunk_text, full_rapportanalys
from utils import extract_noterade_bolag_table
import pdfplumber
from evaluator_ragas import evaluate_rag_sample

load_dotenv()

# --- Embedding-cachefunktioner ---
def get_embedding_cache_name(source_id: str) -> str:
    hashed = hashlib.md5(source_id.encode("utf-8")).hexdigest()
    return os.path.join("embeddings", f"embeddings_{hashed}.pkl")

def save_embeddings(filename, data):
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    with open(filename, "wb") as f:
        pickle.dump(data, f)

def load_embeddings_if_exists(filename):
    if os.path.exists(filename):
        with open(filename, "rb") as f:
            return pickle.load(f)
    return None

# --- Textutvinning från fil ---
def extract_text_from_file(file):
    text_output = ""
    if file.name.endswith(".pdf"):
        file.seek(0)
        try:
            with pdfplumber.open(file) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_output += page_text + "\n"
        except Exception as e:
            st.warning(f"⚠️ Kunde inte läsa PDF: {e}")

    elif file.name.endswith(".html"):
        soup = BeautifulSoup(file.read(), "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        text_output = soup.get_text(separator="\n")

    elif file.name.endswith((".xlsx", ".xls")):
        df = pd.read_excel(file)
        text_output = df.to_string(index=False)

    return text_output

@st.cache_data(show_spinner=False)
def fetch_html_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
        body_text = soup.get_text(separator="\n")
        clean_lines = [line.strip() for line in body_text.splitlines() if line.strip()]
        return "\n".join(clean_lines)
    except Exception as e:
        st.error(f"❌ Fel vid hämtning av HTML: {e}")
        return ""

def is_key_figure(row):
    patterns = [
        r"\b\d+[\.,]?\d*\s*(SEK|MSEK|kr|miljoner|tkr|USD|\$|€|%)",
        r"(resultat|omsättning|utdelning|kassaflöde|kapital|intäkter|EBITDA|vinst).*?\d"
    ]
    return any(re.search(p, row, re.IGNORECASE) for p in patterns)

# --- UI ---
st.set_page_config(page_title="📊 AI Rapportanalys", layout="wide")
st.markdown("<h1 style='color:#3EA6FF;'>📊 AI-baserad Rapportanalys</h1>", unsafe_allow_html=True)
st.image("https://www.appypie.com/dharam_design/wp-content/uploads/2025/05/headd.svg", width=120)

html_link = st.text_input("🌐 Rapport-länk (HTML)")
uploaded_file = st.file_uploader("📎 Ladda upp HTML, PDF, Excel eller bild", type=["html", "pdf", "xlsx", "xls", "png", "jpg", "jpeg"])

# --- Extrahera text ---
preview = ""
if uploaded_file:
    preview = extract_text_from_file(uploaded_file)
elif html_link:
    preview = fetch_html_text(html_link)
else:
    preview = st.text_area("✏️ Klistra in text manuellt här:", "", height=200)

text_to_analyze = preview

if preview:
    st.text_area("📄 Förhandsvisning:", preview[:5000], height=200)
else:
    st.warning("❌ Ingen text att analysera än.")


# --- Fullständig analys ---
if st.button("🔍 Fullständig rapportanalys"):
    if text_to_analyze:
        with st.spinner("📊 GPT analyserar hela rapporten..."):
            st.markdown("### 🧾 Fullständig AI-analys:")
            st.markdown(full_rapportanalys(text_to_analyze))
    else:
        st.error("Ingen text tillgänglig för analys.")

# --- GPT Fråga ---
if "user_question" not in st.session_state:
    st.session_state.user_question = "Vilken utdelning per aktie föreslås?"
st.text_input("Fråga:", key="user_question")

if text_to_analyze and len(text_to_analyze.strip()) > 20:
    if st.button("🔍 Analysera med GPT"):
        with st.spinner("🤖 GPT analyserar..."):
            source_id = (html_link or uploaded_file.name if uploaded_file else text_to_analyze[:50]) + "-v2"
            cache_file = get_embedding_cache_name(source_id)
            embedded_chunks = load_embeddings_if_exists(cache_file)

            if not embedded_chunks:
                chunks = chunk_text(text_to_analyze)
                embedded_chunks = []
                for i, chunk in enumerate(chunks, 1):
                    st.write(f"🔹 Chunk {i} – {len(chunk)} tecken")
                    try:
                        embedding = get_embedding(chunk)
                        embedded_chunks.append({"text": chunk, "embedding": embedding})
                    except Exception as e:
                        st.error(f"❌ Fel vid embedding av chunk {i}: {e}")
                        st.stop()
                save_embeddings(cache_file, embedded_chunks)

            context, top_chunks = search_relevant_chunks(st.session_state.user_question, embedded_chunks)
            st.code(context[:1000], language="text")
            answer = generate_gpt_answer(st.session_state.user_question, context)
            st.session_state.answer = answer
            st.session_state.top_chunks = top_chunks

            st.success("✅ Svar klart!")
            st.markdown(f"### 🤖 GPT-4o svar:\n{answer}")

            key_figures = [row for row in answer.split("\n") if is_key_figure(row)]
            if key_figures:
                st.markdown("### 📊 Möjliga nyckeltal i svaret:")
                for row in key_figures:
                    st.markdown(f"- {row}")

            st.download_button("💾 Ladda ner svar (.txt)", answer, file_name="gpt_svar.txt")
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            for line in answer.split("\n"):
                pdf.multi_cell(0, 10, line)
            st.download_button("📄 Ladda ner svar (.pdf)", pdf.output(dest="S").encode("latin1"), file_name="gpt_svar.pdf")
else:
    st.info("📝 Ange text, länk eller ladda upp en fil eller bild för att börja.")
# === RAGAS-evaluering (säkert och korrekt hanterat) ===
if "top_chunks" in st.session_state and "answer" in st.session_state:
    with st.expander("🧪 Utvärdera GPT-svar med RAGAS"):
        st.markdown("#### 🔍 RAG Evaluering")
        st.markdown("**Kontext (top chunks):**")
        for i, chunk in enumerate(st.session_state.top_chunks):
            st.code(chunk[1][:400], language="text")
    
        if st.button("Utvärdera RAG-svar"):
            contexts = [chunk[1] for chunk in st.session_state.top_chunks]
                scores = evaluate_rag_sample(
                    question=st.session_state.user_question,
                    answer=st.session_state.answer,
                    contexts=contexts
                )
            
                st.success("✅ Utvärdering klar!")
                st.metric("Faithfulness", f"{scores['faithfulness']:.2f}")
                st.metric("Answer Relevancy", f"{scores['answer_relevancy']:.2f}")
            except Exception as e:
                st.error(f"❌ Fel vid utvärdering: {e}")
else:
    st.info("💡 Kör först GPT-analysen innan du kan utvärdera svaret.")




