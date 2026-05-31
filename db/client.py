# db/client.py
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def get_supabase() -> Client:
    """
    Retorna o cliente Supabase.
    @cache_resource garante uma única conexão por sessão do Streamlit.
    """
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)
