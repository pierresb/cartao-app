--- a/app.py
+++ b/app.py
@@ -1,12 +1,12 @@
 # -*- coding: utf-8 -*-
 import os
 import json
 import base64
 import sqlite3
 from datetime import datetime
 from io import BytesIO
 
 import pandas as pd
 import streamlit as st
 
 # =========================
 # Configuração do app
 # =========================
 st.set_page_config(
-    page_title="Solicitação de Cartão Empresarial",
-    page_icon="💳",
+    page_title="Solicitação de Cartão Empresarial",
+    page_icon="💳",  # opcional: "assets/caixa_logo.png"
     layout="wide"
 )
 
-PRIMARY = "#005CA9"  # Azul
-ACCENT = "#F39200"   # Laranja
-
-st.markdown(
-    f"""
-    <style>
-      .title h1 {{ color: {PRIMARY}; }}
-      .step {{ background: #f8fafc; border: 1px solid #e6ecf2; padding: 1rem; border-radius: 0.5rem; }}
-      .ok    {{ color: #1b8a5a; }}
-      .warn  {{ color: #b65c00; }}
-      .bad   {{ color: #b00020; }}
-      .tag   {{ background:#eef3fb; color:{PRIMARY}; padding:.15rem .5rem; border-radius:.4rem; font-size:.82rem; }}
-    </style>
-    """,
-    unsafe_allow_html=True
-)
+########################################
+# Branding CAIXA: cores, header e CSS  #
+########################################
+CAIXA_BLUE   = "#005CA9"
+CAIXA_ORANGE = "#F39200"
+CAIXA_BG     = "#F4F7FC"
+
+# Cabeçalho com logo e selo "Demo"
+left, right = st.columns([1, 5], vertical_alignment="center")
+with left:
+    try:
+        st.image("assets/caixa_logo.png", width=140)
+    except Exception:
+        st.markdown(f"<div style='color:{CAIXA_BLUE};font-weight:700'>CAIXA</div>", unsafe_allow_html=True)
+with right:
+    st.markdown(
+        f"""
+        <div style="display:flex; align-items:center; gap:.75rem; margin-top:.25rem;">
+          <h1 style="margin:0; color:{CAIXA_BLUE};">Solicitação de Cartão de Crédito Empresarial</h1>
+          <span style="background:{CAIXA_BG}; color:{CAIXA_BLUE}; padding:.2rem .6rem; border-radius:.5rem; font-size:.9rem; border:1px solid #E2E8F0;">Demo</span>
+        </div>
+        """,
+        unsafe_allow_html=True
+    )
+
+# Tipografia e detalhes de UI
+st.markdown(
+    f"""
+    <style>
+      @import url('https://fonts.googleapis.com/css2?family=Montserrat:wght@400;600;700&display=swap');
+      html, body, [class*="css"] {{
+        font-family: 'Montserrat', system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial !important;
+      }}
+      .stTabs [data-baseweb="tab-list"] button {{ font-weight: 600; }}
+      .stButton>button {{
+        border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 1px 2px rgba(0,0,0,.04);
+      }}
+      .stButton>button:hover {{ border-color: {CAIXA_BLUE}; }}
+      [data-testid="stMetricValue"] {{ color: {CAIXA_BLUE} !important; font-weight: 700 !important; }}
+      .ok   {{ color: #1b8a5a; font-weight:600; }}
+      .warn {{ color: #b65c00; font-weight:600; }}
+      .bad  {{ color: #b00020; font-weight:600; }}
+      .tag {{
+        background: {CAIXA_BG}; color: {CAIXA_BLUE};
+        padding: .2rem .6rem; border-radius: .5rem; font-size: .85rem; border: 1px solid #E2E8F0;
+      }}
+      /* Sidebar com faixa azul */
+      section[data-testid="stSidebar"] > div:first-child {{
+        background: linear-gradient(180deg, {CAIXA_BLUE} 0%, #014a87 100%); color: white;
+      }}
+      section[data-testid="stSidebar"] h2, 
+      section[data-testid="stSidebar"] p, 
+      section[data-testid="stSidebar"] label {{
+        color: white !important;
+      }}
+      /* Foco em inputs */
+      input:focus, textarea:focus, select:focus {{
+        outline: none !important;
+        box-shadow: 0 0 0 3px rgba(0,92,169,.2) !important;
+        border-color: {CAIXA_BLUE} !important;
+      }}
+      a {{ color: {CAIXA_BLUE}; text-decoration: none; }}
+      a:hover {{ text-decoration: underline; }}
+    </style>
+    """,
+    unsafe_allow_html=True
+)
 
 # =========================
 # Utilidades
 # =========================
@@ -120,20 +120,20 @@
 # =========================
 # Sidebar
 # =========================
 with st.sidebar:
-    st.markdown("## 💳 Cartão Empresarial")
-    st.write("Preencha os dados para enviar sua solicitação. Os campos marcados com * são obrigatórios.")
-    st.markdown("---")
-    admin_view = st.toggle("🔐 Modo administrador (lista de solicitações)")
-    st.caption("Este app é demonstrativo. Nenhum crédito é concedido automaticamente.")
+    st.markdown("## 💳 Cartão Empresarial")
+    st.caption("Preencha os dados para enviar sua solicitação. Campos * são obrigatórios.")
+    admin_view = st.toggle("🔐 Modo administrador (lista de solicitações)")
+    st.markdown("---")
+    st.markdown(f"<span class='tag'>Identidade visual Caixa</span>", unsafe_allow_html=True)
 
 # =========================
 # Título
 # =========================
-st.markdown('<div class="title"><h1>Solicitação de Cartão de Crédito Empresarial</h1></div>', unsafe_allow_html=True)
-st.markdown(f'<span class="tag">Demo • Streamlit</span>', unsafe_allow_html=True)
-st.write("")
+# (título já renderizado no cabeçalho com logo)
+# Tag extra opcional:
+# st.markdown(f'<span class="tag">Demo • Streamlit</span>', unsafe_allow_html=True)
+# st.write("")