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
    page_title="Solicitação de Cartão Empresarial",
    page_icon="💳",
    layout="wide"
)

PRIMARY = "#005CA9"  # Azul
ACCENT = "#F39200"   # Laranja

st.markdown(
    f"""
    <style>
      .title h1 {{ color: {PRIMARY}; }}
      .step {{ background: #f8fafc; border: 1px solid #e6ecf2; padding: 1rem; border-radius: 0.5rem; }}
      .ok    {{ color: #1b8a5a; }}
      .warn  {{ color: #b65c00; }}
      .bad   {{ color: #b00020; }}
      .tag   {{ background:#eef3fb; color:{PRIMARY}; padding:.15rem .5rem; border-radius:.4rem; font-size:.82rem; }}
    </style>
    """,
    unsafe_allow_html=True
)

# =========================
# Utilidades
# =========================
DB_PATH = "data/db.sqlite3"
UPLOAD_DIR = "uploads"

os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
os.makedirs(UPLOAD_DIR, exist_ok=True)

def init_db():
    with sqlite3.connect(DB_PATH) as cx:
        cx.execute("""
            CREATE TABLE IF NOT EXISTS solicitacoes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                criado_em TEXT NOT NULL,
                empresa_razao_social TEXT,
                empresa_nome_fantasia TEXT,
                cnpj TEXT,
                ramo_atividade TEXT,
                faturamento_mensal REAL,
                qntd_funcionarios INTEGER,
                contato_nome TEXT,
                contato_email TEXT,
                contato_telefone TEXT,
                contato_cpf TEXT,
                limite_pretendido REAL,
                qtde_cartoes INTEGER,
                vencimento_fatura INTEGER,
                adesao_pontos INTEGER,
                participa_credenciamento INTEGER,
                aceitar_termos INTEGER,
                status TEXT DEFAULT 'Recebida',
                dados_json TEXT
            )
        """)
        cx.commit()

def only_digits(s: str) -> str:
    return "".join(ch for ch in s if ch.isdigit())

def valida_cpf(cpf: str) -> bool:
    cpf = only_digits(cpf)
    if len(cpf) != 11 or cpf == cpf[0] * 11:
        return False
    def dv(c, w):
        s = sum(int(c[i]) * w[i] for i in range(len(w)))
        r = (s * 10) % 11
        return 0 if r == 10 else r
    d1 = dv(cpf, list(range(10,1,-1)))
    d2 = dv(cpf, list(range(11,2,-1)))
    return d1 == int(cpf[9]) and d2 == int(cpf[10])

def valida_cnpj(cnpj: str) -> bool:
    cnpj = only_digits(cnpj)
    if len(cnpj) != 14 or cnpj == cnpj[0] * 14:
        return False
    pesos1 = [5,4,3,2,9,8,7,6,5,4,3,2]
    pesos2 = [6] + pesos1
    def calc(c, p):
        s = sum(int(x)*y for x,y in zip(c, p))
        r = s % 11
        return '0' if r < 2 else str(11-r)
    d1 = calc(cnpj[:12], pesos1)
    d2 = calc(cnpj[:12]+d1, pesos2)
    return cnpj[-2:] == d1 + d2

def to_money(v):
    if v is None or v == "":
        return ""
    try:
        return f"R$ {float(v):,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    except:
        return str(v)

def make_receipt(payload: dict) -> bytes:
    """Gera um 'comprovante' simples em PDF-like (na prática, um TXT bonito) para download."""
    txt = []
    txt.append("COMPROVANTE DE SOLICITAÇÃO - CARTÃO DE CRÉDITO EMPRESARIAL")
    txt.append("-" * 66)
    for k, v in payload.items():
        if isinstance(v, (dict, list)):
            v = json.dumps(v, ensure_ascii=False)
        txt.append(f"{k}: {v}")
    txt.append("-" * 66)
    return "\n".join(txt).encode("utf-8")

def save_file(uploaded, prefix=""):
    if not uploaded:
        return None
    name = f"{prefix}{datetime.now().strftime('%Y%m%d%H%M%S')}_{uploaded.name}"
    path = os.path.join(UPLOAD_DIR, name)
    with open(path, "wb") as f:
        f.write(uploaded.read())
    return path

def salvar_solicitacao(payload: dict) -> int:
    with sqlite3.connect(DB_PATH) as cx:
        cur = cx.cursor()
        cur.execute("""
            INSERT INTO solicitacoes(
                criado_em, empresa_razao_social, empresa_nome_fantasia, cnpj, ramo_atividade,
                faturamento_mensal, qntd_funcionarios, contato_nome, contato_email, contato_telefone,
                contato_cpf, limite_pretendido, qtde_cartoes, vencimento_fatura, adesao_pontos,
                participa_credenciamento, aceitar_termos, status, dados_json
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            datetime.now().isoformat(timespec="seconds"),
            payload["empresa"]["razao_social"],
            payload["empresa"]["nome_fantasia"],
            only_digits(payload["empresa"]["cnpj"]),
            payload["empresa"]["ramo"],
            float(payload["empresa"]["faturamento_mensal"]) if payload["empresa"]["faturamento_mensal"] else None,
            int(payload["empresa"]["qtd_func"]) if payload["empresa"]["qtd_func"] else None,
            payload["responsavel"]["nome"],
            payload["responsavel"]["email"],
            payload["responsavel"]["telefone"],
            only_digits(payload["responsavel"]["cpf"]),
            float(payload["solicitacao"]["limite"]) if payload["solicitacao"]["limite"] else None,
            int(payload["solicitacao"]["qtde_cartoes"]) if payload["solicitacao"]["qtde_cartoes"] else None,
            int(payload["solicitacao"]["vencimento"]),
            1 if payload["solicitacao"]["adesao_pontos"] else 0,
            1 if payload["solicitacao"]["participa_credenciamento"] else 0,
            1 if payload["consentimento"]["aceite"] else 0,
            payload.get("status", "Recebida"),
            json.dumps(payload, ensure_ascii=False)
        ))
        cx.commit()
        return cur.lastrowid

def listar_solicitacoes() -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as cx:
        df = pd.read_sql_query("""
            SELECT
              id as Protocolo,
              datetime(criado_em) as CriadoEm,
              empresa_razao_social as RazaoSocial,
              cnpj as CNPJ,
              contato_nome as Contato,
              contato_email as Email,
              limite_pretendido as LimitePretendido,
              status as Status
            FROM solicitacoes
            ORDER BY id DESC
        """, cx)
    return df

# =========================
# Inicia DB
# =========================
init_db()

# =========================
# Sidebar
# =========================
with st.sidebar:
    st.markdown("## 💳 Cartão Empresarial")
    st.write("Preencha os dados para enviar sua solicitação. Os campos marcados com * são obrigatórios.")
    st.markdown("---")
    admin_view = st.toggle("🔐 Modo administrador (lista de solicitações)")
    st.caption("Este app é demonstrativo. Nenhum crédito é concedido automaticamente.")

# =========================
# Título
# =========================
st.markdown('<div class="title"><h1>Solicitação de Cartão de Crédito Empresarial</h1></div>', unsafe_allow_html=True)
st.markdown(f'<span class="tag">Demo • Streamlit</span>', unsafe_allow_html=True)
st.write("")

# =========================
# Passos / Tabs
# =========================
tabs = st.tabs([
    "1) Dados da Empresa",
    "2) Responsável",
    "3) Solicitação",
    "4) Documentos",
    "5) Revisão & Envio"
])

# -------- 1) Empresa --------
with tabs[0]:
    st.markdown("### 1) Dados da Empresa")
    with st.container(border=True):
        col1, col2 = st.columns([2,2])
        with col1:
            empresa_razao = st.text_input("Razão Social *")
            empresa_fantasia = st.text_input("Nome Fantasia")
            empresa_cnpj = st.text_input("CNPJ *", placeholder="__.___.___/____-__")
            ramo = st.text_input("Ramo de Atividade *", placeholder="Ex.: Comércio varejista de ...")
        with col2:
            faturamento = st.number_input("Faturamento Mensal (R$) *", min_value=0.0, step=1000.0, format="%.2f")
            qtd_func = st.number_input("Quantidade de Funcionários", min_value=0, step=1)
            site = st.text_input("Site (opcional)", placeholder="https://")

        # validação CNPJ
        if empresa_cnpj and not valida_cnpj(empresa_cnpj):
            st.warning("⚠️ CNPJ inválido. Verifique os dígitos.", icon="⚠️")

# -------- 2) Responsável --------
with tabs[1]:
    st.markdown("### 2) Responsável pela Solicitação")
    with st.container(border=True):
        col1, col2, col3 = st.columns([2,2,1.4])
        with col1:
            resp_nome = st.text_input("Nome Completo *")
            resp_email = st.text_input("E-mail *")
        with col2:
            resp_tel = st.text_input("Telefone/WhatsApp *", placeholder="(DDD) 99999-9999")
            resp_cpf = st.text_input("CPF *", placeholder="___.___.___-__")
        with col3:
            cargo = st.text_input("Cargo *", placeholder="Sócio, Diretor, Contador...")

        if resp_cpf and not valida_cpf(resp_cpf):
            st.warning("⚠️ CPF inválido. Verifique os dígitos.", icon="⚠️")

# -------- 3) Solicitação --------
with tabs[2]:
    st.markdown("### 3) Dados da Solicitação")
    with st.container(border=True):
        col1, col2, col3 = st.columns([1.3,1,1])
        with col1:
            limite = st.number_input("Limite pretendido (R$) *", min_value=0.0, step=500.0, format="%.2f")
        with col2:
            qtde_cartoes = st.number_input("Quantidade de cartões *", min_value=1, step=1, value=1)
        with col3:
            vencimento = st.selectbox("Vencimento da fatura *", options=[1,5,10,15,20,25])

        col4, col5 = st.columns(2)
        with col4:
            adesao_pontos = st.checkbox("Adesão ao programa de pontos")
        with col5:
            participa_cred = st.checkbox("Participa de credenciamento e maquininhas")

        # sinalização simples de elegibilidade (heurística)
        msg, css = "", "ok"
        if faturamento and limite:
            ratio = float(limite) / float(max(faturamento, 1))
            if ratio <= 0.3:
                msg, css = "Perfil compatível com análise inicial.", "ok"
            elif ratio <= 1.0:
                msg, css = "Solicitação moderada — pode exigir comprovação adicional.", "warn"
            else:
                msg, css = "Limite muito acima do faturamento — provável redução após análise.", "bad"
            st.markdown(f'<div class="{css}">• {msg}</div>', unsafe_allow_html=True)

# -------- 4) Documentos --------
with tabs[3]:
    st.markdown("### 4) Documentos (PDF/JPG/PNG)")
    st.caption("Carregue documentos básicos para agilizar a análise. Tamanho por arquivo ≤ 10MB.")
    with st.container(border=True):
        doc_contrato_social = st.file_uploader("Contrato Social / Requerimento de Empresário", type=["pdf","jpg","jpeg","png"])
        doc_cartao_cnpj    = st.file_uploader("Cartão CNPJ", type=["pdf","jpg","jpeg","png"])
        doc_endereco       = st.file_uploader("Comprovante de Endereço", type=["pdf","jpg","jpeg","png"])
        doc_fat_ultimos    = st.file_uploader("Faturamento (últimos 3 meses) - zip/pdf (opcional)", type=["zip","pdf"])

# -------- 5) Revisão & Envio --------
with tabs[4]:
    st.markdown("### 5) Revisão & Envio")
    with st.container(border=True):
        aceite = st.checkbox("✅ Li e aceito os Termos, Política de Privacidade e autorizo o tratamento de dados (LGPD) *")
        st.caption("Este é um protótipo. Ao enviar, você concorda em armazenar as informações localmente para teste.")

        # Resumo
        st.markdown("#### Resumo")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Razão Social", empresa_razao or "-")
            st.metric("CNPJ", empresa_cnpj or "-")
        with c2:
            st.metric("Faturamento", to_money(faturamento))
            st.metric("Limite Pretendido", to_money(limite))
        with c3:
            st.metric("Qtd. Cartões", int(qtde_cartoes) if qtde_cartoes else 0)
            st.metric("Vencimento", f"{vencimento} do mês" if vencimento else "-")

        # Botão Enviar
        can_submit = all([
            empresa_razao, empresa_cnpj, ramo, faturamento is not None,
            resp_nome, resp_email, resp_tel, resp_cpf, cargo,
            limite is not None, qtde_cartoes, vencimento, aceite,
            valida_cnpj(empresa_cnpj), valida_cpf(resp_cpf)
        ])

        if not valida_cnpj(empresa_cnpj) and empresa_cnpj:
            st.error("CNPJ inválido.")
        if not valida_cpf(resp_cpf) and resp_cpf:
            st.error("CPF inválido.")

        submit = st.button("📨 Enviar solicitação", use_container_width=True, disabled=not can_submit)

        if submit:
            # salva uploads
            path_contrato = save_file(doc_contrato_social, prefix="contrato_")
            path_cnpj     = save_file(doc_cartao_cnpj, prefix="cnpj_")
            path_end      = save_file(doc_endereco, prefix="endereco_")
            path_fat      = save_file(doc_fat_ultimos, prefix="faturamento_")

            payload = {
                "protocolo_preview": None,  # preenchido após salvar
                "empresa": {
                    "razao_social": empresa_razao,
                    "nome_fantasia": empresa_fantasia,
                    "cnpj": empresa_cnpj,
                    "ramo": ramo,
                    "faturamento_mensal": faturamento,
                    "qtd_func": qtd_func,
                    "site": site
                },
                "responsavel": {
                    "nome": resp_nome,
                    "email": resp_email,
                    "telefone": resp_tel,
                    "cpf": resp_cpf,
                    "cargo": cargo
                },
                "solicitacao": {
                    "limite": limite,
                    "qtde_cartoes": qtde_cartoes,
                    "vencimento": vencimento,
                    "adesao_pontos": bool(adesao_pontos),
                    "participa_credenciamento": bool(participa_cred)
                },
                "documentos": {
                    "contrato_social": path_contrato,
                    "cartao_cnpj": path_cnpj,
                    "comprovante_endereco": path_end,
                    "faturamento_ultimos": path_fat
                },
                "consentimento": {
                    "aceite": bool(aceite),
                    "aceito_em": datetime.now().isoformat(timespec="seconds")
                },
                "status": "Recebida",
                "meta": {
                    "gerado_por": "Streamlit demo",
                    "versao": "1.0.0",
                }
            }

            # persistir
            sid = salvar_solicitacao(payload)
            protocolo = f"{datetime.now().strftime('%Y%m%d')}-{sid:06d}"
            payload["protocolo_preview"] = protocolo

            st.success(f"✅ Solicitação recebida! Protocolo **{protocolo}**.")
            st.toast("Solicitação registrada com sucesso.", icon="✅")

            # Comprovante para download
            comp = make_receipt({
                "Protocolo": protocolo,
                "Data/Hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
                "Razão Social": empresa_razao,
                "CNPJ": empresa_cnpj,
                "Responsável": resp_nome,
                "E-mail": resp_email,
                "Telefone": resp_tel,
                "Limite Pretendido": to_money(limite),
                "Qtd Cartões": qtde_cartoes,
                "Vencimento": vencimento,
                "Adesão Pontos": "Sim" if adesao_pontos else "Não",
                "Participa Credenciamento": "Sim" if participa_cred else "Não",
            })
            st.download_button(
                "⬇️ Baixar comprovante (TXT)",
                data=comp,
                file_name=f"comprovante_{protocolo}.txt",
                mime="text/plain",
                use_container_width=True
            )

# =========================
# Modo administrador
# =========================
if admin_view:
    st.markdown("---")
    st.markdown("### 📋 Solicitações recebidas (local)")
    df = listar_solicitacoes()
    if df.empty:
        st.info("Nenhuma solicitação registrada ainda.")
    else:
        # formatação amigável
        df_fmt = df.copy()
        if "LimitePretendido" in df_fmt.columns:
            df_fmt["LimitePretendido"] = df_fmt["LimitePretendido"].apply(to_money)
        st.dataframe(df_fmt, use_container_width=True, hide_index=True)