import streamlit as st
import pandas as pd
from pyairtable import Api
from PIL import Image
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
import numpy as np
import re
import streamlit.components.v1 as components

# === Manual ID → Startup Name mapping ===
id_to_name = {
    "2": "Heuristik",
    "3": "Metly",
    "6": "Skor",
    "7": "Robopedics",
    "9": "Quix",
    "10": "Calliope",
    "12": "Nidus Lab",
    "13": "Vivra",
    "14": "Lowerton",
    "15": "Chemometric Brain",
    "16": "Stamp",
    "17": "SheerMe",
    "18": "Zell",
    "19": "Anyformat",
    "21": "Valerdat",
    "22": "Kestrix Ltd.",
    "23": "LingLoop (Menorca)",
    "24": "Stand Up (Menorca)",
    "26": "Gaddex",
    "27": "Sheldonn",
    "28": "Vixiees",
    "29": "IKI Health Group sL",
    "30" : "ByteHide"
}

# === Manual mapping of Airtable record ID to founder names ===
founder_id_to_name = {
    "reckEp7yXcc5kUzw4": "Joan Jover",
    "recc1YJvKk9y9sNre": "Lluis Jover Vilafranca",
    "recjj5TVqlQ73gIml": "Artem Loginov",
    "recSj5tMjcNT787Gp": "Dmitry Zaets",
    "rec9qQtBw86jdfo0x": "Paula Camps",
    "recOv4tuPs1ZJQeLB": "Nil Rodas",
    "recmdeZCzXI2DyfDk": "Juan Alberto España Garcia",
    "recJs9xDdf3GHhhbJ": "Alejandro Fernández Rodríguez",
    "recq1vn95maYO1AFF": "Diego Pérez Sastre",
    "recAwUcK4UwYCQ8Nb": "Juan Huguet",
    "recogcsAZibIk4OPH": "Joaquin Diez",
    "rec60NVqarI2s48u3": "Rafael Casuso",
    "recsOZlQNZsFDSqtw": "Henrik Stamm Kristensen",
    "recAjgqqnSqgN6v8r": "Jacob Kristensen Illán",
    "recChH7IwT6LQOyv7": "Alejandro Paloma",
    "recLQijSLzobSCODd": "Víctor Vicente Sánchez",
    "recmhid6dQCAYG88A": "Antxon Caballero",
    "recUAQITJFLdtUYIz": "Thomas Carson",
    "recSrfVzDvKFjILAx": "Patricia Puiggros",
    "rec9Jv3VH5N3S2H7c": "Silvia Fernandez Mulero",
    "recD4WlvpZsevcIHT": "Lucy Lyons",
    "recTqg6QXDwmjKLmg": "Gorka Muñecas",
    "recW3rDeBmB5tq2Kz": "Anna Torrents",
    "recvQEIoPUFehzmeJ": "Graeme Harris",
    "recYcgQh2VU8KcrgU": "Lydia Taranilla",
    "recb5zUyj1wWDjkgT": "Ana Lozano Portillo",
    "reclX7It1sxtNFHOW": "Ignacio Barrea",
    "recqudxt04FlAgcKy": "Santiago Gomez",
    "recYjsxu2q09VddMK": "Dionís Guzmán",
    "recR7t8yYqGhlIc3C": "Iván Martínez",
    "rec7zMyfjA5RSDGmm": "Marc Serra",
    "rec26pQKXNolvda2P": "Miguel Alves Ribeiro",
    "recTf976Q3xY0zWnH": "Shakil Satar",
    "recoyqN8ST1jUO58Y": "Francisco Alejandro Jurado Pérez",
    "recDBB7bHPU1q397X": "Giorgio Fidei",
    "recKFc88VGjI7xpJn": "Aditya  Malhotra",
    "reccZ0ZCEPj48DZ1h": "Carlos Moreno Martín",
    "recpb9EYIYYU8jrpq": "Abel Navajas",
    "recxzCofGUvIuTJaM": "Javier Castrillo",
    "recr0MHr9fQReJy2m": "Eduard  Aran Calonja",
    "recy3oVDwgLtha2MV": "Carlos  Arboleya",
    "recWPSZTxNWOvbL4d": "Carlos Saro",
    "recjVjpczDp5CbYsU": "Alex Sanchez",
    "rec842iG1sXEsgmf1": "Pablo Pascual",
    "recGik3FBuGqYbZN5": "Alberto Garagnani",
    "recuT12JFw2AZIEGX": "Moritz Beck"
}

def normalize_list(value):
    """Return a list no matter what Airtable gives back."""
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return [] if value is None or (isinstance(value, float) and pd.isna(value)) else [str(value)]

def get_founder_id(val):
    """Handle Airtable linked-record objects or plain IDs."""
    return val.get("id") if isinstance(val, dict) else val

# === Streamlit page config ===
st.set_page_config(
    page_title="Startup Program Feedback Dashboard",
    page_icon=".streamlit/static/favicon.png",  # or "🚀", or "📊", or a path to a .png
    layout="wide"
)
st.image("https://images.squarespace-cdn.com/content/v1/67811e8fe702fd5553c65249/749161ba-4abb-4514-9642-edc82c1c9c9d/Decelera-Logo.png?format=1500w", width=500)

# === Airtable Config ===
AIRTABLE_PAT = st.secrets["airtable"]["api_key"]
BASE_ID = st.secrets["airtable"]["base_id"]
TABLE_ID = st.secrets["airtable"]["table_id"]

# === Airtable Connection ===
api = Api(AIRTABLE_PAT)
table = api.table(BASE_ID, TABLE_ID)
records = table.all()

# === Convert to DataFrame ===
df = pd.DataFrame([r["fields"] for r in records])

# === Fix {'specialValue': 'NaN'} values ===
def fix_cell(val):
    if isinstance(val, dict) and "specialValue" in val:
        return float("nan")
    return val

df = df.applymap(fix_cell)

# === Fallback to Id as startup identifier ===
df = df[df["Id"].notna()]
df["Id"] = df["Id"].astype(str)

# === General Stats ===
st.title("Decelera 2025 Program Feedback Dashboard")

st.markdown("""
**This dashboard summarizes real-time feedback from Decelera Experience Makers, from the team, and multiple due dilligiences conducted.**  

Use the dropdown below to explore each startup’s evaluation, or scroll down for program-wide insights.
            
""")


st.subheader("General view of the Program")
total_reviews = df["Number of Reviews"].fillna(0).sum()
avg_risk = df["Average RISK"].mean()
avg_reward = df["Average Reward"].mean()
num_startups = df["Id"].nunique()

col1, col2, col3, col4 = st.columns(4)
col1.metric("Number of Startups", num_startups)
col2.metric("Total Reviews", int(total_reviews))
col3.metric("Average Risk", f"{avg_risk:.2f}" if pd.notna(avg_risk) else "N/A")
col4.metric("Average Reward", f"{avg_reward:.2f}" if pd.notna(avg_reward) else "N/A")

# Sum the counts from all rows
yes_total = df["Investable_Yes_Count"].fillna(0).sum()
no_total = df["Investable_No_Count"].fillna(0).sum()

# Create pie chart data
pie_data = pd.DataFrame({
    "Response": ["Yes", "No"],
    "Count": [yes_total, no_total]
})

# Plot using Plotly
fig_pie = px.pie(
    pie_data,
    names="Response",
    values="Count",
    color="Response",
    color_discrete_map={"Yes": "green", "No": "red"},
    title="Experience Makers' Investability Votes"
)

fig_pie.update_traces(textinfo="label+percent", pull=[0.05, 0])
fig_pie.update_layout(height=400, showlegend=False)

st.plotly_chart(fig_pie, use_container_width=True)

# Define score tiers
def classify(value):
    if value > 3.5:
        return "High"
    elif value > 2.5:
        return "Medium"
    else:
        return "Low"

# Classify each startup
df["Risk Level"] = df["Average RISK"].apply(classify)
df["Reward Level"] = df["Average Reward"].apply(classify)

# Define labels from ID mapping
df["Startup Label"] = df["Id"].apply(lambda x: id_to_name.get(x, f"ID {x}"))

# Clean subset for plotting
plot_df = df[["Startup Label", "Average RISK", "Average Reward"]].dropna()

# Create scatter plot with unique color per startup
fig = px.scatter(
    plot_df,
    x="Average RISK",
    y="Average Reward",
    color="Startup Label",         # 🟢 each startup gets unique color
    text="Startup Label",
    labels={
        "Average RISK": "Risk Score",
        "Average Reward": "Reward Score"
    }
)
fig.update_xaxes(autorange = "reversed")


# Improve style
fig.update_traces(
    textposition='top center',
    textfont_color='black',
    marker=dict(size=12, line=dict(width=1, color='DarkSlateGrey'))
)

fig.update_layout(
    height=600,
    xaxis=dict(range=[4, 1], dtick=1, constrain="domain"),
    yaxis=dict(range=[1, 4], dtick=1),
    title="Risk vs. Reward Matrix",
    title_x=0.5,
    showlegend=False,  # Optional: turn off if too many startups
    shapes=[
        dict(type="line", x0=2.5, x1=2.5, y0=0, y1=4.2, line=dict(dash="dot", color="grey", width=1)),
        dict(type="line", x0=0, x1=4.2, y0=2.5, y1=2.5, line=dict(dash="dot", color="grey", width=1))
    ]
)
# Etiquetas de cuadrantes
fig.add_annotation(x=1.25, y=3.8, text="Riesgo alto, recompensa alta", showarrow=False, font=dict(size=12))
fig.add_annotation(x=3.5,  y=3.8, text="Riesgo bajo, recompensa alta", showarrow=False, font=dict(size=12))
fig.add_annotation(x=1.25, y=1.4, text="Riesgo alto, recompensa baja", showarrow=False, font=dict(size=12))
fig.add_annotation(x=3.5,  y=1.4, text="Riesgo bajo, recompensa baja", showarrow=False, font=dict(size=12))

st.plotly_chart(fig, use_container_width=True)

# === Dropdown
startup_ids = sorted(df["Id"].unique())


# === Dropdown using hardcoded ID → Name mapping ===
valid_ids = [id_ for id_ in df["Id"].unique() if id_ in id_to_name]
selected_id = st.selectbox(
    "Choose a Startup",
    options=sorted(valid_ids, key=int),
    format_func=lambda x: id_to_name.get(x, f"Startup {x}")
)

filtered = df[df["Id"] == selected_id]
if filtered.empty:
    st.warning("❌ No data for the selected startup.")
    st.stop()

row = filtered.iloc[0]

st.subheader(f"Evaluation for {id_to_name.get(selected_id, selected_id)}")

# === Display logo if available
logo_data = row.get("original logo")

if isinstance(logo_data, list) and len(logo_data) > 0 and "url" in logo_data[0]:
    logo_url = logo_data[0]["url"]
    st.image(logo_url, width=400)
else:
    st.info("No logo available for this startup.")


st.markdown(" ")
# -------------------------------------------------------------------
# 💸 1) INVESTABILITY  ───────────────────────────────────────────────
# -------------------------------------------------------------------
st.markdown("## Business Metrics")

st.subheader("💸 Investability")

yes_votes  = row.get("Investable_Yes_Count", 0) or 0
no_votes   = row.get("Investable_No_Count", 0) or 0
total_votes = yes_votes + no_votes
yes_ratio   = (yes_votes / total_votes * 100) if total_votes else 0

#–– yes / no / ratio  (3-column row)
col_yes, col_no, col_ratio = st.columns(3)
col_yes.metric("✅ Yes Votes",  int(yes_votes))
col_no.metric("❌ No Votes",    int(no_votes))
col_ratio.metric("🟢 Yes Ratio", f"{yes_ratio:.1f}%" if total_votes else "—")

# horizontal rule between the two big blocks
st.markdown("---")

st.subheader("Risk/Reward")

st.markdown("The following are the averages for the PROGRAM")
col11, col22= st.columns(2)
col11.metric("Average Risk", f"{avg_risk:.2f}" if pd.notna(avg_risk) else "N/A")
col22.metric("Average Reward", f"{avg_reward:.2f}" if pd.notna(avg_reward) else "N/A")

# === Average Risk and Reward (Side by Side)
st.markdown("The following are the averages for the STARTUP you selected")
risk_col, reward_col = st.columns(2)

risk_col.metric("Average Risk", round(row.get("Average RISK", 0), 2))
reward_col.metric("Average Reward", round(row.get("Average Reward", 0), 2))

st.markdown("""- **Risk**: based on  
  • *State of Development: How do you assess the current State of Development of the product?*  
  • *Momentum: Is the market momentum favorable in terms of trends, legislation, and market dynamics?*  
  • *Management: Does the company have the necessary expertise and execute effectively?*

- **Reward**: based on  
  • *Market potential: Is it large, accessible, and not overly competitive?*  
  • *Team strength: Does the team seem to have a strong bond and complement each other?*  
  • *Pain relevance: Does it address a real and significant problem in the market?*  
  • *Scalability: Is there a clear and feasible path for growth and expansion?*

All metrics are scored on a **scale from 1 to 4**, with 4 being the most favorable.""")

st.subheader("Risk Breakdown")

risk_scores = {
    "State of Development": row.get("Average RISK | State of development_Score", 0),
    "Momentum": row.get("Average RISK | Momentum_Score", 0),
    "Management": row.get("Average RISK | Management_Score", 0),
}

risk_df = pd.DataFrame.from_dict(risk_scores, orient="index", columns=["Score"]).reset_index()
risk_df.columns = ["Category", "Score"]

fig_risk = px.bar(
    risk_df,
    x="Category",
    y="Score",
    text="Score",
    color_discrete_sequence=["rgb(29, 202, 237)"]
)
fig_risk.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig_risk.update_layout(yaxis_range=[1, 4], height=450)

st.plotly_chart(fig_risk, use_container_width=True)

st.subheader("Reward Breakdown")

reward_scores = {
    "Market": row.get("Average Reward | Market_Score", 0),
    "Team": row.get("Average Reward | Team_Score", 0),
    "Pain": row.get("Average Reward | Pain_Score", 0),
    "Scalability": row.get("Average Reward | Scalability_Score", 0),
}

reward_df = pd.DataFrame.from_dict(reward_scores, orient="index", columns=["Score"]).reset_index()
reward_df.columns = ["Category", "Score"]

fig_reward = px.bar(
    reward_df,
    x="Category",
    y="Score",
    text="Score",
    color_discrete_sequence=["rgb(29, 202, 237)"]
)
fig_reward.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig_reward.update_layout(yaxis_range=[1, 4], height=450)

st.plotly_chart(fig_reward, use_container_width=True)

# --- 1. Names list stays the same ------------------------------------------
JUDGE_NAMES = [
    "Jorge Gonzalez-Iglesias", "Juan de Antonio", "Adam Beguelin",
    "Alejandro Lopez", "Alex Barrera", "Álvaro Dexeus", "Anastasia Dedyukhina",
    "Andrea Klimowitz", "Anna  Fedulow", "Bastien  Pierre Jean Gambini",
    "Beth Susanne", "David Beratech", "Elise Mitchell", "Esteban Urrea",
    "Fernando Cabello", "Gennaro Bifulco", "Ivan Alaiz", "Ivan Nabalon",
    "Ivan Peña", "Jair Halevi", "Jason Eckenroth", "Javier Darriba",
    "Juan Pablo Tejela", "Laura Montells", "Manel Adell", "Oscar Macia",
    "Paul Ford", "Pedro Claveria", "Philippe Gelis", "Ranny Nachmais",
    "Rebeca De Sancho", "Rui Fernandes", "Sean Cook", "Shadi  Yazdan",
    "Shari Swan", "Stacey  Ford", "Sven  Huber", "Torsten Kolind", "Jaime", "John Varuguese", "Elise Mitchel"
]

# --- 2. Simple HTML cleaner (unchanged) ------------------------------------
_HTML_BREAK_RE = re.compile(r"<br\s*/?>", flags=re.I)

def _clean_html(raw: str) -> str:
    if not isinstance(raw, str):
        return raw or ""
    txt = _HTML_BREAK_RE.sub("\n", raw)
    txt = txt.replace("**", "")
    return txt.strip()

# --- 3. Updated NAME regex --------------------------------------------------
# It matches a judge name followed by EITHER:
#   • end-of-string
#   • whitespace
#   • a capital letter (for “State”, “Momentum”…), a colon, or a newline
CATS = [
    "State of development", "Momentum", "Management",
    "Market", "Team", "Pain", "Scalability",
]

# === Expresión regular para categorías (con ":")
_CAT_RE = re.compile(r"(" + "|".join(map(re.escape, CATS)) + r")\s*:", flags=re.I)

# === Expresión regular para nombres de mentor
_NAME_RE = re.compile(
    r"(" + "|".join(re.escape(n) for n in JUDGE_NAMES) + r")(?=$|\s|[A-Z])",
    flags=re.I
)

def extract_mentor_scores(row) -> dict[str, dict[str, float]]:
    mentor_scores = defaultdict(dict)

    for cat in CATS:
        field_name = f"{cat} | Mentor Scores"
        raw = row.get(field_name)
        if not raw:
            continue
        entries = normalize_list(raw)
        for entry in entries:
            parts = [p.strip() for p in entry.split(",")]
            for p in parts:
                if ": " in p:
                    name, score = p.split(": ")
                    try:
                        mentor_scores[name.strip()][cat.lower()] = float(score.strip())
                    except ValueError:
                        continue
    return mentor_scores

# === Formatea texto con puntuaciones del mentor
def _format_categories(text: str, scores: dict[str, float] | None = None) -> str:
    text = _clean_html(text)
    matches = list(_CAT_RE.finditer(text))
    if not matches:
        return text.strip()

    out = []

    if matches[0].start() > 0:
        out.append(text[:matches[0].start()].strip())

    for idx, match in enumerate(matches):
        label = match.group(1).strip()
        key = label.lower()
        start = match.end()
        end = matches[idx + 1].start() if idx + 1 < len(matches) else len(text)
        body = text[start:end].strip()

        score = scores.get(key) if scores else None
        score_text = f" ({score:.2f})" if score is not None and pd.notna(score) else ""
        out.append(f"**{label}{score_text}:** {body}")

    return "\n\n".join(out)

# === Extrae (mentor, comentario sin procesar) desde string largo
def _group_by_mentor(raw: str) -> list[tuple[str, str]]:
    text = _clean_html(raw)
    hits = list(_NAME_RE.finditer(text))

    if not hits:
        yield "Anonymous", text.strip()
        return

    for idx, hit in enumerate(hits):
        mentor = hit.group(1).strip()
        start = hit.end()
        end = hits[idx + 1].start() if idx + 1 < len(hits) else len(text)
        comment = text[start:end].lstrip(' :–').strip()
        if comment:
            yield mentor, comment

# === Junta todas las banderas (green/yellow/red) para cada mentor
def collect_flag_records(row):
    flag_fields = [
        ("RISK | Green_exp",   "green"),
        ("RISK | Yellow_exp",  "yellow"),
        ("RISK | Red_exp",     "red"),
        ("Reward | Green_exp", "green"),
        ("Reward | Yellow_exp","yellow"),
        ("Reward | Red_exp",   "red"),
    ]

    records = []
    for field, color in flag_fields:
        for raw in normalize_list(row.get(field, [])):
            for mentor, raw_comment in _group_by_mentor(raw):
                records.append((mentor, color, raw_comment))
    return records

# === Pinta cada mentor y su lista de flags con puntuaciones
def render_flags_by_mentor(row):
    st.markdown("#### 🚩 EM's Feedback")

    mentor_scores = extract_mentor_scores(row)
    records = collect_flag_records(row)

    if not records:
        st.markdown("_No hay feedback para este startup._")
        return

    # Agrupar por mentor y color
    grouped = defaultdict(lambda: defaultdict(list))  # mentor → color → [raw_text]

    for mentor, color, raw_comment in records:
        grouped[mentor][color].append(raw_comment)

    color_to_emoji = {"green": "🟢", "yellow": "🟡", "red": "🔴"}

    for mentor in sorted(grouped):
        st.markdown(f"### 👤 **{mentor}**")
        scores = extract_mentor_scores(row).get(mentor, {})

        for color in ["red", "yellow", "green"]:
            comments = grouped[mentor].get(color, [])
            if not comments:
                continue

            emoji = color_to_emoji.get(color, "⚪️")
            st.markdown(f"{emoji} **{color.capitalize()} Flag**")

            # Agrupar y mostrar todo como lista
            all_formatted = []
            for comment in comments:
                formatted = _format_categories(comment, scores=scores)
                all_formatted.append(formatted)

            st.markdown("\n\n".join(all_formatted))
            st.markdown("---")

render_flags_by_mentor(row)

st.markdown("## 👤 Individual Human Metrics")

# -------------------------------------------------------------------
# 🧠 2) UNCONVENTIONAL THINKING  ─────────────────────────────────────
# -------------------------------------------------------------------

startup_ut_talks = normalize_list(row.get("Talks | Unconventional thinking (Founder & Score)", []))
talks_ut_list = [p.strip() for entry in startup_ut_talks for p in entry.split(", ")]  # tenemos nuestra lista de founder: tag

startup_ut_works = normalize_list(row.get("Workstations | Unconventional Thinking (Founder & Score)", []))
works_ut_list = [p.strip() for entry in startup_ut_works for p in entry.split(", ")]

startup_ut_ind = normalize_list(row.get("Individual Contest | Unconventional Thinking (Founder & Score)", []))
ind_ut_list = [p.strip() for entry in startup_ut_ind for p in entry.split(", ")]

list_ut = [talks_ut_list, works_ut_list, ind_ut_list]
#Vamos a contar cuantas de cada hay por founder
scores_count_ut = defaultdict(lambda: {"Bonus Star": 0, "Red Flag": 0})
for l in list_ut:
    for tag in l:
        nombre, score = tag.split(": ")
        nombre = nombre.strip()
        score = score.strip()
        if "Bonus" in score:
            scores_count_ut[nombre]["Bonus Star"] += 1
        elif "Red" in score:
            scores_count_ut[nombre]["Red Flag"] += 1

if scores_count_ut:
    st.subheader("🧠 Unconventional Thinking")
    for nombre in sorted(scores_count_ut):
        st.markdown(f"**{nombre}**")
        col_bonus, col_red = st.columns(2)
        col_bonus.metric("⭐ Bonus Star", int(scores_count_ut[nombre]["Bonus Star"]))
        col_red.metric("🚩 Red Flag",    int(scores_count_ut[nombre]["Red Flag"]))

# --------Ambition y Confidence (de Individual Contest)----------------------------

startup_conf = normalize_list(row.get("Individual Contest | Confidence (Founder & Score)", []))
ind_conf_list = [p.strip() for entry in startup_conf for p in entry.split(", ")]

startup_amb = normalize_list(row.get("Individual Contest | Ambition (Founder & Score)", []))
ind_amb_list = [p.strip() for entry in startup_amb for p in entry.split(", ")]

scores_count_conf = defaultdict(lambda: {"Bonus Star": 0, "Red Flag": 0})
scores_count_amb = defaultdict(lambda: {"Bonus Star": 0, "Red Flag": 0})

for tag in ind_conf_list:
    if ": " in tag:
        nombre, score = tag.split(": ")
        nombre = nombre.strip()
        score = score.strip()
        if "Bonus" in score:
            scores_count_conf[nombre]["Bonus Star"] += 1
        elif "Red" in score:
            scores_count_conf[nombre]["Red Flag"] += 1

for tag in ind_amb_list:
    if ": " in tag:
        nombre, score = tag.split(": ")
        nombre = nombre.strip()
        score = score.strip()
        if "Bonus" in score:
            scores_count_amb[nombre]["Bonus Star"] += 1
        elif "Red" in score:
            scores_count_amb[nombre]["Red Flag"] += 1

for title, score_dict in zip(["Confidence", "Ambition"], [scores_count_conf, scores_count_amb]):
    if score_dict:
        st.subheader(title)
        for nombre in sorted(score_dict):
            st.markdown(f"**{nombre}**")
            col_bonus, col_red = st.columns(2)
            col_bonus.metric("⭐ Bonus Star", int(score_dict[nombre]["Bonus Star"]))
            col_red.metric("🚩 Red Flag", int(score_dict[nombre]["Red Flag"]))

# ====Individual Human Metrics========================================================

st.markdown("""
**The following are the averages for the program and below the breakdown for the selected startup**
""")

individual_columns = [
    "Purpose | Average",
    "Openness | Average",
    "Integrity and honesty | Average",
    "Relevant experience | Average",
    "Visionary leadership | Average",
    "Flexibility | Average",
    "Emotional intelligence | Average"
]

cohort_ind_means = df[individual_columns].mean()

avg_cols_ind = st.columns(len(individual_columns))
for i, col in enumerate(individual_columns):
    pillar = col.split(" |")[0]
    avg_cols_ind[i].metric(pillar, f"{cohort_ind_means[col]:.2f}")

table_purp = normalize_list(row.get("Purpose | Founder & Score", []))
tags_purp = [p.strip() for entry in table_purp for p in entry.split(", ")]

table_open = normalize_list(row.get("Openness | Founder & Score", []))
tags_open = [p.strip() for entry in table_open for p in entry.split(", ")]

table_int = normalize_list(row.get("Integrity and honesty | Founder & Score", []))
tags_int = [p.strip() for entry in table_int for p in entry.split(", ")]

table_rel = normalize_list(row.get("Relevant experience | Founder & Score", []))
tags_rel = [p.strip() for entry in table_rel for p in entry.split(", ")]

table_vis = normalize_list(row.get("Visionary leadership | Founder & Score", []))
tags_vis = [p.strip() for entry in table_vis for p in entry.split(", ")]

table_flex = normalize_list(row.get("Flexibility | Founder & Score", []))
tags_flex = [p.strip() for entry in table_flex for p in entry.split(", ")]

table_emo = normalize_list(row.get("Emotional intelligence | Founder & Score", []))
tags_emo = [p.strip() for entry in table_emo for p in entry.split(", ")]

list_hum = [tags_purp, tags_open, tags_int, tags_rel, tags_vis, tags_flex, tags_emo]
campos_hum = ["Purpose", "Openness", "Integrity and honesty", "Relevant experience", "Visionary leadership", "Flexibility", "Emotional intelligence"]

rec_hum = defaultdict(lambda: defaultdict(list))

for i, lista in enumerate(list_hum):
    campo = campos_hum[i]
    for entrada in lista:
        if ": " in entrada:
            nombre, valor = entrada.split(": ")
            try:
                rec_hum[nombre.strip()][campo].append(float(valor.strip()))
            except ValueError:
                continue

df_hum = {}
for nombre, campos in rec_hum.items():
    rows = []
    for campo, valores in campos.items():
        if valores:
            media = sum(valores) / len(valores)
            rows.append({"Campo": campo, "Media": media})
    df_hum[nombre] = pd.DataFrame(rows)

i = 0
for nombre in sorted(df_hum):
    data = df_hum[nombre]
    if not data.empty:

            fig_ft = px.bar(
                data,
                x="Campo",
                y="Media",
                text="Media",
                barmode="group",
                title= f"{nombre}",
                color_discrete_sequence=["rgb(52, 199, 89)"],
                height=350,
            )

            fig_ft.update_traces(texttemplate='%{text:.2f}', textposition='outside')
            fig_ft.update_layout(
                yaxis_range=[1, 4],
                height=450,
                xaxis_tickangle=-45,
                margin=dict(t=50, b=0),
            )
            st.plotly_chart(fig_ft, use_container_width=True, key=f"fig_{i}")
            i += 1
    else:
        st.info(f"No feedback for individual metrics.")


# === Team Human Metrics =====================================================
st.markdown("## 👥 Team Human Metrics")
st.markdown("""
**The following are the averages for the program and below the breakdown for the selected startup**
""")

team_columns = [
    "Conflict resolution | Average",
    "Clear vision alignment | Average",
    "Clear roles | Average",
    "Complementary hard skills | Average",
    "Execution and speed | Average",
    "Team ambition | Average",
    "Confidence and mutual respect | Average",
    "Product and Customer Focus | Average",
]

# --- Scores for the chosen startup ------------------------------------------
startup_team_scores = {c.split(" |")[0]: row.get(c, 0) for c in team_columns}

# --- Cohort-wide averages ----------------------------------------------------
cohort_team_means = df[team_columns].mean()

# ── Show cohort averages as headline metrics ────────────────────────────────
avg_cols = st.columns(len(team_columns))
for i, col in enumerate(team_columns):
    pillar = col.split(" |")[0]
    avg_cols[i].metric(pillar, f"{cohort_team_means[col]:.2f}")

# ── Bar chart of the startup’s own scores ───────────────────────────────────
team_df = (
    pd.DataFrame({
        "Metric": list(startup_team_scores.keys()),
        "Score":  list(startup_team_scores.values()),
    })
)

fig_team = px.bar(
    team_df,
    x="Metric",
    y="Score",
    text="Score",
    color_discrete_sequence=["rgb(52, 199, 89)"],
)
fig_team.update_traces(texttemplate='%{text:.2f}', textposition='outside')
fig_team.update_layout(
    yaxis_range=[0, 4],
    height=450,
    xaxis_tickangle=-45,
    margin=dict(t=50, b=0),
)

st.plotly_chart(fig_team, use_container_width=True)

# =====Human Call Results Section========================================

st.markdown("## 👥 Human Call Results")

st.markdown("""
This section reflects qualitative human due diligence conducted through evaluator calls.  
It highlights how strong the founders are perceived to be based on expertise, clarity, execution ability, and leadership potential.
""")

# === Values from Airtable
hdd_avg = row.get("HDD_Calls_Average", "N/A")
hdd_exceptional = row.get("HDD_Calls_Exceptional", 0)
# Clean evaluator field
raw_evaluator = row.get("HDD_Calls_Evaluator", "Unknown")
hdd_evaluator = raw_evaluator[0] if isinstance(raw_evaluator, list) and raw_evaluator else raw_evaluator
# Clean notes field
raw_notes = row.get("HDD_Calls_Notes", "No notes provided.")
hdd_notes = raw_notes[0] if isinstance(raw_notes, list) and raw_notes else raw_notes

# === Score and Exceptional Tag
col1, col2 = st.columns(2)
col1.metric("Average HDD Score -- Out of 4", round(hdd_avg, 2) if pd.notna(hdd_avg) else "N/A")
col2.metric("Exceptional Founders", "✅ Yes" if hdd_exceptional == 1 else "❌ No")

# === Evaluator
st.markdown(f"**Evaluator:** {hdd_evaluator}")

# === Notes
st.markdown("**📝 Notes from the call:**")
st.info(hdd_notes)

st.markdown("### 🧪 Scientific Analysis Results")

# === BRS – Brief Resilience Scale
st.markdown("""
**1. BRS – Brief Resilience Scale**  
*Purpose:* Measures the ability to recover or "bounce back" from stress.  
*Interpretation:* A high score indicates strong resilience, meaning the person is capable of quickly recovering from emotional setbacks.
""")

raw_calc = row.get("BRS_Calculation", "No interpretation provided.")
brs_interpretation = raw_calc[0] if isinstance(raw_calc, list) and raw_calc else raw_calc
st.success(f"**Conclusion:** {brs_interpretation}")


# === GRIT Scale
st.markdown("""
**2. GRIT Scale**  
*Purpose:* Assesses perseverance and passion for long-term goals.  
*Interpretation:* A high GRIT score reflects consistency in interests and sustained effort over time, even in the face of setbacks.
""")

raw_grit_calc = row.get("GRIT_Calculation", "No interpretation provided.")
grit_interpretation = raw_grit_calc[0] if isinstance(raw_grit_calc, list) and raw_grit_calc else raw_grit_calc
st.success(f"**Conclusion:** {grit_interpretation}")


st.markdown("""
**3. OLBI – Oldenburg Burnout Inventory**  
*Purpose:* Evaluates two core dimensions of burnout — **exhaustion** and **disengagement** from work.  
*Interpretation:* Helps identify early signs of burnout. High scores on either dimension could indicate emotional fatigue or withdrawal from work tasks.
""")

# Extract descriptors
raw_olbi_exhaust = row.get("OLBI_Exhaustion_Descriptor", "No result")
olbi_exhaust = raw_olbi_exhaust[0] if isinstance(raw_olbi_exhaust, list) and raw_olbi_exhaust else raw_olbi_exhaust

raw_olbi_disengage = row.get("OLBI_Disengagement_Descriptor", "No result")
olbi_disengage = raw_olbi_disengage[0] if isinstance(raw_olbi_disengage, list) and raw_olbi_disengage else raw_olbi_disengage

# Combine into a single block with icons
def flag_color(text):
    if isinstance(text, str):
        text = text.lower()
        if "high" in text:
            return "🔴"
        elif "moderate" in text:
            return "🟡"
        elif "low" in text:
            return "🟢"
    return "⚪️"

olbi_summary = f"""
**Exhaustion:** {flag_color(olbi_exhaust)} {olbi_exhaust}  
**Disengagement:** {flag_color(olbi_disengage)} {olbi_disengage}
"""
st.success(olbi_summary)

# ------------------------------------------------------------------
# 📄  FULL-PAGE “Save as PDF” button – paste at bottom of app.py
# ------------------------------------------------------------------
st.markdown("""
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>

    <style>
        #savepdf {
            background-color: #0b6abf;
            color: white;
            padding: 0.6rem 1.2rem;
            font-size: 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            margin-top: 30px;
        }
    </style>

    <button id="savepdf">⬇️ Descargar esta página en PDF</button>

    <script>
    const { jsPDF } = window.jspdf;

    document.getElementById("savepdf").addEventListener("click", function () {
        const body = document.body;
        html2canvas(body, { scale: 2, useCORS: true }).then(canvas => {
            const imgData = canvas.toDataURL('image/png');
            const pdf = new jsPDF('p', 'mm', 'a4');
            const pageWidth = pdf.internal.pageSize.getWidth();
            const pageHeight = pdf.internal.pageSize.getHeight();
            const imgHeight = canvas.height * pageWidth / canvas.width;

            let heightLeft = imgHeight;
            let position = 0;

            pdf.addImage(imgData, 'PNG', 0, position, pageWidth, imgHeight);
            heightLeft -= pageHeight;

            while (heightLeft > 0) {
                position -= pageHeight;
                pdf.addPage();
                pdf.addImage(imgData, 'PNG', 0, position, pageWidth, imgHeight);
                heightLeft -= pageHeight;
            }

            pdf.save("feedback-decelera.pdf");
        });
    });
    </script>
""", unsafe_allow_html=True)
