import streamlit as st
import pandas as pd
import os

csv_file_path = 'dados_leads.csv'

def mostrar_relatorio():
    if "senha_validada" not in st.session_state:
        st.session_state.senha_validada = False

    if not st.session_state.senha_validada:
        senha = st.text_input("Digite a senha para acessar os dados:", type="password")

        if st.button("Acessar"):
            if senha == PASSWORD:
                st.session_state.senha_validada = True
                st.rerun() 
            else:
                st.error("Senha incorreta. Tente novamente.")
    else:
        try:
            df = pd.read_csv(csv_file_path)
            
            if df.empty:
                st.warning("O arquivo está vazio. Nenhum dado disponível.")
                return
            
            df.columns = ['Agente Comercial','Lead', 'Razão Social', 'Nome Fantasia', 'E-mail', 'Telefone', 'CNPJ', 'Nº de Cobranças', 'Comentários']
            
            st.write("📌 **Dados dos Leads Registrados:**")
            st.dataframe(df)

            csv_download = df.to_csv(index=False).encode('utf-8-sig')
            st.download_button(
                label="📥 Baixar CSV",
                data=csv_download,
                file_name="dados_leads.csv",
                mime="text/csv"
            )

        except FileNotFoundError:
            st.error("⚠️ Arquivo de dados não encontrado. Nenhum lead registrado.")
        except pd.errors.EmptyDataError:
            st.warning("⚠️ O arquivo está vazio. Nenhum dado disponível.")
        except Exception as e:
            st.error(f"❌ Ocorreu um erro ao carregar os dados: {e}")

st.title("📊 Relatório de Leads")
mostrar_relatorio()
