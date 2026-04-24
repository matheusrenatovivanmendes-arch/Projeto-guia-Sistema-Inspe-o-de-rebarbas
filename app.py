import streamlit as st
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, date

# ─────────────────────────────────────────
# CONFIGURAÇÃO
# ─────────────────────────────────────────
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

SPREADSHEET_ID = "1cdSwUUx9WoNJ-uXuf3L_emcmZfwLEx4b8rFXnTNyW1I"
SHEET_NAME = "Página1"
SHEET_TURNOS = "Turno"   # nome da aba com os turnos

CABECALHO = [
    "Data",
    "Hora",
    "Turno",
    "Slitter (BZ, BFQ)",
    "Espessura Nominal da Chapa",
    "Medição da Chapa",
    "Medição da Rebarba",
    "Número de Golpes (Turno)",
    "Número de Golpes Total",
    "Tipo de Peça (CDR 80, CDR 100)",
    "Código da Matriz",
]


# ─────────────────────────────────────────
# CONEXÃO COM GOOGLE SHEETS
# ─────────────────────────────────────────
@st.cache_resource
def get_sheet():
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_NAME)
        return sheet
    except gspread.exceptions.SpreadsheetNotFound:
        st.error("❌ Planilha não encontrada. Verifique o SPREADSHEET_ID.")
        st.stop()
    except gspread.exceptions.WorksheetNotFound:
        st.error(f"❌ Aba '{SHEET_NAME}' não encontrada.")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erro de conexão: {e}")
        st.stop()

@st.cache_data(ttl=60)
def get_turnos() -> list:
    try:
        creds = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=SCOPES
        )
        client = gspread.authorize(creds)
        aba = client.open_by_key(SPREADSHEET_ID).worksheet(SHEET_TURNOS)
        valores = aba.col_values(1)
        turnos = [v.strip() for v in valores if v.strip()]
        if turnos:
            return turnos
    except Exception:
        pass
    return [
        "1° Turno (06h-14h)",
        "2° Turno (14h-22h)",
        "3° Turno (22h-06h)",
    ]


def aplicar_cabecalho(sheet):
    """
    Limpa TUDO (texto e cores) e coloca o cabeçalho na LINHA 1.
    """
    import time
    
    # 1. Limpa valores e formatações (cores, negritos, etc)
    sheet.clear()
    time.sleep(1)

    # 2. Insere o cabeçalho simples na Linha 1 (A1)
    sheet.update(range_name="A1:K1", values=[CABECALHO])
    
    # 3. Tira o congelamento de linhas
    sheet.freeze(rows=0)

def criar_cabecalho_se_necessario(sheet):
    """
    Verifica se o cabeçalho está na LINHA 1.
    """
    dados = sheet.get_all_values()
    # Agora verifica a primeira linha (índice 0)
    if len(dados) < 1 or dados[0] != CABECALHO:
        aplicar_cabecalho(sheet)


def enviar_para_sheets(sheet, dados: dict) -> bool:
    try:
        linha = [
            dados["data"],
            dados["hora"],
            dados["turno"],
            dados["slitter"],
            dados["esp_nominal"],
            dados["med_chapa"],
            dados["med_rebarba"],
            dados["golpes_turno"],
            dados["golpes_total"],
            dados["tipo_peca"],
            dados["cod_matriz"],
        ]
        # append_row sempre adiciona após a última linha com dado
        sheet.append_row(linha, value_input_option="USER_ENTERED")
        return True
    except Exception as e:
        st.error(f"Erro ao salvar: {e}")
        return False


def calcular_turno_automatico() -> int:
    hora = datetime.now().hour
    if 6 <= hora < 14:
        return 0
    elif 14 <= hora < 22:
        return 1
    else:
        return 2


# ─────────────────────────────────────────
# ESTILO CSS
# ─────────────────────────────────────────
st.set_page_config(
    page_title="Águia - Inspeção Rebarbas - PR600",
    page_icon="🦅",
    layout="centered",
)

st.markdown("""
<style>
    /* Container principal do cabeçalho */
    .header-table {
         border: 2px solid #003366; /* Azul Escuro Águia */
        width: 100%;
        font-family: 'Arial', sans-serif;
        margin-bottom: 20px;
    }

    /* Linha superior: Logo e Edição */
    .header-row-top {
        display: flex;
        border-bottom: 2px solid #003366 !important;
        border-right: 2px solid #003366 !important;
    }
    .header-logo {
        flex: 2;
        padding: 10px;
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 2px;
        display: flex;
        align-items: center;
        border-right: 2px solid #333;
    }
    .header-meta {
        flex: 1;
        padding: 5px 10px;
        font-size: 12px;
        line-height: 1.4;
    }

    /* Linha central: Setor e Título Principal */
    .header-row-title {
        border-bottom: 2px solid #333;
        text-align: center;
        padding: 10px;
    }
    .header-sector {
        font-size: 13px;
        font-weight: bold;
        text-transform: uppercase;
    }
    .header-main-title {
        font-size: 18px;
        font-weight: bold;
        margin-top: 5px;
    }

    /* Linha inferior: Autoria, Verificação e Frequência */
    .header-row-bottom {
        display: flex;
        font-size: 11px;
    }
    .header-bottom-item {
        flex: 1;
        padding: 5px;
        border-right: 1px solid #003366 !important;
        min-height: 45px ;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .header-bottom-item:last-child {
        border-right: none;
    }

    /* Estilo das instruções (Passos) */
    .passo-container {
        border: 1px solid #ccc;
        padding: 10px;
        background-color: #f9f9f9;
        margin-bottom: 15px;
    }
    .passo-item {
        font-size: 13px;
        margin-bottom: 8px;
        line-height: 1.5;
    }
    .passo-label {
        font-weight: bold;
        text-decoration: underline;
        color: #003366;
    }

    /* Título da Seção de Registros */
    .section-divider {
        background-color: #003366; /* Fundo Azul Escuro */
        color: white;
        text-align: center;
        padding: 8px;
        font-weight: bold;
        margin-top: 20px;
        text-transform: uppercase;
    }
       /* Estilo da área do Logo */
    .logo-container {
        flex: 2;
        padding: 5px 15px;
        display: flex;
        align-items: center; /* Alinha imagem e texto verticalmente */
        gap: 15px;           /* Espaço entre a imagem e o texto */
        border-right: 2px solid #333;
    }

    .logo-img {
        height: 45px;        /* Altura controlada para não quebrar a tabela */
        width: auto;
        object-fit: contain;
    }

    .logo-text {
        font-size: 24px;
        font-weight: 900;
        letter-spacing: 2px;
        margin: 0;
        color: #003366;

    }
        /* Estiliza especificamente o botão Primary (Registrar) */
    div.stButton > button[kind="primary"] {
        background-color: #003366 !important; /* Azul Escuro Águia */
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        font-weight: bold !important;
        padding: 0.5rem 1rem !important;
        transition: all 0.3s ease !important;
    }

    /* Efeito ao passar o mouse */
    div.stButton > button[kind="primary"]:hover {
        background-color: #004c99 !important; /* Azul levemente mais claro */
        border: none !important;
        color: white !important;
        box-shadow: 0 4px 8px rgba(0,0,0,0.2) !important;
    }

    /* Efeito ao clicar */
    div.stButton > button[kind="primary"]:active {
        background-color: #002244 !important;
        transform: scale(0.98);
    }
         /* Esconde o menu de configurações (três pontos) */
        #MainMenu {visibility: hidden;}
        
        /* Esconde o rodapé padrão */
        footer {visibility: hidden;}
        
        /* Esconde o botão de Deploy e o menu de opções superior */
        .stAppDeployButton {display:none;}
        header {visibility: hidden;}
        
        /* Garante que o fundo seja sempre branco para evitar flashes do modo escuro */
        .stApp {
            background-color: white;
        }
</style>
""", unsafe_allow_html=True)

# ─── CABEÇALHO ESTRUTURADO (Fiel ao PDF) ─────────────────
# ─── CABEÇALHO ESTRUTURADO (Fiel ao PDF) ─────────────────
url_logo = "https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcR_4natAasgwq0fSZykaJX6YN2cKSK9-sJP-g&s" 

st.markdown(f"""
<div class="header-table">
    <div class="header-row-top">
        <div class="logo-container">
            <img src="{url_logo}" class="logo-img">
        </div>
        <div class="header-meta">
            <div><b>Edição:</b> 17/02/2026</div>
            <div><b>Revisão:</b> 4</div>
        </div>
    </div>
    <div class="header-row-title">
        <div class="header-sector">Setor: Qualidade Industrial</div>
        <div class="header-main-title">INSPEÇÃO REBARBAS - PR600</div>
    </div>
    <div class="header-row-bottom">
        <div class="header-bottom-item"><b>Autor(a):</b><br>Gabriela Hohl Mendes</div>
        <div class="header-bottom-item"><b>Verificado:</b><br>Wagner Kazuki de Azambuja</div>
        <div class="header-bottom-item"><b>Inspeção:</b><br>A cada troca de slitter</div>
        <div class="header-bottom-item"><b>Desenvolvido pelo Operador web:</b><br>Matheus Renato Vivan Mendes</div>
    </div>
</div>
""", unsafe_allow_html=True)




# ─── INSTRUÇÕES DE TRABALHO ─────────────────────────────
st.markdown(f"""
<div class="passo-container">
    <div class="passo-item">
        <span class="passo-label">1 PASSO</span>: Com a máquina parada para a troca de slitter, efetuar a medição da chapa com o paquímetro e registrar no campo "Medição da chapa".
    </div>
    <div class="passo-item">
        <span class="passo-label">2 PASSO</span>: Com cuidado, identificar em qual dos furos a rebarba está mais crítica, medir com o paquímetro e registrar no campo "Medição da rebarba".
    </div>
    <div class="passo-item">
        <span class="passo-label">3 PASSO</span>: A cada troca de slitter, registrar o número de golpes.
    </div>
</div>
""", unsafe_allow_html=True)

# ─── SEÇÃO DE REGISTROS ─────────────────────────────────
st.markdown('<div class="section-divider">Registros de Qualidade</div>', unsafe_allow_html=True)

# ─────────────────────────────────────────
# FORMULÁRIO
# ─────────────────────────────────────────
sheet = get_sheet()
criar_cabecalho_se_necessario(sheet)

col1, col2, col3 = st.columns(3)
data_registro = date.today()
hora_registro = datetime.now().time()

col1, col2, col3 = st.columns(3)
with col1:
    st.text_input("📅 Data", value=data_registro.strftime("%d/%m/%Y"), disabled=True)
with col2:
    st.text_input("🕐 Hora", value=hora_registro.strftime("%H:%M"), disabled=True)
with col3:
    opcoes_turno = get_turnos()
    idx = calcular_turno_automatico()
    idx = idx if idx < len(opcoes_turno) else 0
    turno = st.selectbox("🔄 Turno", opcoes_turno, index=idx)

col1, col2, col3 = st.columns(3)
with col1:
    slitter = st.selectbox("⚙️ Slitter", ["BZ", "BFQ"])
with col2:
    tipo_peca = st.selectbox("🔩 Tipo de Peça", ["CDR 80", "CDR 100"])
with col3:
    cod_matriz = st.text_input("🏷️ Código da Matriz", placeholder="Ex: MTZ-001")

col1, col2, col3 = st.columns(3)
with col1:
    esp_nominal = st.number_input(
        "📐 Espessura Nominal (mm)",
        min_value=0.0, max_value=50.0,
        value=0.0, step=0.01, format="%.2f",
    )
with col2:
    med_chapa = st.number_input(
        "📏 Medição da Chapa (mm)",
        min_value=0.0, max_value=50.0,
        value=0.0, step=0.01, format="%.2f",
    )
with col3:
    med_rebarba = st.number_input(
        "🔬 Medição da Rebarba (mm)",
        min_value=0.0, max_value=50.0,
        value=0.0, step=0.001, format="%.3f",
    )

# Indicador de desvio em tempo real
if esp_nominal > 0 and med_chapa > 0:
    desvio = med_chapa - esp_nominal
    desvio_pct = (desvio / esp_nominal) * 100
    

col1, col2 = st.columns(2)
with col1:
    golpes_turno = st.number_input(
        "🔨 Nº Golpes (Turno)", min_value=0, step=1,
        help="Golpes realizados neste turno",
    )
with col2:
    golpes_total = st.number_input(
        "🔨 Nº Golpes Total", min_value=0, step=1,
        help="Contador total acumulado da máquina",
    )

observacoes = st.text_area("📝 Observações", placeholder="Campo livre para observações...", height=80)

st.divider()

enviado = st.button(
    "Registrar",
    use_container_width=True,
    type="primary",
)

if enviado:
    erros = []
    if not cod_matriz.strip():
        erros.append("Código da Matriz é obrigatório.")
    if esp_nominal == 0:
        erros.append("Espessura Nominal deve ser maior que zero.")
    if med_chapa == 0:
        erros.append("Medição da Chapa deve ser maior que zero.")
    if golpes_total == 0:
        erros.append("Nº de Golpes Total deve ser maior que zero.")

    if erros:
        for e in erros:
            st.warning(f"⚠️ {e}")
    else:
        dados = {
            "data": data_registro.strftime("%d/%m/%Y"),
            "hora": hora_registro.strftime("%H:%M"),
            "turno": turno,
            "slitter": slitter,
            "esp_nominal": f"{esp_nominal:.2f}".replace(".", ","),
            "med_chapa": f"{med_chapa:.2f}".replace(".", ","),
            "med_rebarba": f"{med_rebarba:.3f}".replace(".", ","),
            "golpes_turno": golpes_turno,
            "golpes_total": golpes_total,
            "tipo_peca": tipo_peca,
            "cod_matriz": cod_matriz.strip().upper(),
        }

        with st.spinner("Salvando na planilha..."):
            sucesso = enviar_para_sheets(sheet, dados)

        if sucesso:
            st.success("✅ Registro salvo com sucesso na planilha!")
            

# ─── Consulta e Filtros ──────────────────
#st.divider()
#with st.expander("🔍 Consultar e filtrar registros", expanded=False):

    #if st.button("🔄 Carregar dados", key="btn_carregar"):
        #st.session_state["registros_cache"] = None
        #try:
         #   with st.spinner("Carregando..."):
                # Busca a partir da linha 4 (após as 3 linhas de cabeçalho)
          #      todos = sheet.get_all_values()
           #     if len(todos) > 3:
            #        colunas = todos[2]   # linha 3 = nomes das colunas
              #      linhas  = todos[3:]  # linha 4 em diante = dados
               #     registros = [dict(zip(colunas, l)) for l in linhas if any(c.strip() for c in l)]
                #    st.session_state["registros_cache"] = registros
              #  else:
               #     st.info("Nenhum registro encontrado ainda.")
       # except Exception as e:
          #  st.error(f"Erro ao carregar: {e}")

  #  if st.session_state.get("registros_cache"):
        #import pandas as pd
        #from datetime import datetime as dt

        #df = pd.DataFrame(st.session_state["registros_cache"])

        #st.markdown("#### Filtros")
       # col1, col2, col3 = st.columns(3)

        # ── Filtro por Data ──────────────────────
        #with col1:
          #  try:
             #   datas_unicas = sorted(
                 #   df["Data"].dropna().unique().tolist(),
                   # key=lambda x: dt.strptime(x, "%d/%m/%Y") if x else dt.min
              #  )
          #  except Exception:
              #  datas_unicas = sorted(df["Data"].dropna().unique().tolist())

           # datas_sel = st.multiselect(
               # "📅 Filtrar por Data",
                #options=datas_unicas,
               # placeholder="Todas as datas",
           # )

        # ── Filtro por Código de Matriz ──────────
        #with col2:
           # codigos_unicos = sorted(df["Código da Matriz"].dropna().unique().tolist())
           # codigos_sel = st.multiselect(
              #  "🏷️ Filtrar por Código da Matriz",
               # options=codigos_unicos,
               # placeholder="Todos os códigos",
            #)

        # ── Filtro por Slitter ───────────────────
        #with col3:
           # slitters_unicos = sorted(df["Slitter (BZ, BFQ)"].dropna().unique().tolist())
           # slitter_sel = st.multiselect(
               # "⚙️ Filtrar por Slitter",
                #options=slitters_unicos,
               # placeholder="Todos",
            #)

        # ── Aplicar filtros ──────────────────────
       # df_filtrado = df.copy()
       # if datas_sel:
        #    df_filtrado = df_filtrado[df_filtrado["Data"].isin(datas_sel)]
        #if codigos_sel:
           # df_filtrado = df_filtrado[df_filtrado["Código da Matriz"].isin(codigos_sel)]
        #if slitter_sel:
           # df_filtrado = df_filtrado[df_filtrado["Slitter (BZ, BFQ)"].isin(slitter_sel)]

        # ── Resultado ────────────────────────────
       # st.markdown(f"**{len(df_filtrado)} registro(s) encontrado(s)**")
       # st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

#with st.expander("🔧 Configurações da planilha"):
   # st.caption("Use o botão abaixo se o cabeçalho da planilha estiver faltando ou incorreto.")
   # if st.button("📝 Criar / Reescrever cabeçalho na planilha", type="secondary"):
       # try:
          #  with st.spinner("Aplicando cabeçalho..."):
               # aplicar_cabecalho(sheet)
            #st.success("✅ Cabeçalho criado com sucesso na linha 1 da planilha!")
        #except Exception as e:
            #st.error(f"Erro: {e}")
