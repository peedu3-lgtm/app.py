import streamlit as st
from fpdf import FPDF
import datetime
import requests
import pytz

# --- KONSTANDID JA ANDMED ---
MAAKONNAD = {
    "Harjumaa": (59.33, 24.75), "Tartumaa": (58.37, 26.72), "Pärnumaa": (58.38, 24.50),
    "Ida-Virumaa": (59.35, 27.41), "Saaremaa": (58.25, 22.48), "Viljandimaa": (58.36, 25.59)
}

# --- FUNKTSIOONID ---
def get_eesti_aeg():
    try:
        eesti_tz = pytz.timezone('Europe/Tallinn')
        return datetime.datetime.now(eesti_tz).strftime("%H:%M")
    except: return datetime.datetime.now().strftime("%H:%M")

def get_weather(lat, lon):
    try:
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,wind_speed_10m&wind_speed_unit=ms"
        response = requests.get(url, timeout=3)
        data = response.json()
        return round(data['current']['wind_speed_10m'], 1), f"{data['current']['temperature_2m']}°C"
    except: return 0.0, "N/A"

# --- UI ALGUS ---
st.set_page_config(page_title="ISA Puu Riski Hindamine", layout="wide")
st.title("🌳 Puu riski hindamise vorm (ISA v7.1)")

# 1. ÜLDINFO
st.header("1. Üldandmed")
c1, c2 = st.columns(2)
with c1:
    hindaja = st.text_input("Hindaja nimi", value="")
    klient = st.text_input("Klient / Omanik", value="")
    aadress = st.text_input("Puu asukoht / Aadress", "")
with c2:
    maakond = st.selectbox("Maakond (ilmateade)", list(MAAKONNAD.keys()))
    lat, lon = MAAKONNAD[maakond]
    tuul, temp = get_weather(lat, lon)
    st.write(f"Hetkeilm: {temp}, tuul {tuul} m/s")
    hindamisperiood = st.text_input("Hindamisperiood (nt 2 aastat)", "2 aastat")

st.divider()

# 2. PUU ANDMED
st.header("2. Puu spetsifikatsioon")
c3, c4, c5 = st.columns(3)
with c3:
    liik = st.text_input("Puu liik")
with c4:
    dbh = st.number_input("Tüve läbimõõt (DBH cm)", min_value=0)
with c5:
    korgus = st.number_input("Kõrgus (m)", min_value=0)

# 3. SIHTMÄRGID (TARGETS)
st.header("3. Sihtmärgid ja ohuala")
c6, c7 = st.columns(2)
with c6:
    target_desc = st.text_area("Sihtmärgi kirjeldus", placeholder="Inimesed kergteel, naabri katus, parkla jne.")
with c7:
    occupancy = st.selectbox("Viibimise sagedus", ["Harv", "Aeg-ajalt", "Sage", "Pidev"])
    ohuala = korgus * 1.5
    st.info(f"Soovituslik ohuala raadius: {ohuala} m")

st.divider()

# 4. PUU SEISUNDI ANALÜÜS
st.header("4. Puu osade vaatlus")
tabs = st.tabs(["Võra", "Tüvi", "Juured & Pinnas"])

with tabs[0]:
    v_tervis = st.selectbox("Puu tervis", ["Surnud", "Halb", "Rahuldav", "Hea"])
    v_vead = st.multiselect("Võra vead", ["Surnud oksad", "Murrunud oksad", "Ebatasakaal", "Latv kuivab", "Liigne mass okstel"])
    v_markused = st.text_area("Võra märkused")

with tabs[1]:
    t_vead = st.multiselect("Tüve vead", ["Mädanik/seened", "Praod", "Koor puudu", "Õõnsused", "Kalle", "Varasemad haru murrud"])
    t_kalle = st.checkbox("Kalle on korrigeeritud (puu on hakanud otse kasvama)")
    t_markused = st.text_area("Tüve märkused")

with tabs[2]:
    j_vead = st.multiselect("Juurestiku vead", ["Juurekael maetud", "Seened/mädanik", "Juured läbi lõigatud", "Pinnas tõusnud", "Piiratud kasvuala"])
    j_markused = st.text_area("Juurestiku märkused")

st.divider()

# 5. RISKI MAATRIKS (Vormi 2. leht)
st.header("5. Riski hindamine (ISA Maatriks)")
st.write("Vali tõenäosus ja tagajärjed vastavalt ISA standardile.")

c8, c9, c10 = st.columns(3)
with c8:
    l_failure = st.selectbox("Murdumise tõenäosus", ["Ebatõenäoline", "Võimalik", "Tõenäoline", "Vältimatu"])
with c9:
    l_impact = st.selectbox("Sihtmärgile pihtasaamise tõenäosus", ["Väga väike", "Väike", "Keskmine", "Suur"])
with c10:
    consequence = st.selectbox("Tagajärjed", ["Tühised", "Väikesed", "Olulised", "Rasked"])

# Lihtsustatud riskikalkulatsioon (näitlik)
risk_score = "MADAL"
if l_failure in ["Tõenäoline", "Vältimatu"] and consequence in ["Olulised", "Rasked"]:
    risk_score = "KÕRGE / EXTREME"
elif l_failure == "Võimalik" or consequence == "Olulised":
    risk_score = "KESKMINE"

st.subheader(f"Lõplik riskitase: {risk_score}")

# 6. LEEVENDAMINE
st.header("6. Soovitused ja leevendamine")
mitigation = st.text_area("Vajalikud tööd riski vähendamiseks", placeholder="Hoolduslõikus, ladva kergendamine, raie jne.")

# PDF GENEREERIMINE
def create_pdf():
    pdf = FPDF()
    pdf.add_page()
    def enc(txt): return str(txt).encode('latin-1', 'replace').decode('latin-1')
    
    pdf.set_font("helvetica", 'B', 16)
    pdf.cell(0, 10, enc("PUU RISKI HINDAMISE ARUANNE (ISA)"), ln=True, align='C')
    pdf.ln(10)
    
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, enc(f"Aadress: {aadress}"), ln=True)
    pdf.cell(0, 10, enc(f"Liik: {liik} | DBH: {dbh} cm | Korgus: {korgus} m"), ln=True)
    pdf.cell(0, 10, enc(f"Hindaja: {hindaja} | Kuupaev: {datetime.date.today()}"), ln=True)
    pdf.ln(5)
    
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, enc("Riski hinnang:"), ln=True)
    pdf.set_font("helvetica", '', 12)
    pdf.cell(0, 10, enc(f"Murdumise toenäosus: {l_failure}"), ln=True)
    pdf.cell(0, 10, enc(f"Tagajärjed: {consequence}"), ln=True)
    pdf.set_font("helvetica", 'B', 14)
    pdf.cell(0, 10, enc(f"LOPLIK RISKITAŠE: {risk_score}"), ln=True)
    
    pdf.ln(5)
    pdf.set_font("helvetica", 'B', 12)
    pdf.cell(0, 10, enc("Soovitused:"), ln=True)
    pdf.set_font("helvetica", '', 12)
    pdf.multi_cell(0, 7, enc(mitigation))
    
    return pdf.output()

if st.button("🚀 Genereeri ISA standardi PDF"):
    pdf_out = create_pdf()
    st.download_button("Laadi aruanne alla", bytes(pdf_out), "Puu_Riskianalyys.pdf", "application/pdf")
