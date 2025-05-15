import streamlit as st
import plotly.express as px
from datetime import datetime
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import plotly.graph_objects as go
import re  # Importando a biblioteca de expressões regulares

# Configurar a página para o layout largo
st.set_page_config(layout="wide")

# Inserir estilo CSS customizado
st.markdown("""
    <style>
        .main-container {
            max-width: 80%;  /* Define largura da página */
            margin-left: auto; 
            margin-right: auto;
            padding: 1rem;
        }
        .css-18e3th9 {
            padding: 1rem;  /* Reduz o padding superior e inferior */
        }
        .css-1d391kg {
            padding-top: 0.5rem;
            padding-bottom: 0.5rem;  /* Reduz o padding geral da página */
        }
        .css-1adrfps {
            margin-bottom: 1rem;
        }
        .css-1g6gooi {
            margin-bottom: 1rem;
        }
    </style>
    <div class="main-container">
""", unsafe_allow_html=True)

# Carregar os dados
data = pd.read_csv('dados_completos.csv', delimiter=',', encoding='latin-1')


# Normalizar as colunas
data['segmento_individual'] = data['segmento_individual'].str.strip().str.lower()
data['nome_fantasia'] = data['nome_fantasia'].str.strip().str.lower()

# Converter a coluna 'data_finalizacao' para datetime
data['data_finalizacao'] = pd.to_datetime(data['data_finalizacao'])

# Criar a coluna 'mes' a partir de 'data_finalizacao'
data['mes'] = data['data_finalizacao'].dt.strftime('%B')

# Definir a paleta de cores
cores = ["#27306c",  "#08adac", "#d12a78", "#e7ebea", "#8b9db9", "#b5bed1", "#7c7c9c", "#acacc4", "#b4b4c4", "#c4c4d4"]
# Lista de empresas para sempre incluir no gráfico
empresas_para_incluir = ['cnp capitalização (antiga caixa capitalização)',
                             'cnp consórcio (antiga caixa consórcios)',
                             'previsul',
                             'odonto empresas']

st.sidebar.image("cnpp.jpg", width=200)  # Ajuste o caminho e a largura da imagem conforme necessário

# Filtros na Sidebar
st.sidebar.header("Filtros")

# Filtros de região, UF, sexo e faixa etária
regiao = st.sidebar.multiselect('Selecione a região', options=data['regiao'].unique())
uf = st.sidebar.multiselect('Selecione a UF', options=data['uf'].unique())
sexo = st.sidebar.multiselect('Selecione o sexo', options=data['sexo'].unique())
faixa_etaria = st.sidebar.multiselect('Selecione a faixa etária', options=data['faixa_etaria'].unique())

# Filtrar os dados com base nas seleções da sidebar
dados_filtrados = data.copy()  # Copiamos os dados originais para aplicar os filtros

# Aplica os filtros da sidebar aos dados
if regiao:
    dados_filtrados = dados_filtrados[dados_filtrados['regiao'].isin(regiao)]
if uf:
    dados_filtrados = dados_filtrados[dados_filtrados['uf'].isin(uf)]
if sexo:
    dados_filtrados = dados_filtrados[dados_filtrados['sexo'].isin(sexo)]
if faixa_etaria:
    dados_filtrados = dados_filtrados[dados_filtrados['faixa_etaria'].isin(faixa_etaria)]

# Assinatura na sidebar
st.sidebar.markdown("---")
st.sidebar.markdown("*Desenvolvido Por: Gabriel Luis*")

# Função para buscar os dados com Selenium
def buscar_dados(empresa, periodo):
    driver = webdriver.Chrome()  # Inicializa o WebDriver do Chrome
    driver.get("https://consumidor.gov.br/pages/indicador/empresa/abrir")

    # Espera até que o campo de pesquisa esteja disponível
    try:
        search_box = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.ID, "autocomplete_priEmpresa"))
        )
    except Exception as e:
        driver.quit()
        st.error(f"Erro ao localizar o campo de busca: {e}")
        return None

    # Inserir o nome da empresa no campo de pesquisa
    search_box.send_keys(empresa)

    # Espera a lista suspensa aparecer e seleciona o item correspondente à empresa
    try:
        empresa_autocomplete = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, f"//li[contains(@class, 'pui-autocomplete-item') and contains(., '{empresa.upper()}')]"))
        )
        empresa_autocomplete.click()  # Seleciona a empresa da lista de autocomplete
    except Exception as e:
        st.error(f"Erro ao selecionar a empresa do autocomplete: {e}")
        driver.quit()
        return None

    # Espera até que as abas de período estejam disponíveis
    try:
        WebDriverWait(driver, 20).until(
            lambda driver: driver.execute_script("return document.readyState") == "complete"
        )
        if periodo == '30 Dias':
            aba_periodo = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab_30_dias' and @data-toggle='tab']"))
            )
        elif periodo == '6 Meses':
            aba_periodo = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab_6_meses' and @data-toggle='tab']"))
            )
        elif periodo == '2025':
            aba_periodo = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab_ano_2025' and @data-toggle='tab']"))
            )
        elif periodo == 'Todos':
            aba_periodo = WebDriverWait(driver, 20).until(
                EC.element_to_be_clickable((By.XPATH, "//a[@href='#tab_todas' and @data-toggle='tab']"))
            )
        aba_periodo.click()  # Clicar na aba correspondente ao período
        time.sleep(3)  # Pequeno atraso para garantir o carregamento dos dados da aba selecionada
    except Exception as e:
        driver.save_screenshot('erro.png')  # Captura a tela para análise
        st.error(f"Erro ao localizar a aba do período selecionado: {e}")
        driver.quit()
        return None

    # Verifica se os dados estão dentro de um iframe e, se sim, muda o contexto
    #try:
    #    iframe = driver.find_element(By.XPATH, "//iframe")
    #    driver.switch_to.frame(iframe)
    #except Exception as e:
        #st.write("Nenhum iframe encontrado, continuando no contexto principal.")

    # Extrair os dados
    try:
        if periodo == '30 Dias':
            satisfacao_atendimento = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Satisfação com o Atendimento')]/following::div[@class='fonteResultado']"))
            ).text

            indice_solucao = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Índice de Solução')]/following::div[@class='fonteResultado']"))
            ).text

            reclamacoes_respondidas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Reclamações Respondidas')]/following::div[@class='fonteResultado']"))
            ).text

            prazo_medio_respostas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//label[contains(text(),'Prazo Médio de Respostas')]/following::div[@class='fonteResultadoDia']"))
            ).text

        elif periodo == '6 Meses':
            satisfacao_atendimento = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCircleatendimentoMESES_6']//div[@class='fonteResultado']"))
            ).text

            indice_solucao = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCirclesolucaoMESES_6']//div[@class='fonteResultado']"))
            ).text

            reclamacoes_respondidas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCirclerespondidasMESES_6']//div[@class='fonteResultado']"))
            ).text

            prazo_medio_respostas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCircleprazoMESES_6']//div[@class='fonteResultadoDia']"))
            ).text

        elif periodo == '2025':
            satisfacao_atendimento = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCircleatendimentoANOS_2025']//div[@class='fonteResultado']"))
            ).text

            indice_solucao = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCirclesolucaoANOS_2025']//div[@class='fonteResultado']"))
            ).text

            reclamacoes_respondidas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCirclerespondidasANOS_2025']//div[@class='fonteResultado']"))
            ).text

            prazo_medio_respostas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCircleprazoANOS_2025']//div[@class='fonteResultadoDia']"))
            ).text

        elif periodo == 'Todos':
            satisfacao_atendimento = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCircleatendimentoTODAS_']//div[@class='fonteResultado']"))
            ).text

            indice_solucao = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCirclesolucaoTODAS_']//div[@class='fonteResultado']"))
            ).text

            reclamacoes_respondidas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCirclerespondidasTODAS_']//div[@class='fonteResultado']"))
            ).text

            prazo_medio_respostas = WebDriverWait(driver, 20).until(
                EC.presence_of_element_located((By.XPATH, "//div[@id='dvCircleprazoTODAS_']//div[@class='fonteResultadoDia']"))
            ).text

    except Exception as e:
        st.error(f"Erro ao extrair os dados: {e}")
        driver.quit()
        return None

    driver.quit()

    return {
        "Satisfação com o Atendimento": satisfacao_atendimento,
        "Índice de Solução": indice_solucao,
        "Reclamações Respondidas": reclamacoes_respondidas,
        "Prazo Médio de Respostas": prazo_medio_respostas
    }


# Definir as abas
aba1, aba2, aba3, aba4, aba5, aba6, aba7 = st.tabs(["Análise Geral", "Dados Demográficos", "Comparativo", "Reclamações", "Tempo de Resposta", "Coleta de Dados", "Ranking"])

with aba1:
    # Seleção de Segmento de Mercado
    segmento = st.selectbox('Selecione o segmento de mercado', data['segmento_de_mercado_x'].unique())

    # Inicializar variável para armazenar o nome da empresa
    empresa_selecionada = None
    segmento_individual = None

    # Lógica de filtro automático baseado no segmento
    if segmento == 'Administradoras de Consórcios':
        empresa_selecionada = 'cnp consórcio (antiga caixa consórcios)'

    elif segmento == 'Seguros, Capitalização e Previdência':
        # Selecionar segmento individual dentro de Seguros, Capitalização e Previdência
        st.write("Segmentação Individual")
        segmentos_individuais_unicos = ['capitalização', 'seguros e previdência']
        segmento_individual = st.selectbox('Selecione o segmento individual', segmentos_individuais_unicos)
        
        if segmento_individual == 'capitalização':
            empresa_selecionada = 'cnp capitalização (antiga caixa capitalização)'
        elif segmento_individual == 'seguros e previdência':
            empresa_selecionada = 'previsul'

    elif segmento == 'Operadoras de Planos de Saúde e Administradoras de Benefícios':
        empresa_selecionada = 'odonto empresas'

    # Filtrar os dados com base na empresa selecionada
    if empresa_selecionada:
        dados_empresa = dados_filtrados[dados_filtrados['nome_fantasia'] == empresa_selecionada]
    else:
        dados_empresa = pd.DataFrame()  # Se não houver empresa selecionada, criar um dataframe vazio

    # Filtrar os dados do mercado (excluindo os dados da empresa selecionada e filtrando pelo segmento)
    dados_mercado = dados_filtrados[(dados_filtrados['nome_fantasia'] != empresa_selecionada) & (dados_filtrados['segmento_de_mercado_x'] == segmento)]

    # Se o segmento for 'Seguros, Capitalização e Previdência', aplicar também o filtro do segmento individual
    if segmento == 'Seguros, Capitalização e Previdência' and segmento_individual:
        if segmento_individual == 'capitalização':
            dados_mercado = dados_mercado[dados_mercado['segmento_individual'] == 'capitalização']
        elif segmento_individual == 'seguros e previdência':
            # Filtrar tanto por 'seguros' quanto por 'previdência'
            dados_mercado = dados_mercado[dados_mercado['segmento_individual'].isin(['seguros', 'previdência'])]

    # Verificação se há dados de mercado disponíveis após o filtro
    if dados_mercado.empty:
        st.warning('Nenhum dado de mercado encontrado para este segmento.')
    else:
        # 1. Distribuição de Reclamações por Avaliação
        st.header('Distribuição de Reclamações por Avaliação')

        # Dividir a visualização em duas colunas para Empresa e Mercado
        col1, col2 = st.columns(2)

        # Dados da Empresa
        with col1:
            st.subheader(f'Dados da Empresa ({empresa_selecionada})')
            if not dados_empresa.empty:
                avaliacao_empresa = dados_empresa['avaliacao_reclamacao'].value_counts().reset_index()
                avaliacao_empresa.columns = ['avaliacao_reclamacao', 'counts']
                total_count_empresa = avaliacao_empresa['counts'].sum()
                avaliacao_empresa['percentual'] = (avaliacao_empresa['counts'] / total_count_empresa) * 100

                fig_avaliacao_empresa = px.bar(avaliacao_empresa, 
                                               x='avaliacao_reclamacao', 
                                               y='counts', 
                                               title="Distribuição de Reclamações por Avaliação (Empresa)", 
                                               color='avaliacao_reclamacao', 
                                               color_discrete_sequence=cores,  
                                               text=avaliacao_empresa['percentual'].apply(lambda x: f"{x:.2f}%"))
                fig_avaliacao_empresa.update_traces(textposition='outside')
                st.plotly_chart(fig_avaliacao_empresa)
            else:
                st.write('Nenhuma reclamação encontrada para a empresa.')

        # Dados do Mercado
        with col2:
            st.subheader('Dados do Mercado')
            avaliacao_mercado = dados_mercado['avaliacao_reclamacao'].value_counts().reset_index()
            avaliacao_mercado.columns = ['avaliacao_reclamacao', 'counts']
            total_count_mercado = avaliacao_mercado['counts'].sum()
            avaliacao_mercado['percentual'] = (avaliacao_mercado['counts'] / total_count_mercado) * 100

            fig_avaliacao_mercado = px.bar(avaliacao_mercado, 
                                           x='avaliacao_reclamacao', 
                                           y='counts', 
                                           title="Distribuição de Reclamações por Avaliação (Mercado)", 
                                           color='avaliacao_reclamacao', 
                                           color_discrete_sequence=cores,  
                                           text=avaliacao_mercado['percentual'].apply(lambda x: f"{x:.2f}%"))
            fig_avaliacao_mercado.update_traces(textposition='outside')
            st.plotly_chart(fig_avaliacao_mercado)

        # 2. Análise de Reclamações Respondidas vs. Não Respondidas
        st.header('Análise de Reclamações Respondidas vs. Não Respondidas')

        # Dividir a visualização em duas colunas para Empresa e Mercado
        col1, col2 = st.columns(2)

        # Dados da Empresa
        with col1:
            st.subheader(f'Dados da Empresa ({empresa_selecionada})')
           
            if not dados_empresa.empty:
                respondida_group_empresa = dados_empresa['respondida'].value_counts().reset_index()
                respondida_group_empresa.columns = ['respondida', 'counts']
                fig_respondida_empresa = px.pie(respondida_group_empresa, 
                                                names='respondida', 
                                                values='counts', 
                                                title="Proporção de Reclamações Respondidas vs. Não Respondidas (Empresa)", 
                                                color_discrete_sequence=cores)
                st.plotly_chart(fig_respondida_empresa)
            else:
                st.write('Nenhuma reclamação encontrada para a empresa.')

        # Dados do Mercado
        with col2:
            st.subheader('Dados do Mercado')
            respondida_group_mercado = dados_mercado['respondida'].value_counts().reset_index()
            respondida_group_mercado.columns = ['respondida', 'counts']
            fig_respondida_mercado = px.pie(respondida_group_mercado, 
                                            names='respondida', 
                                            values='counts', 
                                            title="Proporção de Reclamações Respondidas vs. Não Respondidas (Mercado)", 
                                            color_discrete_sequence=cores)
            st.plotly_chart(fig_respondida_mercado)

        # 3. Distribuição de Reclamações por Como Comprou/Contratou
        st.header('Distribuição de Reclamações por Como Comprou/Contratou')

        # Dividir a visualização em duas colunas para Empresa e Mercado
        col1, col2 = st.columns(2)

        # Dados da Empresa
        with col1:
            st.subheader(f'Dados da Empresa ({empresa_selecionada})')
            if not dados_empresa.empty:
                como_comprou_group_empresa = dados_empresa['como_comprou_contratou'].value_counts().reset_index()
                como_comprou_group_empresa.columns = ['como_comprou_contratou', 'counts']
                fig_como_comprou_empresa = px.bar(como_comprou_group_empresa, 
                                                  x='como_comprou_contratou', 
                                                  y='counts', 
                                                  title="Distribuição de Reclamações por Como Comprou/Contratou (Empresa)", 
                                                  color='como_comprou_contratou', 
                                                  color_discrete_sequence=cores, 
                                                  text='counts')
                fig_como_comprou_empresa.update_traces(texttemplate='%{text}', textposition='outside')
                st.plotly_chart(fig_como_comprou_empresa)
            else:
                st.write('Nenhuma reclamação encontrada para a empresa.')

        # Dados do Mercado
        with col2:
            st.subheader('Dados do Mercado')
            como_comprou_group_mercado = dados_mercado['como_comprou_contratou'].value_counts().reset_index()
            como_comprou_group_mercado.columns = ['como_comprou_contratou', 'counts']
            fig_como_comprou_mercado = px.bar(como_comprou_group_mercado, 
                                              x='como_comprou_contratou', 
                                              y='counts', 
                                              title="Distribuição de Reclamações por Como Comprou/Contratou (Mercado)", 
                                              color='como_comprou_contratou', 
                                              color_discrete_sequence=cores, 
                                              text='counts')
            fig_como_comprou_mercado.update_traces(texttemplate='%{text}', textposition='outside')
            st.plotly_chart(fig_como_comprou_mercado)

        # 4. Análise de Reclamações por Procura da Empresa
        st.header('Análise de Reclamações por Procura da Empresa')

        # Dividir a visualização em duas colunas para Empresa e Mercado
        col1, col2 = st.columns(2)

        # Dados da Empresa
        with col1:
            st.subheader(f'Dados da Empresa ({empresa_selecionada})')
            if not dados_empresa.empty:
                procurou_group_empresa = dados_empresa['procurou_empresa'].value_counts().reset_index()
                procurou_group_empresa.columns = ['procurou_empresa', 'counts']
                fig_procurou_empresa = px.pie(procurou_group_empresa, 
                                              names='procurou_empresa', 
                                              values='counts', 
                                              title="Proporção de Reclamações com e sem Procura da Empresa (Empresa)", 
                                              color_discrete_sequence=cores)
                st.plotly_chart(fig_procurou_empresa)
            else:
                st.write('Nenhuma reclamação encontrada para a empresa.')

        # Dados do Mercado
        with col2:
            st.subheader('Dados do Mercado')
            procurou_group_mercado = dados_mercado['procurou_empresa'].value_counts().reset_index()
            procurou_group_mercado.columns = ['procurou_empresa', 'counts']
            fig_procurou_mercado = px.pie(procurou_group_mercado, 
                                          names='procurou_empresa', 
                                          values='counts', 
                                          title="Proporção de Reclamações com e sem Procura da Empresa (Mercado)", 
                                          color_discrete_sequence=cores)
            st.plotly_chart(fig_procurou_mercado)

with aba2:
    st.title("Dados Demográficos Por Empresa")

    # Use uma cópia dos dados para não modificar o original
    data_demografico = data.copy()

    # Normalizar as colunas para garantir a correta filtragem
    data_demografico['segmento_de_mercado_x'] = data_demografico['segmento_de_mercado_x'].str.strip().str.lower()
    data_demografico['segmento_individual'] = data_demografico['segmento_individual'].str.strip().str.lower()

    # Filtro de Segmento de Mercado
    segmento = st.selectbox('Selecione o segmento de mercado', data_demografico['segmento_de_mercado_x'].unique(), key='segmento_mercado_aba2')

    # Filtro de Segmento Individual - Aparece apenas se o segmento for 'Seguros, Capitalização e Previdência'
    if segmento == 'seguros, capitalização e previdência':
        segmento_individual = st.selectbox(
            'Selecione o segmento individual',
            ['capitalização', 'seguros e previdência'],  # Combina Seguros e Previdência em uma única opção
            key='segmento_individual_aba2'
        )
    else:
        segmento_individual = None

    # Filtragem dos dados com base nos filtros de segmento de mercado e individual
    if segmento == 'seguros, capitalização e previdência':
        if segmento_individual == 'seguros e previdência':
            dados_filtrados_demograficos = data_demografico[(data_demografico['segmento_de_mercado_x'] == segmento) & 
                                                            (data_demografico['segmento_individual'].isin(['seguros', 'previdência']))]
        else:
            dados_filtrados_demograficos = data_demografico[(data_demografico['segmento_de_mercado_x'] == segmento) & 
                                                            (data_demografico['segmento_individual'] == segmento_individual)]
    else:
        dados_filtrados_demograficos = data_demografico[data_demografico['segmento_de_mercado_x'] == segmento]

    # Filtro de Pesquisa de Empresa - Adicionando a opção 'Todos'
    empresas_disponiveis = ['Todos'] + list(dados_filtrados_demograficos['nome_fantasia'].unique())
    empresa_selecionada_demografica = st.selectbox('Selecione a empresa para análise demográfica', empresas_disponiveis, key='empresa_demografica_aba2')

    # Filtrar os dados novamente com base na empresa selecionada, exceto se for 'Todos'
    if empresa_selecionada_demografica != 'Todos':
        dados_filtrados_demograficos = dados_filtrados_demograficos[dados_filtrados_demograficos['nome_fantasia'] == empresa_selecionada_demografica]

    # Verificação se há dados filtrados
    if dados_filtrados_demograficos.empty:
        st.write("Nenhum dado disponível para a seleção atual.")
    else:
        # 1. Distribuição Demográfica
        st.subheader('Distribuição Demográfica')

        # 1.1 Distribuição Geográfica
        st.subheader('Distribuição Geográfica (Região, UF, Cidade)')
        geo_group = dados_filtrados_demograficos.groupby(['regiao', 'uf', 'cidade']).size().reset_index(name='counts')
        fig_geo = px.sunburst(geo_group, path=['regiao', 'uf', 'cidade'], values='counts', title="Distribuição Geográfica", color_discrete_sequence=cores)
        st.plotly_chart(fig_geo)

        # 1.2 Distribuição por Sexo
        st.subheader('Distribuição por Sexo (M, F, O)')
        sex_group = dados_filtrados_demograficos['sexo'].value_counts().reset_index()
        sex_group.columns = ['sexo', 'counts']
        fig_sex = px.bar(sex_group, 
                          x='sexo', 
                          y='counts', 
                          title="Distribuição por Sexo", 
                          color='sexo', 
                          color_discrete_sequence=cores, 
                          text='counts')
        fig_sex.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig_sex)

        # 1.3 Distribuição por Faixa Etária
        st.subheader('Distribuição por Faixa Etária')
        age_group = dados_filtrados_demograficos['faixa_etaria'].value_counts().reset_index()
        age_group.columns = ['faixa_etaria', 'counts']
        fig_age = px.bar(age_group, 
                         x='faixa_etaria', 
                         y='counts', 
                         title="Distribuição por Faixa Etária", 
                         color='faixa_etaria', 
                         color_discrete_sequence=cores, 
                         text='counts')
        fig_age.update_traces(texttemplate='%{text}', textposition='outside')
        st.plotly_chart(fig_age)

with aba3:
    st.title('Comparativo de reclamações entre empresas')

    # Filtros para segmento de mercado e segmento individual
    segmento = st.selectbox('Selecione o Segmento de Mercado', ['Administradoras de Consórcios', 'Seguros, Capitalização e Previdência', 'Operadoras de Planos de Saúde e Administradoras de Benefícios'])
    
    if segmento == 'Seguros, Capitalização e Previdência':
        segmentos_individuais_unicos = ['capitalização', 'seguros e previdência']
        segmento_individual = st.selectbox('Selecione o segmento individual', segmentos_individuais_unicos, key="segmento_individual")

    # Filtrar dados com base no segmento de mercado e segmento individual
    if segmento == 'Administradoras de Consórcios':
        dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]
        empresa_selecionada = 'cnp consórcio (antiga caixa consórcios)'
    elif segmento == 'Seguros, Capitalização e Previdência':
        if segmento_individual == 'capitalização':
            dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & (data['segmento_individual'] == 'capitalização')]
            empresa_selecionada = 'cnp capitalização (antiga caixa capitalização)'
        elif segmento_individual == 'seguros e previdência':
            dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & (data['segmento_individual'].isin(['seguros', 'previdência']))]
            empresa_selecionada = 'previsul'
    elif segmento == 'Operadoras de Planos de Saúde e Administradoras de Benefícios':
        dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]
        empresa_selecionada = 'odonto empresas'

    # Salvar uma cópia dos dados filtrados para os gráficos de Top 10
    dados_top10 = dados_filtrados.copy()

    # 2. Top 10 Empresas com Mais Reclamações por Mês
    st.header('Top 10 Empresas com Mais Reclamações por Mês')
    selected_month = st.selectbox('Selecione o mês', options=dados_top10['mes'].unique())

    # 2.1 Top 10 Empresas com Mais Reclamações no Mês Selecionado
    st.subheader(f'Top 10 Empresas com Mais Reclamações em {selected_month}')
    monthly_data = dados_top10[dados_top10['mes'] == selected_month]
    monthly_counts = monthly_data['nome_fantasia'].value_counts().reset_index()
    monthly_counts.columns = ['nome_fantasia', 'counts']

    # Filtrar para exibir apenas as 10 maiores, mas também adicionar empresas específicas, se necessário
    top_10 = monthly_counts.head(10)

    # Adicionar empresas que não estão no top 10
    empresas_para_incluir = ['cnp capitalização (antiga caixa capitalização)', 'cnp consórcio (antiga caixa consórcios)', 'previsul', 'odonto empresas']
    for empresa in empresas_para_incluir:
        if empresa not in top_10['nome_fantasia'].values:
            contagem_empresa = monthly_data[monthly_data['nome_fantasia'] == empresa]['nome_fantasia'].count()
            if contagem_empresa > 0:
                top_10 = pd.concat([top_10, pd.DataFrame({'nome_fantasia': [empresa], 'counts': [contagem_empresa]})])

    # Destacar empresas específicas com negrito
    top_10['nome_fantasia'] = top_10['nome_fantasia'].apply(lambda x: f"<b>{x}</b>" if x in empresas_para_incluir else x)

    # Criar o gráfico de barras
    fig_monthly = px.bar(top_10, x='nome_fantasia', y='counts', title=f"Top 10 Empresas em {selected_month}", text='counts', color_discrete_sequence=cores)
    fig_monthly.update_traces(texttemplate='%{text}', textposition='outside')
    fig_monthly.update_layout(xaxis_title='Nome da Empresa', yaxis_title='Número de Reclamações')
    st.plotly_chart(fig_monthly)

    # 3. Top 10 Empresas com Mais Reclamações no Ano Atual
    st.header('Top 10 Empresas com Mais Reclamações no Ano Atual')
    current_year = dados_top10['data_finalizacao'].dt.year == datetime.now().year
    current_year_data = dados_top10[current_year]
    current_year_counts = current_year_data['nome_fantasia'].value_counts().reset_index()
    current_year_counts.columns = ['nome_fantasia', 'counts']

    # Filtrar para exibir apenas as 10 maiores, mas também adicionar empresas específicas, se necessário
    top_10_ano = current_year_counts.head(10)

    # Adicionar empresas que não estão no top 10
    for empresa in empresas_para_incluir:
        if empresa not in top_10_ano['nome_fantasia'].values:
            contagem_empresa = current_year_data[current_year_data['nome_fantasia'] == empresa]['nome_fantasia'].count()
            if contagem_empresa > 0:
                top_10_ano = pd.concat([top_10_ano, pd.DataFrame({'nome_fantasia': [empresa], 'counts': [contagem_empresa]})])

    # Destacar empresas específicas com negrito
    top_10_ano['nome_fantasia'] = top_10_ano['nome_fantasia'].apply(lambda x: f"<b>{x}</b>" if x in empresas_para_incluir else x)

    # Criar o gráfico de barras
    fig_ano = px.bar(top_10_ano, x='nome_fantasia', y='counts', title=f"Top 10 Empresas no Ano Atual", text='counts', color_discrete_sequence=cores)
    fig_ano.update_traces(texttemplate='%{text}', textposition='outside')
    fig_ano.update_layout(xaxis_title='Nome da Empresa', yaxis_title='Número de Reclamações')
    st.plotly_chart(fig_ano)

    # 4. Gráfico de Situação das Reclamações por Empresa
    st.header('Situação das Reclamações por Empresa')
    selected_month_situacao = st.selectbox('Selecione o mês para ver a situação das reclamações', options=dados_filtrados['mes'].unique())

    # Filtrar os dados para o mês selecionado
    situacao_data = dados_filtrados[dados_filtrados['mes'] == selected_month_situacao]

    # Obter as 10 empresas com mais reclamações
    top_10_empresas = situacao_data['nome_fantasia'].value_counts().head(10).index.tolist()

    # Adicionar suas empresas à lista das 10 principais se ainda não estiverem
    top_10_empresas = list(set(top_10_empresas) | set(empresas_para_incluir))

    # Filtrar os dados para incluir apenas as empresas em top_10_empresas
    situacao_data = situacao_data[situacao_data['nome_fantasia'].isin(top_10_empresas)]

    # Contar as ocorrências de cada situação por empresa
    situacao_counts = situacao_data.groupby(['nome_fantasia', 'situacao']).size().reset_index(name='counts')

    # Criar o gráfico
    fig_situacao = px.bar(situacao_counts, x='nome_fantasia', y='counts', color='situacao', title="Situação das Reclamações por Empresa (Top 10)", 
                          text='counts', barmode='group', color_discrete_sequence=cores)
    fig_situacao.update_traces(texttemplate='%{text}', textposition='outside')

    # Destacar nomes das suas empresas em negrito
    fig_situacao.for_each_trace(lambda t: t.update(name='<b>' + t.name + '</b>') if t.name in empresas_para_incluir else ())

    st.plotly_chart(fig_situacao)

with aba4:
        # Normalizar as colunas
    data.columns = data.columns.str.lower().str.strip()
    data = data.applymap(lambda s: s.lower().strip() if isinstance(s, str) else s)

    # Filtro de Segmento de Mercado
    segmento = st.selectbox('Selecione o segmento de mercado', data['segmento_de_mercado_x'].unique(), key='segmento_mercado')

    # Filtro de Segmento Individual - aparece apenas se o segmento for 'seguros, capitalização e previdência'
    if segmento == 'seguros, capitalização e previdência':
        segmento_individual = st.selectbox(
            'Selecione o segmento individual',
            ['capitalização', 'seguros e previdência'],  # Combina 'seguros' e 'previdência' em uma única opção
            key='segmento_individual'
        )
    else:
        segmento_individual = None

    # Filtragem de dados com base nos segmentos
    if segmento == 'seguros, capitalização e previdência':
        if segmento_individual == 'seguros e previdência':
            dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                (data['segmento_individual'].isin(['seguros', 'previdência']))]
        else:
            dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                (data['segmento_individual'] == segmento_individual)]
    else:
        dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]

    # Filtro de Empresas Disponíveis - Adicionando a opção 'Todos'
    empresas_disponiveis = ['Todos'] + list(dados_filtrados['nome_fantasia'].unique())
    empresa_selecionada = st.selectbox('Selecione a empresa', empresas_disponiveis, key='empresa')

    # Aplicar o filtro de empresa, se uma específica for selecionada
    if empresa_selecionada != 'Todos':
        dados_filtrados = dados_filtrados[dados_filtrados['nome_fantasia'] == empresa_selecionada]

    # Filtrar dados para reclamações "Não Resolvida"
    dados_nao_resolvidos = dados_filtrados[dados_filtrados['avaliacao_reclamacao'] == "não resolvida"]

    # Verificação se há dados filtrados
    if dados_filtrados.empty:
            st.write("Nenhum dado disponível para a seleção atual.")
    else:
            st.write(f"Exibindo os dados para: {empresa_selecionada}")

            # 5. Distribuição de Reclamações por Assunto, Grupo de Problema e Problema
            st.header('Distribuição de Reclamações por Assunto, Grupo de Problema e Problema')

            # Agrupar os dados para criar a hierarquia de Assunto, Grupo de Problema e Problema
            tree_map_data = dados_filtrados.groupby(['assunto', 'grupo_problema', 'problema']).size().reset_index(name='counts')

            # Criar o gráfico de mapa de árvore (Tree Map)
            fig_tree_map = px.treemap(tree_map_data, 
                                    path=['assunto', 'grupo_problema', 'problema'], 
                                    values='counts', 
                                    title="Distribuição de Reclamações por Assunto, Grupo de Problema e Problema",
                                    color_discrete_sequence=cores)  # Paleta de cores

            # Exibir o gráfico de árvore
            st.plotly_chart(fig_tree_map)

        # Define a paleta de cores
    cores = ["#27306c", "#08adac", "#d12a78", "#e7ebea", "#8b9db9", "#b5bed1", "#7c7c9c", "#acacc4", "#b4b4c4", "#c4c4d4"]

        # Seleção da análise para diferentes visualizações
    analise_selecionada = st.selectbox(
            'Escolha uma análise:',
            [
                "Frequência de Avaliações da Reclamação",
                "Grupo de Problema vs Nota do Consumidor",
                "Como Comprou/Contratou vs Satisfação"
            ]
        )

        # Condições para as diferentes análises
    if analise_selecionada == "Frequência de Avaliações da Reclamação":
            st.header('Frequência de Avaliações da Reclamação')

            freq_data = dados_filtrados['avaliacao_reclamacao'].value_counts().reset_index()
            freq_data.columns = ['avaliacao_reclamacao', 'frequencia']

            fig_pie = go.Figure()
            fig_pie.add_trace(go.Pie(
                labels=freq_data['avaliacao_reclamacao'],
                values=freq_data['frequencia'],
                hole=0.3,
                hoverinfo="label+value+percent",
                marker=dict(colors=cores)
            ))
            fig_pie.update_layout(title="Distribuição da Frequência de Avaliações de Reclamações")
            st.plotly_chart(fig_pie)

    elif analise_selecionada == "Grupo de Problema vs Nota do Consumidor":
            st.header('Grupo de Problema vs Nota do Consumidor')

            group_data = dados_filtrados.groupby('grupo_problema').agg(
                media_nota=('nota_do_consumidor', 'mean')
            ).reset_index().sort_values(by='media_nota', ascending=False)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=group_data['grupo_problema'],
                y=group_data['media_nota'],
                marker_color=cores[0],
                text=group_data['media_nota'].round(2),
                textposition='outside'
            ))
            fig_bar.update_layout(
                title="Grupo de Problema vs Nota do Consumidor",
                xaxis_title="Grupo de Problema",
                yaxis_title="Nota Média",
                showlegend=False
            )
            st.plotly_chart(fig_bar)

    elif analise_selecionada == "Como Comprou/Contratou vs Satisfação":
            st.header('Como Comprou/Contratou vs Satisfação')

            avg_satisfaction = dados_filtrados.groupby('como_comprou_contratou').agg(
                nota_media=('nota_do_consumidor', 'mean')
            ).reset_index().sort_values(by='nota_media', ascending=False)

            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=avg_satisfaction['como_comprou_contratou'],
                y=avg_satisfaction['nota_media'],
                marker_color=cores[1],
                text=avg_satisfaction['nota_media'].round(2),
                textposition='outside'
            ))
            fig_bar.update_layout(
                title="Como Comprou/Contratou vs Satisfação",
                xaxis_title="Como Comprou/Contratou",
                yaxis_title="Nota Média",
                showlegend=False
            )
            st.plotly_chart(fig_bar)



    # Título da aplicação
    st.title("Análise das Reclamações Não Resolvidas")

    # Estatísticas descritivas
    #st.write("### Estatísticas Descritivas para Reclamações Não Resolvidas:")
    #st.write(dados_nao_resolvidos.describe(include='all'))

    # Análise dos Principais Problemas Identificados
    st.write("### Principais Reclamações Identificadas")

    # Contar as reclamações agrupadas por problema
    problemas_reclamacoes = (
        dados_nao_resolvidos.groupby(['problema'])
        .size()
        .reset_index(name='counts')
    )

    # Obter os 3 principais problemas
    top_problemas = problemas_reclamacoes.sort_values(by='counts', ascending=False).head(3)

    # Exibir os resultados
    for index, row in top_problemas.iterrows():
        st.write(f"- **{row['problema']}**: **{row['counts']}** reclamações.")

    # Gráfico dos principais problemas (horizontal)
    fig_top_problemas = px.bar(top_problemas, x='counts', y='problema',
                                title="Principais Problemas em Reclamações Não Resolvidas",
                                labels={'counts': 'Número de Reclamações'},
                                orientation='h',  # Define a orientação como horizontal
                                color_discrete_sequence=cores)
    st.plotly_chart(fig_top_problemas)

    # Análise Temporal
    dados_nao_resolvidos['data_finalizacao'] = pd.to_datetime(dados_nao_resolvidos['data_finalizacao'])
    reclamacoes_por_mes = dados_nao_resolvidos.resample('M', on='data_finalizacao').size().reset_index(name='counts')

    # Ordenar por data
    reclamacoes_por_mes.columns = ['data_finalizacao', 'total_reclamacoes']
    reclamacoes_por_mes.sort_values(by='data_finalizacao', ascending=True, inplace=True)

    # Gráfico temporal
    st.write("### Análise Temporal das Reclamações Não Resolvidas:")
    fig_temporal = px.line(reclamacoes_por_mes, x='data_finalizacao', y='total_reclamacoes',
                            title="Reclamações Não Resolvidas ao Longo do Tempo",
                            labels={'total_reclamacoes': 'Número de Reclamações'},
                            line_shape='linear')
    st.plotly_chart(fig_temporal)

    # Análise da Faixa Etária
    st.write("### Distribuição das Reclamações Não Resolvidas por Faixa Etária")

    contagem_faixa_etaria = dados_nao_resolvidos['faixa_etaria'].value_counts().reset_index()
    contagem_faixa_etaria.columns = ['faixa_etaria', 'contagem']

    # Gráfico da distribuição das faixas etárias
    fig_faixa_etaria = px.bar(contagem_faixa_etaria.sort_values('contagem', ascending=False), 
                            x='faixa_etaria', y='contagem',
                            title="Distribuição das Reclamações Não Resolvidas por Faixa Etária",
                            labels={'faixa_etaria': 'Faixa Etária', 'contagem': 'Número de Reclamações'},
                            color_discrete_sequence=cores)
    st.plotly_chart(fig_faixa_etaria)

    # Contagem de reclamações por região
    contagem_regiao = dados_nao_resolvidos['regiao'].value_counts().reset_index()
    contagem_regiao.columns = ['regiao', 'contagem']
    contagem_regiao = contagem_regiao.sort_values(by='contagem', ascending=False)

    st.write("### Contagem de Reclamações Não Resolvidas por Região:")
    fig_regiao = px.pie(contagem_regiao, names='regiao', values='contagem', title="Distribuição das Reclamações por Região",
                        color_discrete_sequence=cores)
    st.plotly_chart(fig_regiao)

    # Contagem de reclamações por sexo
    contagem_sexo = dados_nao_resolvidos['sexo'].value_counts().reset_index()
    contagem_sexo.columns = ['sexo', 'contagem']
    contagem_sexo = contagem_sexo.sort_values(by='contagem', ascending=False)

    st.write("### Contagem de Reclamações Não Resolvidas por Sexo:")
    fig_sexo = px.pie(contagem_sexo, names='sexo', values='contagem', title="Distribuição das Reclamações por Sexo",
                    color_discrete_sequence=cores)
    st.plotly_chart(fig_sexo)

    # Insights e Conclusões Dinâmicos
    st.write("### Insights e Conclusões:")

    if not dados_nao_resolvidos.empty:
        # Calculando insights dinâmicos com base nos dados filtrados
        regiao_mais_afetada = contagem_regiao.iloc[0]['regiao'] if not contagem_regiao.empty else "N/A"
        total_reclamacoes = len(dados_nao_resolvidos)
        
        # Calcular sexo predominante
        sexo_predominante = contagem_sexo.iloc[0]['sexo'] if not contagem_sexo.empty else "N/A"
        
        # Calcular faixa etária mais afetada (definindo a variável antes)
        contagem_faixa_etaria = dados_nao_resolvidos['faixa_etaria'].value_counts().reset_index()
        contagem_faixa_etaria.columns = ['faixa_etaria', 'contagem']
        faixa_etaria_predominante = contagem_faixa_etaria.iloc[0]['faixa_etaria'] if not contagem_faixa_etaria.empty else "N/A"

        # Adicionar insights dinâmicos à interface do Streamlit
        st.write(f"1. A maioria das reclamações não resolvidas ocorre na região **{regiao_mais_afetada}**, que é a principal área de preocupação.")
        
        st.write(f"2. Total de reclamações não resolvidas: **{total_reclamacoes}**. Esse número requer atenção para melhorar o processo de resolução.")
        
        st.write(f"3. As reclamações não resolvidas são predominantemente feitas por consumidores do sexo **{sexo_predominante}**, o que pode indicar a necessidade de campanhas direcionadas para este público.")
        
        st.write(f"4. A faixa etária mais afetada é entre **{faixa_etaria_predominante}**, sugerindo que este grupo pode estar enfrentando desafios específicos que precisam ser abordados.")
        
    else:
        st.write("Nenhuma reclamação não resolvida encontrada para os filtros selecionados.")

    # Finalização
    st.write("A análise acima fornece uma visão abrangente das reclamações não resolvidas, permitindo que a ouvidoria tome decisões informadas para melhorar a satisfação do cliente.")

with aba5:
        # Normalizar as colunas para evitar inconsistências
    data['segmento_de_mercado_x'] = data['segmento_de_mercado_x'].str.strip().str.lower()
    data['segmento_individual'] = data['segmento_individual'].str.strip().str.lower()

    # Filtro de Segmento de Mercado
    segmento = st.selectbox('Selecione o segmento de mercado', data['segmento_de_mercado_x'].unique(), key='segmento_mercado_aba5')

    # Filtro de Segmento Individual - Aparece apenas se o segmento for 'Seguros, Capitalização e Previdência'
    if segmento == 'seguros, capitalização e previdência':
        segmento_individual = st.selectbox(
            'Selecione o segmento individual',
            ['capitalização', 'seguros e previdência'],
            key='segmento_individual_aba5'
        )
    else:
        segmento_individual = None

    # Filtragem dos dados para o gráfico, sem excluir outras empresas
    if segmento == 'seguros, capitalização e previdência':
        if segmento_individual == 'seguros e previdência':
            # Filtrar os dados do segmento e do segmento individual (inclui todas as empresas)
            dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                (data['segmento_individual'].isin(['seguros', 'previdência']))]
        else:
            # Filtrar para o segmento de capitalização (todas as empresas)
            dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                (data['segmento_individual'] == 'capitalização')]
    elif segmento == 'administradoras de consórcios':
        # Filtrar o segmento de consórcios (todas as empresas)
        dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]
    elif segmento == 'operadoras de planos de saúde e administradoras de benefícios':
        # Filtrar o segmento de planos de saúde (todas as empresas)
        dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]
    else:
        # Filtrar apenas por segmento de mercado, sem considerar o segmento individual
        dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]

    # Filtrar empresas com pelo menos 10 reclamações
    contagem_reclamacoes = dados_filtrados.groupby('nome_fantasia').size()
    empresas_com_10_ou_mais = contagem_reclamacoes[contagem_reclamacoes >= 10].index
    dados_filtrados = dados_filtrados[dados_filtrados['nome_fantasia'].isin(empresas_com_10_ou_mais)]

    # Limitar o tempo de resposta máximo a 10 dias
    dados_filtrados['tempo_resposta'] = dados_filtrados['tempo_resposta'].clip(upper=10)

    # Média do tempo de resposta da empresa específica
    empresas_especificas = {
        'seguros e previdência': ['previsul'],
        'capitalização': ['cnp capitalização (antiga caixa capitalização)'],
        'administradoras de consórcios': ['cnp consórcio (antiga caixa consórcios)'],
        'operadoras de planos de saúde e administradoras de benefícios': ['odonto empresas']
    }

    # Destacar empresas específicas com base no segmento
    empresas_destaque = []
    if segmento == 'seguros, capitalização e previdência':
        if segmento_individual == 'seguros e previdência':
            empresas_destaque = ['previsul']
        elif segmento_individual == 'capitalização':
            empresas_destaque = ['cnp capitalização (antiga caixa capitalização)']
    elif segmento == 'administradoras de consórcios':
        empresas_destaque = ['cnp consórcio (antiga caixa consórcios)']
    elif segmento == 'operadoras de planos de saúde e administradoras de benefícios':
        empresas_destaque = ['odonto empresas']

    # Calcular a média do tempo de resposta por empresa
    media_por_empresa = dados_filtrados.groupby('nome_fantasia')['tempo_resposta'].mean()

    # Identificar a empresa com menor tempo de resposta (melhor)
    melhor_empresa = media_por_empresa.idxmin()
    melhor_tempo_resposta = media_por_empresa.min()

    # Identificar a empresa com maior tempo de resposta (pior)
    pior_empresa = media_por_empresa.idxmax()
    pior_tempo_resposta = media_por_empresa.max()

    # Criar o Boxplot com todos os dados do mercado
    fig = px.box(dados_filtrados, 
                x='segmento_de_mercado_x', 
                y='tempo_resposta', 
                points="all",  # Exibir todos os pontos
                title="Comparação de Tempo de Resposta - Mercado",
                labels={"segmento_de_mercado_x": "Segmento de Mercado", "tempo_resposta": "Tempo de Resposta (dias)"})

    # Destacar o tempo de resposta das suas empresas
    for empresa in empresas_destaque:
        media_tempo_resposta = dados_filtrados[dados_filtrados['nome_fantasia'] == empresa]['tempo_resposta'].mean()
        
        if not pd.isna(media_tempo_resposta):
            fig.add_trace(go.Scatter(
                x=[segmento],  # Usa o mesmo segmento para o eixo X
                y=[media_tempo_resposta],  
                mode='markers',
                marker=dict(color='red', size=12, symbol='diamond'),
                name=f'{empresa} (Média: {media_tempo_resposta:.2f} dias)'
            ))

    # Destacar a melhor empresa (menor tempo de resposta)
    fig.add_trace(go.Scatter(
        x=[segmento], 
        y=[melhor_tempo_resposta],  
        mode='markers',
        marker=dict(color='green', size=12, symbol='star'),
        name=f'Melhor Empresa: {melhor_empresa} (Média: {melhor_tempo_resposta:.2f} dias)'
    ))

    # Destacar a pior empresa (maior tempo de resposta)
    fig.add_trace(go.Scatter(
        x=[segmento], 
        y=[pior_tempo_resposta],  
        mode='markers',
        marker=dict(color='orange', size=12, symbol='triangle-up'),
        name=f'Pior Empresa: {pior_empresa} (Média: {pior_tempo_resposta:.2f} dias)'
    ))

    # Exibir a média real do mercado para o segmento selecionado
    media_mercado = dados_filtrados['tempo_resposta'].mean()

    # Adicionar anotação no gráfico para exibir a média real
    fig.add_annotation(
        x=0,  # Posição no eixo X (0 para a primeira categoria)
        y=media_mercado,  # Posição no eixo Y com a média
        text=f'Média do Mercado: {media_mercado:.2f} dias',
        showarrow=False,
        font=dict(color="blue", size=12),
        yshift=10
    )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig)

    # Exibir informações sobre a melhor e pior empresa
    st.write(f"A melhor empresa é: {melhor_empresa} com um tempo médio de resposta de {melhor_tempo_resposta:.2f} dias.")
    st.write(f"A pior empresa é: {pior_empresa} com um tempo médio de resposta de {pior_tempo_resposta:.2f} dias.")

    # Gráfico de Boxplot por Região
    st.write("### Boxplot de Tempo de Resposta por Região")

    # Criar o gráfico de boxplot por região
    fig_boxplot_regiao = px.box(
        dados_filtrados, 
        x='regiao', 
        y='tempo_resposta', 
        title="Boxplot de Tempo de Resposta por Região",
        labels={"regiao": "Região", "tempo_resposta": "Tempo de Resposta (dias)"}
    )

    # Função para adicionar melhor, pior e empresa em destaque por região
    def adicionar_empresas_destaque_por_regiao(regiao, dados_filtrados, empresas_destaque, fig):
        # Filtrar dados por região
        dados_por_regiao = dados_filtrados[dados_filtrados['regiao'] == regiao]
        
        # Obter a melhor e pior empresa da região
        media_por_empresa_regiao = dados_por_regiao.groupby('nome_fantasia')['tempo_resposta'].mean()
        melhor_empresa_regiao = media_por_empresa_regiao.idxmin()
        pior_empresa_regiao = media_por_empresa_regiao.idxmax()
        melhor_tempo_resposta_regiao = media_por_empresa_regiao.min()
        pior_tempo_resposta_regiao = media_por_empresa_regiao.max()

        # Adicionar as empresas em destaque no gráfico
        for empresa in empresas_destaque:
            if empresa in media_por_empresa_regiao.index:
                media_tempo_resposta_regiao = media_por_empresa_regiao[empresa]
                fig.add_trace(go.Scatter(
                    x=[regiao],  
                    y=[media_tempo_resposta_regiao],  
                    mode='markers',
                    marker=dict(color='red', size=12, symbol='diamond'),
                    name=f'{empresa} ({regiao} - Média: {media_tempo_resposta_regiao:.2f} dias)'
                ))

        # Adicionar a melhor e pior empresa da região
        fig.add_trace(go.Scatter(
            x=[regiao], 
            y=[melhor_tempo_resposta_regiao],  
            mode='markers',
            marker=dict(color='green', size=12, symbol='star'),
            name=f'Melhor Empresa: {melhor_empresa_regiao} ({regiao} - Média: {melhor_tempo_resposta_regiao:.2f} dias)'
        ))

        fig.add_trace(go.Scatter(
            x=[regiao], 
            y=[pior_tempo_resposta_regiao],  
            mode='markers',
            marker=dict(color='orange', size=12, symbol='triangle-up'),
            name=f'Pior Empresa: {pior_empresa_regiao} ({regiao} - Média: {pior_tempo_resposta_regiao:.2f} dias)'
        ))

    # Adicionar destaques por região
    for regiao in dados_filtrados['regiao'].unique():
        adicionar_empresas_destaque_por_regiao(regiao, dados_filtrados, empresas_destaque, fig_boxplot_regiao)

    # Exibir o gráfico de boxplot por região
    st.plotly_chart(fig_boxplot_regiao)

    # Fechar o bloco HTML customizado
    st.markdown("</div>", unsafe_allow_html=True)


    # Filtro para selecionar a região
    regiao_selecionada = st.selectbox('Selecione a Região para Análise', dados_filtrados['regiao'].unique())

    # Filtrar os dados pela região selecionada
    dados_por_regiao = dados_filtrados[dados_filtrados['regiao'] == regiao_selecionada]

    # Calcular a média do tempo de resposta para TODAS as empresas da região selecionada
    media_geral_regiao = dados_por_regiao['tempo_resposta'].mean()

    # Calcular a média do tempo de resposta por empresa para a região selecionada
    media_por_empresa_regiao = dados_por_regiao.groupby('nome_fantasia')['tempo_resposta'].mean()

    # Identificar as 3 melhores e 3 piores empresas da região (com base no tempo de resposta)
    melhores_empresas_regiao = media_por_empresa_regiao.nsmallest(3)  # Menores tempos de resposta
    piores_empresas_regiao = media_por_empresa_regiao.nlargest(3)  # Maiores tempos de resposta

    # Preparar os dados para o gráfico de barras (incluindo as empresas em destaque)
    empresas_para_grafico = pd.concat([melhores_empresas_regiao, piores_empresas_regiao])

    # Verificar se empresas destacadas (outras empresas de interesse) devem ser adicionadas ao gráfico
    for empresa in empresas_destaque:
        if empresa in media_por_empresa_regiao.index:
            # Garantir que as empresas de destaque sejam adicionadas ao gráfico
            empresas_para_grafico = pd.concat([empresas_para_grafico, pd.Series(media_por_empresa_regiao[empresa], index=[empresa])])

    # Remover duplicatas no caso de alguma empresa já estar nos 3 melhores ou piores
    empresas_para_grafico = empresas_para_grafico[~empresas_para_grafico.index.duplicated(keep='first')]
    # Ordenar os dados do menor para o maior tempo de resposta
    empresas_para_grafico = empresas_para_grafico.sort_values()
    # Criar o gráfico de barras
    fig_barras = go.Figure()

    # Adicionar as barras para as empresas
    fig_barras.add_trace(go.Bar(
        x=empresas_para_grafico.index,
        y=empresas_para_grafico.values,
        marker=dict(
            color=['#71BF44' if x in melhores_empresas_regiao.index else '#D70064' if x in piores_empresas_regiao.index else '#002364' for x in empresas_para_grafico.index]
        ),
        text=[f'{y:.2f} dias' for y in empresas_para_grafico.values],
        textposition='auto'
    ))

    # Adicionar uma linha representando a média geral da região (média de todos os dados filtrados pela região)
    fig_barras.add_trace(go.Scatter(
        x=empresas_para_grafico.index,  # Linha em todas as empresas do gráfico
        y=[media_geral_regiao] * len(empresas_para_grafico),  # Traçar a linha de média geral da região
        mode='lines',
        line=dict(color='blue', dash='dash'),
        name=f'Média Geral da Região ({media_geral_regiao:.2f} dias)'
    ))

    # Ajustar o layout do gráfico
    fig_barras.update_layout(
        title=f'Melhores, Piores e Empresas em Destaque - Região {regiao_selecionada}',
        xaxis_title='Empresas',
        yaxis_title='Tempo de Resposta Médio (dias)',
        showlegend=False  # A legenda pode ser removida ou ajustada conforme a necessidade
    )

    # Exibir o gráfico no Streamlit
    st.plotly_chart(fig_barras)

with aba6:
    
            # Carregar a lista de empresas da coluna 'nome_fantasia' e remover duplicatas
    empresas_disponiveis = data['nome_fantasia'].unique()

    # Input para selecionar as duas empresas
    empresa_1 = st.selectbox(
        "Selecione a primeira empresa:",
        options=empresas_disponiveis,
        key="empresa_1"
    )

    empresa_2 = st.selectbox(
        "Selecione a segunda empresa:",
        options=empresas_disponiveis,
        key="empresa_2"
    )

    # Menu suspenso para selecionar o período
    periodo = st.selectbox(
        "Selecione o período:",
        ("30 Dias", "6 Meses", "2025", "Todos"),
        key="periodo_comparacao"
    )

    # Função para converter strings para float, lidando com porcentagens e texto
    def convert_to_float(value):
        if isinstance(value, str):
            # Remove o símbolo de porcentagem se existir e substitui vírgula por ponto
            value = value.replace('%', '').replace(',', '.').strip()
            # Extrai apenas os números da string
            value = re.sub(r'[^\d.]+', '', value)  # Remove tudo exceto dígitos e ponto
        return float(value)

    # Botão para buscar os dados das duas empresas
    if st.button("Comparar Empresas"):
        if empresa_1 and empresa_2:  # Certificar que ambas as empresas foram preenchidas
            with st.spinner("Buscando dados..."):
                dados_empresa_1 = buscar_dados(empresa_1, periodo)
                dados_empresa_2 = buscar_dados(empresa_2, periodo)

            if dados_empresa_1 is not None and dados_empresa_2 is not None:
                st.success("Dados encontrados!")

                # Garantir que os valores são numéricos (conversão de string para float)
                satisfacao_empresa_1 = convert_to_float(dados_empresa_1['Satisfação com o Atendimento'])
                satisfacao_empresa_2 = convert_to_float(dados_empresa_2['Satisfação com o Atendimento'])

                # Gráfico para Satisfação com o Atendimento
                fig_satisfacao = go.Figure()
                fig_satisfacao.add_trace(go.Bar(
                    x=[empresa_1, empresa_2],
                    y=[satisfacao_empresa_1, satisfacao_empresa_2],
                    name='Satisfação',
                    marker_color=['#27306c', '#08adac'],  # Cores personalizadas
                    text=[f'{satisfacao_empresa_1:.1f}', f'{satisfacao_empresa_2:.1f}'],  # Exibe apenas a nota formatada
                    textposition='auto'
                ))
                fig_satisfacao.update_layout(
                    title="Satisfação com o Atendimento (Nota 1 a 5)",
                    xaxis_title="Empresa",
                    yaxis_title="Nota",
                    yaxis=dict(range=[1, 5]),  # Definindo o limite do eixo Y de 1 a 5
                    bargap=0  # Ajustando o espaçamento entre as barras
                )
                st.plotly_chart(fig_satisfacao)

                # Garantir que o Índice de Solução é numérico
                indice_solucao_empresa_1 = convert_to_float(dados_empresa_1['Índice de Solução'])
                indice_solucao_empresa_2 = convert_to_float(dados_empresa_2['Índice de Solução'])

                # Gráfico para Índice de Solução
                fig_indice_solucao = go.Figure()
                fig_indice_solucao.add_trace(go.Bar(
                    x=[empresa_1, empresa_2],
                    y=[indice_solucao_empresa_1, indice_solucao_empresa_2],
                    name='Índice de Solução',
                    marker_color=['#27306c', '#08adac'],  # Cores personalizadas
                    text=[f'{indice_solucao_empresa_1:.1f}', f'{indice_solucao_empresa_2:.1f}'],  # Exibe apenas o índice de solução
                    textposition='auto'
                ))
                fig_indice_solucao.update_layout(
                    title="Índice de Solução (%)",
                    xaxis_title="Empresa",
                    yaxis_title="Percentual (%)",
                    yaxis=dict(range=[0, 100]),
                    bargap=0
                )
                st.plotly_chart(fig_indice_solucao)

                # Garantir que Reclamações Respondidas são numéricas
                reclamacoes_respondidas_empresa_1 = convert_to_float(dados_empresa_1['Reclamações Respondidas'])
                reclamacoes_respondidas_empresa_2 = convert_to_float(dados_empresa_2['Reclamações Respondidas'])

                # Gráfico para Reclamações Respondidas
                fig_reclamacoes = go.Figure()
                fig_reclamacoes.add_trace(go.Bar(
                    x=[empresa_1, empresa_2],
                    y=[reclamacoes_respondidas_empresa_1, reclamacoes_respondidas_empresa_2],
                    name='Reclamações Respondidas',
                    marker_color=['#27306c', '#08adac'],  # Cores personalizadas
                    text=[f'{reclamacoes_respondidas_empresa_1:.1f}', f'{reclamacoes_respondidas_empresa_2:.1f}'],  # Exibe apenas o percentual de reclamações respondidas
                    textposition='auto'
                ))
                fig_reclamacoes.update_layout(
                    title="Reclamações Respondidas (%)",
                    xaxis_title="Empresa",
                    yaxis_title="Percentual (%)",
                    yaxis=dict(range=[0, 100]),
                    bargap=0
                )
                st.plotly_chart(fig_reclamacoes)

                # Garantir que o Prazo Médio de Respostas é numérico
                prazo_medio_empresa_1 = convert_to_float(dados_empresa_1['Prazo Médio de Respostas'])
                prazo_medio_empresa_2 = convert_to_float(dados_empresa_2['Prazo Médio de Respostas'])

                # Gráfico para Tempo Médio de Respostas
                fig_tempo_medio = go.Figure()
                fig_tempo_medio.add_trace(go.Bar(
                    x=[empresa_1, empresa_2],
                    y=[prazo_medio_empresa_1, prazo_medio_empresa_2],
                    name='Prazo Médio de Respostas',
                    marker_color=['#27306c', '#08adac'],  # Cores personalizadas
                    text=[f'{prazo_medio_empresa_1:.1f}', f'{prazo_medio_empresa_2:.1f}'],  # Exibe apenas o prazo médio
                    textposition='auto'
                ))
                fig_tempo_medio.update_layout(
                    title="Prazo Médio de Respostas (Dias)",
                    xaxis_title="Empresa",
                    yaxis_title="Dias",
                    yaxis=dict(range=[0, 10]),
                    bargap=0
                )
                st.plotly_chart(fig_tempo_medio)

            else:
                st.error("Erro ao buscar os dados de uma ou ambas as empresas.")
        else:
            st.warning("Por favor, selecione os nomes de ambas as empresas.")


with aba7:

    def analise_comp():
        data = pd.read_csv('dados_completos.csv', delimiter=',', encoding='latin-1')
        
        # Converter a coluna 'data_finalizacao' para formato datetime
        data['data_finalizacao'] = pd.to_datetime(data['data_finalizacao'], errors='coerce')

        # Transformar colunas relevantes para minúsculas
        data['segmento_de_mercado_x'] = data['segmento_de_mercado_x'].str.lower()
        data['segmento_individual'] = data['segmento_individual'].str.lower()
        data['nome_fantasia'] = data['nome_fantasia'].str.lower()
        
        # Filtro de Segmento de Mercado
        segmento = st.selectbox('Selecione o segmento de mercado', data['segmento_de_mercado_x'].unique(), key='segmento_mercado_aba7')





        # Filtro de Segmento Individual
        if segmento == 'seguros, capitalização e previdência':
            segmento_individual = st.selectbox(
                'Selecione o segmento individual',
                ['capitalização', 'seguros e previdência'],
                key='segmento_individual_aba7'
            )
        else:
            segmento_individual = None

        # Filtrar os dados para o gráfico
        if segmento == 'seguros, capitalização e previdência':
            if segmento_individual == 'seguros e previdência':
                dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                    (data['segmento_individual'].isin(['seguros', 'previdência']))]
            else:
                dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                    (data['segmento_individual'] == 'capitalização')]
        else:
            dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]

        # Filtro por empresas com no mínimo 10 reclamações
        dados_filtrados = dados_filtrados.groupby('nome_fantasia').filter(lambda x: len(x) >= 10)

        # Definir suas empresas específicas
        empresas_destaque = []
        if segmento == 'seguros, capitalização e previdência':
            if segmento_individual == 'seguros e previdência':
                empresas_destaque = ['previsul']
            elif segmento_individual == 'capitalização':
                empresas_destaque = ['cnp capitalização (antiga caixa capitalização)']
        elif segmento == 'administradoras de consórcios':
            empresas_destaque = ['cnp consórcio (antiga caixa consórcios)']
        elif segmento == 'operadoras de planos de saúde e administradoras de benefícios':
            empresas_destaque = ['odonto empresas']

        # Funções para calcular os indicadores
        def calcular_indice_solucao(grupo):
            total_finalizadas = grupo['situacao'].isin(['Finalizada avaliada', 'Finalizada não avaliada']).sum()
            resolvidas = grupo['avaliacao_reclamacao'] == 'Resolvida'
            nao_avaliadas = grupo['situacao'] == 'Finalizada não avaliada'
            if total_finalizadas > 0:
                return ((resolvidas.sum() + nao_avaliadas.sum()) / total_finalizadas) * 100
            return 0

        def calcular_indice_satisfacao(grupo):
            return grupo['nota_do_consumidor'].mean()

        def calcular_tempo_medio_resposta(grupo):
            return grupo['tempo_resposta'].mean()

        def calcular_percentual_reclamacoes_respondidas(grupo):
            total_reclamacoes = grupo.shape[0]
            total_respondidas = grupo[grupo['respondida'] == 'S'].shape[0]
            return (total_respondidas / total_reclamacoes * 100) if total_reclamacoes > 0 else 0

        # Calcular os indicadores por empresa
        df_indicadores = dados_filtrados.groupby('nome_fantasia').apply(
            lambda grupo: pd.Series({
                'Índice de Solução (%)': calcular_indice_solucao(grupo),
                'Índice de Satisfação': calcular_indice_satisfacao(grupo),
                'Tempo Médio de Resposta': calcular_tempo_medio_resposta(grupo),
                'Percentual de Reclamações Respondidas (%)': calcular_percentual_reclamacoes_respondidas(grupo),
                'Número de Reclamações': grupo.shape[0]
            })
        ).reset_index()

        # Filtrar somente colunas numéricas para calcular a média
        colunas_numericas = ['Índice de Solução (%)', 'Índice de Satisfação', 'Tempo Médio de Resposta', 'Percentual de Reclamações Respondidas (%)']
        media_mercado = df_indicadores[colunas_numericas].mean().to_frame().T


        # Função para criar gráficos com rótulos de índices visíveis e número de reclamações no hover
        def criar_grafico(df, coluna, titulo):
            # Filtrar as 3 melhores e 3 piores empresas com base na coluna
            if coluna == 'Tempo Médio de Resposta':
                melhores_empresas = df.nsmallest(3, coluna)  # As melhores têm menor tempo de resposta
                piores_empresas = df.nlargest(3, coluna)     # As piores têm maior tempo de resposta
            else:
                melhores_empresas = df.nlargest(3, coluna)   
                piores_empresas = df.nsmallest(3, coluna)    

            # Concatenar os dados
            dados_final = pd.concat([melhores_empresas, piores_empresas], ignore_index=True)

            # Adicionar as empresas em destaque ao gráfico (suas empresas)
            dados_destaque = df[df['nome_fantasia'].isin(empresas_destaque)]
            dados_final = pd.concat([dados_final, dados_destaque], ignore_index=True)

            # Criar uma nova coluna para identificar se é melhor, pior ou empresa em destaque
            def classificar_empresa(row):
                if row['nome_fantasia'] in melhores_empresas['nome_fantasia'].values:
                    return 'Melhor'
                elif row['nome_fantasia'] in piores_empresas['nome_fantasia'].values:
                    return 'Pior'
                elif row['nome_fantasia'] in empresas_destaque:
                    return 'Empresa em Destaque'
                else:
                    return 'Outros'

            dados_final['Tipo'] = dados_final.apply(classificar_empresa, axis=1)

            # Ajustar a ordenação com base na coluna
            if coluna == 'Tempo Médio de Resposta':
                dados_final = dados_final.sort_values(by=coluna, ascending=True)  # Ordem crescente para o tempo médio
            else:
                dados_final = dados_final.sort_values(by=coluna, ascending=False)  # Ordem decrescente para os demais indicadores

            # Definir cores personalizadas para cada tipo
            cores = {
                'Melhor': '#71BF44',
                'Pior': '#D70064',
                'Empresa em Destaque': '#002364',  # Azul para as suas empresas em destaque
                'Outros': 'gray'
            }

            # Criar o gráfico
            fig = px.bar(dados_final, 
                        x='nome_fantasia', 
                        y=coluna,
                        title=titulo,
                        labels={'nome_fantasia': 'Nome da Empresa', coluna: titulo},
                        color='Tipo', 
                        text=coluna,  # Exibe o valor do índice como rótulo sobre as barras
                        hover_data={'Número de Reclamações': True},  # Adicionar número de reclamações ao hover
                        color_discrete_map=cores)  # Cores personalizadas

            # Adicionar linha de média do mercado
            fig.add_hline(y=media_mercado[coluna].values[0], line_dash="dash", line_color="orange", 
                        annotation_text="Média do Mercado", annotation_position="top right")

            # Ajustar o tamanho da fonte dos rótulos
            fig.update_traces(texttemplate='%{text:.2f}', textposition='auto')  # Formato dos rótulos com duas casas decimais

            return fig


        # Gráficos para cada indicador
        st.subheader('Índice de Solução (%)')
        fig_solucao = criar_grafico(df_indicadores, 'Índice de Solução (%)', 'Índice de Solução (%)')
        st.plotly_chart(fig_solucao)

        st.subheader('Índice de Satisfação')
        fig_satisfacao = criar_grafico(df_indicadores, 'Índice de Satisfação', 'Índice de Satisfação')
        st.plotly_chart(fig_satisfacao)

        st.subheader('Tempo Médio de Resposta')
        fig_tempo_resposta = criar_grafico(df_indicadores, 'Tempo Médio de Resposta', 'Tempo Médio de Resposta (em dias)')
        st.plotly_chart(fig_tempo_resposta)

        st.subheader('Percentual de Reclamações Respondidas (%)')
        fig_reclamacoes_respondidas = criar_grafico(df_indicadores, 'Percentual de Reclamações Respondidas (%)', 'Percentual de Reclamações Respondidas (%)')
        st.plotly_chart(fig_reclamacoes_respondidas)


        # Subtítulo para a matriz de correlação
        st.subheader('Matriz de Correlação')

        # Calcular a matriz de correlação
        correlacao = df_indicadores[colunas_numericas].corr()

        # Exibir a matriz de correlação
        st.write(correlacao)

        # Função resumida para interpretar a correlação
        def analise_correlacao_resumida(var1, var2, valor):
            if valor > 0.7:
                direcao = "forte e positiva"
                analise = f"Melhorias em {var1} tendem a melhorar {var2} significativamente."
            elif valor > 0.3:
                direcao = "moderada e positiva"
                analise = f"Melhorias em {var1} podem influenciar {var2}, mas outros fatores também importam."
            elif valor > 0:
                direcao = "fraca e positiva"
                analise = f"A relação é pequena, {var1} pode ter pouco impacto em {var2}."
            elif valor < -0.7:
                direcao = "forte e negativa"
                analise = f"Melhorias em {var1} tendem a reduzir {var2} significativamente."
            elif valor < -0.3:
                direcao = "moderada e negativa"
                analise = f"Aumento em {var1} geralmente diminui {var2}, mas não de forma muito forte."
            elif valor < 0:
                direcao = "fraca e negativa"
                analise = f"A relação entre {var1} e {var2} é pequena e inversa."
            else:
                direcao = "nenhuma"
                analise = f"Não há uma correlação significativa entre {var1} e {var2}."

            return f"Correlação entre {var1} e {var2}: {direcao}. {analise}"

        # Aplicar a análise resumida a pares de variáveis da matriz de correlação
        st.write(analise_correlacao_resumida("Índice de Solução (%)", "Índice de Satisfação", correlacao.loc['Índice de Solução (%)', 'Índice de Satisfação']))
        st.write(analise_correlacao_resumida("Índice de Solução (%)", "Tempo Médio de Resposta", correlacao.loc['Índice de Solução (%)', 'Tempo Médio de Resposta']))
        st.write(analise_correlacao_resumida("Índice de Solução (%)", "Percentual de Reclamações Respondidas (%)", correlacao.loc['Índice de Solução (%)', 'Percentual de Reclamações Respondidas (%)']))
        st.write(analise_correlacao_resumida("Índice de Satisfação", "Tempo Médio de Resposta", correlacao.loc['Índice de Satisfação', 'Tempo Médio de Resposta']))
        st.write(analise_correlacao_resumida("Índice de Satisfação", "Percentual de Reclamações Respondidas (%)", correlacao.loc['Índice de Satisfação', 'Percentual de Reclamações Respondidas (%)']))
        st.write(analise_correlacao_resumida("Tempo Médio de Resposta", "Percentual de Reclamações Respondidas (%)", correlacao.loc['Tempo Médio de Resposta', 'Percentual de Reclamações Respondidas (%)']))
        

    def analise_comp3():
        data = pd.read_csv('dados_completos.csv', delimiter=',', encoding='latin-1')
        
        # Converter todas as colunas de interesse para minúsculas
        data['segmento_de_mercado_x'] = data['segmento_de_mercado_x'].str.lower()
        data['segmento_individual'] = data['segmento_individual'].str.lower()
        data['nome_fantasia'] = data['nome_fantasia'].str.lower()
        # Converter a coluna 'data_finalizacao' para o formato DateTime
        data['data_finalizacao'] = pd.to_datetime(data['data_finalizacao'], format='%Y-%m-%d')

        # Criar as colunas de 'mes' e 'ano'
        data['mes'] = data['data_finalizacao'].dt.strftime('%m')  # Extrair o mês no formato MM
        data['ano'] = data['data_finalizacao'].dt.strftime('%Y')  # Extrair o ano no formato YYYY

        # Criar uma coluna de data com base em 'mes' e 'ano'
        data['data'] = pd.to_datetime(data['ano'].astype(str) + '-' + data['mes'].astype(str), format='%Y-%m')


        # Verificar se as colunas necessárias estão presentes
        if 'segmento_de_mercado_x' not in data.columns or 'segmento_individual' not in data.columns or 'nome_fantasia' not in data.columns:
            st.error("As colunas necessárias ('segmento_de_mercado_x', 'segmento_individual', 'nome_fantasia') não estão presentes no dataset.")
            st.stop()

        # Filtro de Segmento de Mercado
        segmento = st.selectbox('Selecione o segmento de mercado', data['segmento_de_mercado_x'].unique(), key='segmento_mercado_aba7')

        # Filtro de Segmento Individual (aparece apenas se o segmento for 'seguros, capitalização e previdência')
        if segmento == 'seguros, capitalização e previdência':
            segmento_individual = st.selectbox(
                'Selecione o segmento individual',
                ['capitalização', 'seguros e previdência'],
                key='segmento_individual_aba7'
            ).lower()  # Converter para minúsculo
        else:
            segmento_individual = None
        # Filtro de Mês
        meses_disponiveis = data['data'].dt.strftime('%Y-%m').unique()
        mes_selecionado = st.multiselect('Selecione o(s) mês(es)', meses_disponiveis)

        # Aplicar o filtro de mês nos dados
        if mes_selecionado:
            data = data[data['data'].dt.strftime('%Y-%m').isin(mes_selecionado)]
        # Definir as empresas de destaque com base no segmento e no segmento individual
        empresas_destaque = []
        if segmento == 'seguros, capitalização e previdência':
            if segmento_individual == 'seguros e previdência':
                empresas_destaque = ['previsul']  # Comparar com Previsul no segmento 'seguros e previdência'
            elif segmento_individual == 'capitalização':
                empresas_destaque = ['cnp capitalização (antiga caixa capitalização)']  # Comparar com CNP Capitalização no segmento 'capitalização'
        elif segmento == 'administradoras de consórcios':
            empresas_destaque = ['cnp consórcio (antiga caixa consórcios)']  # Comparar com CNP Consórcio
        elif segmento == 'operadoras de planos de saúde e administradoras de benefícios':
            empresas_destaque = ['odonto empresas']  # Comparar com Odonto Empresas

        # Verificar se alguma empresa de destaque foi selecionada
        if len(empresas_destaque) == 0:
            st.write("Nenhuma empresa foi selecionada. Verifique os filtros.")
            st.stop()
        else:
            minha_empresa = empresas_destaque[0]  # Definir a primeira empresa da lista como sua empresa

        # Exibir a empresa selecionada para verificação
        st.write(f"Empresa selecionada: {minha_empresa}")

        # Filtrar os dados de acordo com o segmento de mercado e segmento individual (se aplicável)
        if segmento == 'seguros, capitalização e previdência':
            if segmento_individual == 'seguros e previdência':
                dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                    (data['segmento_individual'].isin(['seguros', 'previdência']))]
            else:
                dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                    (data['segmento_individual'] == 'capitalização')]
        else:
            dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]

        # Verificar se há dados após o filtro
        if dados_filtrados.empty:
            st.write("Nenhum dado encontrado para os filtros selecionados.")
            st.stop()

        # Contar quantas vezes cada empresa aparece no dataset filtrado (número de reclamações)
        reclamacoes_por_empresa = dados_filtrados['nome_fantasia'].value_counts().reset_index()
        reclamacoes_por_empresa.columns = ['nome_fantasia', 'Numero_de_Reclamacoes']

        # Verificar se sua empresa está nos dados filtrados
        if minha_empresa not in reclamacoes_por_empresa['nome_fantasia'].values:
            st.write(f"Sua empresa ({minha_empresa}) não foi encontrada no dataset filtrado.")
            st.stop()

        # Encontrar o número de reclamações da sua empresa
        minha_empresa_reclamacoes = reclamacoes_por_empresa[reclamacoes_por_empresa['nome_fantasia'] == minha_empresa]['Numero_de_Reclamacoes'].values[0]

        # Calcular o intervalo de reclamações aceitáveis (15% a mais ou a menos)
        limite_inferior = minha_empresa_reclamacoes * 0.85
        limite_superior = minha_empresa_reclamacoes * 1.15


        # Filtrar as empresas com base no intervalo de reclamações
        empresas_proximas = reclamacoes_por_empresa[
            (reclamacoes_por_empresa['Numero_de_Reclamacoes'] >= limite_inferior) &
            (reclamacoes_por_empresa['Numero_de_Reclamacoes'] <= limite_superior)
        ]

        # Verificar se há empresas próximas para comparar
        if empresas_proximas.empty:
            st.write("Não há empresas com número de reclamações próximo à sua.")
            st.stop()

        # Remover a sua empresa da lista das empresas próximas
        empresas_proximas = empresas_proximas[empresas_proximas['nome_fantasia'] != minha_empresa]

        # Limitar a comparação a 4 empresas além da sua
        if len(empresas_proximas) > 4:
            empresas_proximas = empresas_proximas.head(4)  # Pega apenas as 4 primeiras empresas

        # Adicionar a sua empresa ao dataframe final para visualização
        empresas_comparacao = pd.concat([reclamacoes_por_empresa[reclamacoes_por_empresa['nome_fantasia'] == minha_empresa], empresas_proximas])

        # Criar gráfico de barras para visualizar a comparação
        fig = px.bar(
        empresas_comparacao,
        x='nome_fantasia',
        y='Numero_de_Reclamacoes',
        title='Comparação de Reclamações: Sua Empresa e Empresas Próximas',
        labels={'Numero_de_Reclamacoes': 'Número de Reclamações', 'nome_fantasia': 'Empresa'},
        color='nome_fantasia',
        color_discrete_sequence=[
            "#27306c", "#08adac", "#d12a78", "#e7ebea", 
            "#8b9db9", "#b5bed1", "#7c7c9c", "#acacc4", 
            "#b4b4c4", "#c4c4d4"
            ]
        )

        # Exibir o gráfico no Streamlit
        st.plotly_chart(fig)

        def calcular_indice_solucao(grupo):
            total_finalizadas = grupo['situacao'].isin(['Finalizada avaliada', 'Finalizada não avaliada']).sum()
            resolvidas = grupo['avaliacao_reclamacao'] == 'Resolvida'
            nao_avaliadas = grupo['situacao'] == 'Finalizada não avaliada'
            if total_finalizadas > 0:
                return ((resolvidas.sum() + nao_avaliadas.sum()) / total_finalizadas) * 100
            return 0

        def calcular_indice_satisfacao(grupo):
            return grupo['nota_do_consumidor'].mean()

        def calcular_tempo_medio_resposta(grupo):
            return grupo['tempo_resposta'].mean()

        def calcular_percentual_reclamacoes_respondidas(grupo):
            total_reclamacoes = grupo.shape[0]
            total_respondidas = grupo[grupo['respondida'] == 'S'].shape[0]
            return (total_respondidas / total_reclamacoes * 100) if total_reclamacoes > 0 else 0

        # Calcular o número de reclamações por empresa
        volume_reclamacoes = dados_filtrados['nome_fantasia'].value_counts().reset_index()
        volume_reclamacoes.columns = ['nome_fantasia', 'numero_reclamacoes']

        # Filtrar as empresas com um volume de reclamações próximo
        percentual_limite = 0.15  # 20% de variação
        volume_limite_superior = volume_reclamacoes[volume_reclamacoes['nome_fantasia'].isin(empresas_destaque)]['numero_reclamacoes'].max() * (1 + percentual_limite)
        volume_limite_inferior = volume_reclamacoes[volume_reclamacoes['nome_fantasia'].isin(empresas_destaque)]['numero_reclamacoes'].min() * (1 - percentual_limite)

        # Filtrando as empresas que estão dentro desse intervalo
        empresas_comparacao = volume_reclamacoes[
            (volume_reclamacoes['numero_reclamacoes'] >= volume_limite_inferior) & 
            (volume_reclamacoes['numero_reclamacoes'] <= volume_limite_superior)
        ]['nome_fantasia']

        # Calcular os indicadores apenas para as empresas filtradas
        df_indicadores = dados_filtrados[dados_filtrados['nome_fantasia'].isin(empresas_comparacao)].groupby('nome_fantasia').apply(
            lambda grupo: pd.Series({
                'Índice de Solução (%)': calcular_indice_solucao(grupo),
                'Índice de Satisfação': calcular_indice_satisfacao(grupo),
                'Tempo Médio de Resposta': calcular_tempo_medio_resposta(grupo),
                'Percentual de Reclamações Respondidas (%)': calcular_percentual_reclamacoes_respondidas(grupo),
                'Número de Reclamações': grupo.shape[0]
            })
        ).reset_index()

        # Filtrar somente colunas numéricas para calcular a média
        colunas_numericas = ['Índice de Solução (%)', 'Índice de Satisfação', 'Tempo Médio de Resposta', 'Percentual de Reclamações Respondidas (%)']
        media_mercado = df_indicadores[colunas_numericas].mean().to_frame().T

        # Função para criar gráficos
        # Função para criar gráficos com rótulos de índices visíveis e número de reclamações no hover
        def criar_grafico(df, coluna, titulo):
            # Filtrar as 3 melhores e 3 piores empresas com base na coluna
            if coluna == 'Tempo Médio de Resposta':
                melhores_empresas = df.nsmallest(3, coluna)  # As melhores têm menor tempo de resposta
                piores_empresas = df.nlargest(3, coluna)     # As piores têm maior tempo de resposta
            else:
                melhores_empresas = df.nlargest(3, coluna)   # As melhores têm os maiores valores
                piores_empresas = df.nsmallest(3, coluna)    # As piores têm os menores valores

            # Concatenar os dados
            dados_final = pd.concat([melhores_empresas, piores_empresas], ignore_index=True)

            # Adicionar as empresas em destaque ao gráfico (suas empresas)
            dados_destaque = df[df['nome_fantasia'].isin(empresas_destaque)]
            dados_final = pd.concat([dados_final, dados_destaque], ignore_index=True)

            # Remover duplicatas para evitar sobreposição
            dados_final = dados_final.drop_duplicates(subset=['nome_fantasia'])

            # Criar uma nova coluna para identificar se é melhor, pior ou empresa em destaque
            def classificar_empresa(row):
                if row['nome_fantasia'] in melhores_empresas['nome_fantasia'].values:
                    return 'Melhor'
                elif row['nome_fantasia'] in piores_empresas['nome_fantasia'].values:
                    return 'Pior'
                elif row['nome_fantasia'] in empresas_destaque:
                    return 'Empresa em Destaque'
                else:
                    return 'Outros'

            dados_final['Tipo'] = dados_final.apply(classificar_empresa, axis=1)

            # Ajustar a ordenação com base na coluna
            if coluna == 'Tempo Médio de Resposta':
                dados_final = dados_final.sort_values(by=coluna, ascending=True)  # Ordem crescente para o tempo médio
            else:
                dados_final = dados_final.sort_values(by=coluna, ascending=False)  # Ordem decrescente para os demais indicadores

            # Definir cores personalizadas para cada tipo
            cores = {
                'Melhor': '#71BF44',
                'Pior': '#D70064',
                'Empresa em Destaque': '#002364',  # Azul para as suas empresas em destaque 
                'Outros': 'gray'
            }

            # Criar o gráfico
            fig = px.bar(dados_final, 
                        x='nome_fantasia', 
                        y=coluna,
                        title=titulo,
                        labels={'nome_fantasia': 'Nome da Empresa', coluna: titulo},
                        color='Tipo', 
                        text=coluna,  # Exibe o valor do índice como rótulo sobre as barras
                        hover_data={'Número de Reclamações': True},  # Adicionar número de reclamações ao hover
                        color_discrete_map=cores)  # Cores personalizadas

            # Adicionar linha de média do mercado
            fig.add_hline(y=media_mercado[coluna].values[0], line_dash="dash", line_color="orange", 
                        annotation_text="Média do Mercado", annotation_position="top right")

            # Ajustar o tamanho da fonte dos rótulos
            fig.update_traces(texttemplate='%{text:.2f}', textposition='auto')  # Formato dos rótulos com duas casas decimais

            return fig

            
        # Gráficos para cada indicador usando as empresas filtradas
        st.subheader('Índice de Solução (%)')
        fig_solucao = criar_grafico(df_indicadores, 'Índice de Solução (%)', 'Índice de Solução (%)')
        st.plotly_chart(fig_solucao)
        st.subheader('Índice de Satisfação')
        fig_satisfacao = criar_grafico(df_indicadores, 'Índice de Satisfação', 'Índice de Satisfação')
        st.plotly_chart(fig_satisfacao)

        st.subheader('Tempo Médio de Resposta')
        fig_tempo_resposta = criar_grafico(df_indicadores, 'Tempo Médio de Resposta', 'Tempo Médio de Resposta (em dias)')
        st.plotly_chart(fig_tempo_resposta)

        st.subheader('Percentual de Reclamações Respondidas (%)')
        fig_reclamacoes_respondidas = criar_grafico(df_indicadores, 'Percentual de Reclamações Respondidas (%)', 'Percentual de Reclamações Respondidas (%)')
        st.plotly_chart(fig_reclamacoes_respondidas)

    def analise_top10():
        data = pd.read_csv('dados_completos.csv', delimiter=',', encoding='latin-1')
        
        # Converter todas as colunas de interesse para minúsculas
        data['segmento_de_mercado_x'] = data['segmento_de_mercado_x'].str.lower()
        data['segmento_individual'] = data['segmento_individual'].str.lower()
        data['nome_fantasia'] = data['nome_fantasia'].str.lower()

        # Converter a coluna 'data_finalizacao' para o formato DateTime
        data['data_finalizacao'] = pd.to_datetime(data['data_finalizacao'], format='%Y-%m-%d')

        # Criar as colunas de 'mes' e 'ano'
        data['mes'] = data['data_finalizacao'].dt.strftime('%m')  # Extrair o mês no formato MM
        data['ano'] = data['data_finalizacao'].dt.strftime('%Y')  # Extrair o ano no formato YYYY

        # Criar uma coluna de data com base em 'mes' e 'ano'
        data['data'] = pd.to_datetime(data['ano'].astype(str) + '-' + data['mes'].astype(str), format='%Y-%m')

        # Filtro de Segmento de Mercado
        segmento = st.selectbox('Selecione o segmento de mercado', data['segmento_de_mercado_x'].unique(), key='segmento_mercado_aba7')

        # Filtro de Segmento Individual (aparece apenas se o segmento for 'seguros, capitalização e previdência')
        if segmento == 'seguros, capitalização e previdência':
            segmento_individual = st.selectbox(
                'Selecione o segmento individual',
                ['capitalização', 'seguros e previdência'],
                key='segmento_individual_aba7'
            ).lower()  # Converter para minúsculo
        else:
            segmento_individual = None

        # Filtro de Mês
        meses_disponiveis = data['data'].dt.strftime('%Y-%m').unique()
        mes_selecionado = st.multiselect('Selecione o(s) mês(es)', meses_disponiveis)

        # Filtro de Ano
        anos_disponiveis = data['ano'].unique()
        ano_selecionado = st.selectbox('Selecione o ano', anos_disponiveis)

        # Aplicar o filtro de segmento de mercado e segmento individual
        if segmento == 'seguros, capitalização e previdência':
            if segmento_individual == 'seguros e previdência':
                dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                    (data['segmento_individual'].isin(['seguros', 'previdência']))]
            else:
                dados_filtrados = data[(data['segmento_de_mercado_x'] == segmento) & 
                                    (data['segmento_individual'] == 'capitalização')]
        elif segmento == 'administradoras de consórcios':
            dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]
        elif segmento == 'operadoras de planos de saúde e administradoras de benefícios':
            dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]
        else:
            dados_filtrados = data[data['segmento_de_mercado_x'] == segmento]

        # Aplicar o filtro de ano e mês nos dados
        dados_filtrados = dados_filtrados[dados_filtrados['ano'] == ano_selecionado]

        # Se um ou mais meses forem selecionados, filtrar pelos meses
        if mes_selecionado:
            dados_filtrados = dados_filtrados[dados_filtrados['data'].dt.strftime('%Y-%m').isin(mes_selecionado)]

        # Verificar se há dados após o filtro
        if dados_filtrados.empty:
            st.write("Nenhum dado encontrado para os filtros selecionados.")
            st.stop()

        # Definir empresas destaque com base no segmento e segmento individual
        empresas_destaque = []
        if segmento == 'seguros, capitalização e previdência':
            if segmento_individual == 'seguros e previdência':
                empresas_destaque = ['previsul']  # Comparar com Previsul no segmento 'seguros e previdência'
            elif segmento_individual == 'capitalização':
                empresas_destaque = ['cnp capitalização (antiga caixa capitalização)']  # Comparar com CNP Capitalização
        elif segmento == 'administradoras de consórcios':
            empresas_destaque = ['cnp consórcio (antiga caixa consórcios)']  # Comparar com CNP Consórcio
        elif segmento == 'operadoras de planos de saúde e administradoras de benefícios':
            empresas_destaque = ['odonto empresas']  # Comparar com Odonto Empresas

        # Funções para calcular indicadores
        def calcular_indice_solucao(grupo):
            total_finalizadas = grupo['situacao'].isin(['Finalizada avaliada', 'Finalizada não avaliada']).sum()
            resolvidas = grupo['avaliacao_reclamacao'] == 'Resolvida'
            nao_avaliadas = grupo['situacao'] == 'Finalizada não avaliada'
            if total_finalizadas > 0:
                return ((resolvidas.sum() + nao_avaliadas.sum()) / total_finalizadas) * 100
            return 0

        def calcular_indice_satisfacao(grupo):
            return grupo['nota_do_consumidor'].mean()

        def calcular_tempo_medio_resposta(grupo):
            return grupo['tempo_resposta'].mean()

        def calcular_percentual_reclamacoes_respondidas(grupo):
            total_reclamacoes = grupo.shape[0]
            total_respondidas = grupo[grupo['respondida'] == 'S'].shape[0]
            return (total_respondidas / total_reclamacoes * 100) if total_reclamacoes > 0 else 0

        # Calcular os indicadores para as empresas
        df_indicadores = dados_filtrados.groupby('nome_fantasia').apply(
            lambda grupo: pd.Series({
                'Índice de Solução (%)': calcular_indice_solucao(grupo),
                'Índice de Satisfação': calcular_indice_satisfacao(grupo),
                'Tempo Médio de Resposta': calcular_tempo_medio_resposta(grupo),
                'Percentual de Reclamações Respondidas (%)': calcular_percentual_reclamacoes_respondidas(grupo),
                'Número de Reclamações': grupo.shape[0]
            })
        ).reset_index()

        # Aplicar a regra de no mínimo 10 reclamações apenas para o ano completo
        if not mes_selecionado:  # Se nenhum mês for selecionado, ou seja, a visão for o ano completo
            df_indicadores = df_indicadores[df_indicadores['Número de Reclamações'] >= 10]

        # Adicionar coluna de ranking
        # Adicionar coluna de ranking
        def adicionar_ranking(df, coluna, ascendente=True):
            # Substituir NaN por um valor neutro (como -1) antes de calcular o ranking
            df[coluna] = df[coluna].fillna(-1)
            
            # Criar a coluna de ranking e garantir que seja convertida para inteiro
            df['Rank'] = df[coluna].rank(method='min', ascending=ascendente).astype(int)
            
            # Criar a coluna formatada com o nome e o ranking
            df['Nome (Rank)'] = df['Rank'].astype(str) + "º - " + df['nome_fantasia'].str.capitalize()
            
            return df


        # Função para criar gráficos
        def criar_grafico(df, coluna, titulo, ascendente=True):
            # Top 10 empresas
            top10_empresas = df.nlargest(10, coluna) if not ascendente else df.nsmallest(10, coluna)
            
            # Verificar se a empresa em destaque está no top 10, senão adicioná-la como top 11
            minha_empresa = empresas_destaque[0] if empresas_destaque else None  # Exemplo de empresa em destaque
            if minha_empresa and minha_empresa not in top10_empresas['nome_fantasia'].values:
                empresa_destaque_dados = df[df['nome_fantasia'] == minha_empresa]
                top10_empresas = pd.concat([top10_empresas, empresa_destaque_dados])

            # Adicionar o ranking e a coluna formatada
            top10_empresas = adicionar_ranking(top10_empresas, coluna, ascendente)

            # Cores personalizadas
            color_discrete_map = {minha_empresa: '#27306c'}  # Cor da sua empresa
            color_discrete_map.update({nome: '#08adac' for nome in top10_empresas['nome_fantasia'] if nome != minha_empresa})  # Cor para as outras empresas

            # Criar o gráfico
            fig = px.bar(top10_empresas, x='Nome (Rank)', y=coluna, title=titulo, text=coluna, color='nome_fantasia',
                        color_discrete_map=color_discrete_map, hover_data=['Número de Reclamações'])  # Exibir número de reclamações ao passar o mouse
            
            # Customizar o gráfico
            fig.update_traces(textposition='outside')  # Rótulos de dados do lado de fora
            fig.update_layout(showlegend=False)  # Ocultar legenda para não duplicar informações
            fig.update_layout(yaxis_title=None, xaxis_title=None)  # Remover títulos dos eixos
            fig.update_layout(title_x=0.5)  # Centralizar o título
            
            return fig

        # Criar os gráficos para os diferentes indicadores
        indicadores = {
            'Índice de Solução (%)': 'Top 10 Empresas - Índice de Solução (%)',
            'Índice de Satisfação': 'Top 10 Empresas - Índice de Satisfação',
            'Tempo Médio de Resposta': 'Top 10 Empresas - Tempo Médio de Resposta',
            'Percentual de Reclamações Respondidas (%)': 'Top 10 Empresas - Percentual de Reclamações Respondidas (%)'
        }

        # Exibir os gráficos
        for coluna, titulo in indicadores.items():
            ascendente = True if coluna == 'Tempo Médio de Resposta' else False  # Inverter a ordem para 'Tempo Médio de Resposta'
            fig = criar_grafico(df_indicadores, coluna, titulo, ascendente=ascendente)
            st.plotly_chart(fig, use_container_width=True)

        # Encerrar o contêiner principal
        st.markdown("</div>", unsafe_allow_html=True)

    # Adicionar um seletor de opções
    analise_selecionada = st.selectbox("Selecione a análise", ("Análise Comparativa (Melhores e Piores Empresas)", "Análise Comparativa (Volume Reclamacões Semelhantes)", "Top 10 Empresas"))

    # Exibir a análise baseada na escolha do seletor
    if analise_selecionada == "Análise Comparativa (Melhores e Piores Empresas)":
        analise_comp()
    elif analise_selecionada == "Análise Comparativa (Volume Reclamacões Semelhantes)":
        analise_comp3()
    elif analise_selecionada == "Top 10 Empresas":
        analise_top10()



    
