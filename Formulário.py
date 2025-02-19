import streamlit as st
import requests
import re
import time
import csv
import os
from bs4 import BeautifulSoup

st.set_page_config(
    page_title="Registro de Leads",
    page_icon="assets/favicon.ico",
    layout="centered",
    initial_sidebar_state="expanded"
)

GOOGLE_API_KEY = st.secrets["google_api_key"]
CX = st.secrets["cx"]
SERPAPI_KEY = st.secrets["serpapi_key"]

csv_file_path = 'dados_leads.csv'

def buscar_cnpj(nome_empresa):
    query = f"{nome_empresa} CNPJ"
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "q": query,
        "key": GOOGLE_API_KEY,
        "cx": CX,
        "num": 3
    }
    
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        if "items" in data:
            for item in data["items"]:
                snippet = item.get("snippet", "")
                match = re.search(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', snippet)
                if match:
                    return match.group(0)  
    except requests.RequestException as e:
        print(f"Erro ao buscar CNPJ (Google API): {e}")
    
    return None  

def buscar_cnpj_serpapi(nome_empresa):
    url = "https://serpapi.com/search"
    params = {
        "q": f"{nome_empresa} CNPJ",
        "engine": "google",
        "api_key": SERPAPI_KEY,
        "num": 3
    }

    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()

        if "organic_results" in data:
            for result in data["organic_results"]:
                snippet = result.get("snippet", "")
                match = re.search(r'\b\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}\b', snippet)
                if match:
                    return match.group(0)
    except requests.RequestException as e:
        print(f"Erro ao buscar CNPJ (SerpApi): {e}")
    
    return None  

def buscar_informacoes_cnpj(cnpj):
    cnpj_cleaned = re.sub(r'\D', '', cnpj)
    url = f"https://www.receitaws.com.br/v1/cnpj/{cnpj_cleaned}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        if data.get("status") == "ERROR":
            return None
        return {
            'Razão Social': data.get('nome', 'Não encontrado'),  
            'Nome Fantasia': data.get('fantasia', 'Não encontrado'),
            'E-mail': data.get('email', 'Não encontrado'),
            'Telefone': data.get('telefone', 'Não encontrado'),
        }
    except requests.RequestException:
        return None

def salvar_dados_csv(dados):
    colunas = ['Lead', 'Razão Social', 'Nome Fantasia', 'E-mail', 'Telefone', 'CNPJ', 'Número de Cobranças', 'Mensagem']
    arquivo_existe = os.path.isfile(csv_file_path)
    with open(csv_file_path, mode='a', newline='', encoding='utf-8-sig') as file:
        writer = csv.writer(file, delimiter=',')
        if not arquivo_existe:
            writer.writerow(colunas)
        writer.writerow(dados)

st.image("assets/header.png", use_column_width=True)
st.title("Registro de Leads para contato")

lead = st.text_input("Insira o Lead:", value=st.session_state.get('lead', ''))
nome_empresa = st.text_input("Insira o nome da empresa:", value=st.session_state.get('nome_empresa', ''))

if st.button("Buscar Informações"):
    if nome_empresa:
        with st.spinner("Buscando informações..."):
            cnpj = buscar_cnpj(nome_empresa)
            if not cnpj:
                st.write("CNPJ não encontrado pelo Google. Tentando via SerpApi...")
                cnpj = buscar_cnpj_serpapi(nome_empresa)
            
            if cnpj:
                st.session_state.cnpj = cnpj
                informacoes = buscar_informacoes_cnpj(cnpj)
                st.session_state.informacoes = informacoes or {}
                if informacoes:
                    st.write("CNPJ encontrado:", cnpj)
                    st.write("Razão Social:", informacoes.get('Razão Social', 'Não encontrado'))
                    st.write("Nome Fantasia:", informacoes.get('Nome Fantasia', 'Não encontrado'))
                    st.write("E-mail:", informacoes.get('E-mail', 'Não encontrado'))
                    st.write("Telefone:", informacoes.get('Telefone', 'Não encontrado'))
                else:
                    st.write("Não foi possível obter informações adicionais.")
            else:
                st.write("CNPJ não encontrado em nenhuma fonte.")
    else:
        st.write("Por favor, insira um nome de empresa.")

if "informacoes" in st.session_state and st.session_state.informacoes:
    novo_email = st.text_input("Alterar Email:", value=st.session_state.informacoes.get('E-mail', ''))
    novo_telefone = st.text_input("Alterar Telefone:", value=st.session_state.informacoes.get('Telefone', ''))
    novo_cnpj = st.text_input("Alterar CNPJ:", value=st.session_state.get('cnpj', ''))
    nome_fantasia = st.text_input("Alterar Nome Fantasia:", value=st.session_state.informacoes.get('Nome Fantasia', ''))
    razao_social = st.text_input("Alterar Razão Social:", value=st.session_state.informacoes.get('Razão Social', ''))
    numero_cobrancas = st.text_input("(opcional) | Número de cobranças emitidas por mês:", value=st.session_state.get('numero_cobrancas', ''))
    mensagem = st.text_area("(opcional) | Mensagem:", value=st.session_state.get('mensagem', ''))
    agente_comercial = st.text_input("Agente Comercial:", value=st.session_state.get('agente_comercial', ''))


    if st.button("Salvar"):
        if not novo_email or not novo_telefone or not novo_cnpj or not nome_fantasia or not razao_social or not agente_comercial:
            st.warning("Todos os campos obrigatórios devem ser preenchidos!")
        else:
            st.session_state.agente_comercial = agente_comercial
            st.session_state.lead = lead
            st.session_state.nome_empresa = nome_empresa
            st.session_state.numero_cobrancas = numero_cobrancas
            st.session_state.mensagem = mensagem
            st.session_state.cnpj = novo_cnpj
            st.session_state.salvo = True

            dados = [
                agente_comercial,
                lead,
                razao_social, 
                nome_fantasia,
                novo_email,
                novo_telefone,
                novo_cnpj,
                numero_cobrancas,
                mensagem
            ]
            
            salvar_dados_csv(dados)

            sucesso_msg = (
                "*✔️ Dados salvos com sucesso!*\n"
                f"- *Lead:* {lead}\n"
                f"- *Razão Social:* {razao_social}\n"
                f"- *Nome Fantasia:* {nome_fantasia}\n"
                f"- *E-mail:* {novo_email}\n"
                f"- *Telefone:* {novo_telefone}\n"
                f"- *CNPJ:* {novo_cnpj}\n"
                f"- *Número de Cobranças:* {numero_cobrancas}\n"
                f"- *Mensagem:* {mensagem}\n"
                f"- *Agente Comercial:* {agente_comercial}"
            )
            st.success(sucesso_msg)
            
            st.session_state.lead = " "
            st.session_state.nome_empresa = " "
            st.session_state.numero_cobrancas = " "
            st.session_state.mensagem = " "
            st.session_state.informacoes = {}
            st.session_state.cnpj = " "
            st.session_state.agente_comercial = " "
            st.session_state.salvo = False 

            time.sleep(3)
            st.rerun()