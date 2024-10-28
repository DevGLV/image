import pandas as pd
import glob
import unicodedata
import os

# Função para normalizar todos os nomes das colunas
def normalize_column_names(df):
    df.columns = [
        unicodedata.normalize('NFKD', col).encode('ASCII', 'ignore').decode('ASCII').strip()  # Remove acentos e caracteres especiais
        .replace(' ', '_')  # Substitui espaços por sublinhados
        .replace('-', '_')  # Substitui traços por sublinhados
        .lower()  # Converte para minúsculas
        for col in df.columns  # Aplica a normalização a cada coluna do DataFrame
    ]
    return df  # Retorna o DataFrame com os nomes das colunas normalizados

# Caminho para a pasta com as bases de dados
pasta_arquivos = r'C:\Users\Gabriel\Documents\govpronto'

# Define o padrão de arquivos CSV na pasta
caminho_arquivos = f'{pasta_arquivos}\\finalizadas_*.csv'

# Lista de arquivos CSV
arquivos = glob.glob(caminho_arquivos)

# Lista para armazenar DataFrames
list_dfs = []

# Lê e normaliza os arquivos CSV
for arquivo in arquivos:
    try:
        # Lê o arquivo CSV com delimitador ; e codificação UTF-8
        df = pd.read_csv(arquivo, delimiter=';', encoding='utf-8', on_bad_lines='skip')
        
        # Normaliza os nomes das colunas
        df = normalize_column_names(df)
        
        # Converte colunas específicas para inteiros
        df['nota_do_consumidor'] = pd.to_numeric(df['nota_do_consumidor'], errors='coerce').astype('Int64')
        df['tempo_resposta'] = pd.to_numeric(df['tempo_resposta'], errors='coerce').astype('Int64')
        
        # Remove duplicatas no DataFrame individual
        df.drop_duplicates(inplace=True)
        
        # Adiciona DataFrame à lista
        list_dfs.append(df)
    except Exception as e:
        print(f"Erro ao processar o arquivo {arquivo}: {e}")

# Verifica se a lista de DataFrames não está vazia antes de concatenar
if list_dfs:
    # Concatena todos os DataFrames
    dados_combinados = pd.concat(list_dfs, ignore_index=True)

    # Remove duplicatas após a concatenação
    dados_combinados.drop_duplicates(inplace=True)

    # Verifica e imprime os nomes das colunas após normalização
    print(f"Nomes das colunas combinadas após a normalização: {dados_combinados.columns.tolist()}")

    # Lista dos segmentos desejados
    segmentos_desejados = [
        'Operadoras de Planos de Saúde e Administradoras de Benefícios',
        'Seguros, Capitalização e Previdência',
        'Administradoras de Consórcios'
    ]

    # Ajuste o nome da coluna para o formato normalizado
    coluna_segmento = 'segmento_de_mercado'  # Nome da coluna após normalização

    # Verifica se a coluna desejada está presente
    if coluna_segmento in dados_combinados.columns:
        # Verifica quantos dados existem na coluna 'segmento_de_mercado'
        print(f"Número de valores únicos na coluna '{coluna_segmento}':")
        print(dados_combinados[coluna_segmento].unique())

        # Normaliza a coluna 'nome_fantasia' para minúsculas para evitar problemas de comparação
        dados_combinados['nome_fantasia'] = dados_combinados['nome_fantasia'].str.lower()

        # Filtra os dados com base nos segmentos desejados
        dados_filtrados = dados_combinados[dados_combinados[coluna_segmento].isin(segmentos_desejados)]

        # Verifica se o DataFrame filtrado está vazio
        if dados_filtrados.empty:
            print(f"Nenhum dado encontrado para os segmentos desejados: {segmentos_desejados}")
        else:
            # Carrega o CSV com os segmentos individuais
            segmento_individual_path = r'C:\Users\Gabriel\Documents\govpronto\segmento_individual.csv'
            df_segmento_individual = pd.read_csv(segmento_individual_path, delimiter=';', encoding='utf-8')

            # Normaliza os nomes das colunas no DataFrame de segmentos individuais
            df_segmento_individual = normalize_column_names(df_segmento_individual)

            # Normaliza a coluna 'nome_fantasia' do DataFrame de segmentos individuais para minúsculas
            df_segmento_individual['nome_fantasia'] = df_segmento_individual['nome_fantasia'].str.lower()

            # Verifica se as colunas necessárias estão presentes
            if 'nome_fantasia' in df_segmento_individual.columns and 'segmento_individual' in df_segmento_individual.columns:
                # Remove duplicatas do DataFrame de segmentos individuais antes do merge
                df_segmento_individual = df_segmento_individual.drop_duplicates(subset='nome_fantasia')

                # Faz o merge entre a base de dados filtrada e o DataFrame de segmentos individuais
                dados_completos = dados_filtrados.merge(df_segmento_individual, how='left', left_on='nome_fantasia', right_on='nome_fantasia')
                
                # Remove duplicatas após o merge
                dados_completos.drop_duplicates(inplace=True)

                # Salva o DataFrame resultante em um novo arquivo CSV com codificação latin-1
                output_path = os.path.join(pasta_arquivos, 'dados_completos.csv')
                dados_completos.to_csv(output_path, index=False, encoding='latin-1')
                print(f"Arquivo '{output_path}' gerado com sucesso.")
            else:
                print("Colunas 'nome_fantasia' e/ou 'segmento_individual' não encontradas no arquivo de segmentos individuais.")
    else:
        print(f"Coluna '{coluna_segmento}' não encontrada nos dados combinados.")
else:
    print("Nenhum dado foi lido dos arquivos CSV fornecidos.")