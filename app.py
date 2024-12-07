import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
import pandas as pd
from datetime import timedelta

# Função para carregar as credenciais
def load_credentials():
    return {
        "type": "service_account",
        "project_id": st.secrets["general"]["PROJECT_ID"],
        "private_key_id": st.secrets["general"]["PRIVATE_KEY_ID"],
        "private_key": st.secrets["general"]["PRIVATE_KEY"],
        "client_email": st.secrets["general"]["CLIENT_EMAIL"],
        "client_id": st.secrets["general"]["CLIENT_ID"],
        "auth_uri": "https://accounts.google.com/o/oauth2/auth",
        "token_uri": "https://oauth2.googleapis.com/token",
        "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
        "client_x509_cert_url": st.secrets["general"]["CLIENT_X509_CERT_URL"],
    }

# Conexão com Google Sheets
def connect_to_gsheet(sheet_name: str, credentials: dict):
    try:
        creds = Credentials.from_service_account_info(
            credentials,
            scopes=[
                "https://www.googleapis.com/auth/spreadsheets",
                "https://www.googleapis.com/auth/drive",
            ]
        )
        client = gspread.authorize(creds)
        sheet = client.open(sheet_name).sheet1
        verify_columns(sheet)
        return sheet
    except Exception as e:
        raise RuntimeError("Erro de conexão")

# Verificar e criar colunas necessárias
def verify_columns(sheet):
    required_columns = ["Data", "Distância (km)", "Tempo", "Peso (kg)", "Pace"]
    existing_columns = sheet.row_values(1)
    if existing_columns != required_columns:
        sheet.clear()
        sheet.append_row(required_columns)

# Carregar dados da planilha
def load_sheet_data(sheet):
    try:
        data = sheet.get_all_records()
        return pd.DataFrame(data)
    except Exception as e:
        raise RuntimeError(f"Erro ao carregar os dados: {e}")

# Inserir dados no Google Sheets
def insert_data(sheet, data):
    try:
        sheet.append_row(data)
    except Exception as e:
        raise RuntimeError(f"Erro ao inserir os dados: {e}")

# Função para calcular pace (ritmo) em min/km
def calcular_pace(tempo: timedelta, distancia: float):
    if distancia > 0:
        total_minutes = tempo.total_seconds() / 60
        pace = total_minutes / distancia
        minutos = int(pace)
        segundos = int((pace - minutos) * 60)
        return f"{minutos}:{segundos:02d}"
    return "0:00"

# Configuração da página do Streamlit
st.title("Planilha de Desempenho de Corrida")

# Conexão com a planilha
sheet_name = "Performace"
try:
    sheet = connect_to_gsheet(sheet_name, load_credentials())
except Exception as e:
    st.error(f"Erro ao conectar à planilha: {e}")
    st.stop()

# Formulário para registrar dados da corrida
with st.form("form_corrida"):
    data = st.date_input("Data")
    distancia = st.number_input("Distância (km)", min_value=0.0, format="%.2f")
    horas = st.number_input("Horas", min_value=0, step=1)
    minutos = st.number_input("Minutos", min_value=0, max_value=59, step=1)
    segundos = st.number_input("Segundos", min_value=0, max_value=59, step=1)
    peso = st.number_input("Peso (kg)", min_value=0.0, format="%.1f")
    submit = st.form_submit_button("Registrar Corrida")

# Inserir dados no Google Sheets se o formulário for enviado
if submit:
    try:
        tempo = timedelta(hours=horas, minutes=minutos, seconds=segundos)
        pace = calcular_pace(tempo, distancia)
        insert_data(sheet, [str(data), distancia, str(tempo), peso, pace])
        st.success("Dados registrados com sucesso!")
    except Exception as e:
        st.error(f"Erro ao registrar os dados: {e}")

# Exibir dados registrados
st.subheader("Histórico de Corridas")
try:
    df = load_sheet_data(sheet)
    st.dataframe(df)
except Exception as e:
    st.error(f"Erro ao carregar os dados: {e}")
