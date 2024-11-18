import sys
import os
import psycopg2
import pandas as pd
import json
import os
import logging
from dotenv import load_dotenv
from utils.json_functions import load_json_file


def connect_database():
    """
    Função utilizada para estabelecer uma conexão com o banco de dados PostgreSQL.

        Retorno:
            Objeto para conexão com o banco.
    """
            
    
    load_dotenv()
    connection_credentials = load_json_file(os.getenv('credentials_path'))

    if connection_credentials is None:
        logging.error('Credenciais não encontradas!')
    
    connection_data = connection_credentials[0]

    try:
        connection = psycopg2.connect(
            host=connection_data['host'],
            database=connection_data['database'],
            user=connection_data['user'],
            password=connection_data['password']
        )
        
    except Exception as e:
        logging.error('Conexão mal sucedida!')
    
    return connection



def insert_into_americanas_database(connection, df_americanas):
        """
        Insere os registros do dataframe americanas em uma tabela do banco de dados nomeada 'americanas'.

            Parâmetros:
                connection: Objeto para manipular a conexão com o banco de dados.
                df_americanas (pd.Dataframe): Dataframe que será inserido no banco de dados.
        """

        def to_lower(value):
            return value.lower() if isinstance(value, str) else value


        cursor = connection.cursor()

        for index, row in df_americanas.iterrows():
            try: 
                command = f"""INSERT INTO americanas (codigo, nome, marca, valor, link)
                VALUES (%s, %s, %s, %s, %s)"""
                cursor.execute(command, (to_lower(row['code']), to_lower(row['title']), to_lower(row['brand']), row['price'], to_lower(row['link'])))
                connection.commit()

                print(f'Inserção da linha {index} bem sucedida')

            except Exception as e:
                print(f'Erro ao inserir a linha {index}: {e}')

        connection.close()



def get_mercado_livre_codes_from_database(connection):
    """
    Lê a tabela do mercado livre criada no banco de dados e salva os dados em um dataframe pandas.
        Parâmetros:
                connection: Objeto para manipular a conexão com o banco de dados.
        Retorno:
                df_mercadoLivre (pd.Dataframe): Dataframe com os dados extraídos do banco de dados.
    """

    query = """select * from mercadoLivre"""
    df_mercadoLivre = pd.read_sql(query, connection)
    connection.close()

    return df_mercadoLivre


def insert_into_mercado_livre_database(connection, df_ml):
    """
    Função para inserir os dados do dataframe em uma tabela do banco de dados.

        Parâmetros:
                connection: Objeto utilizado para manipular a conexão com o banco de dados.
                df_ml (pd.Dataframe): Dataframe que será inserido no banco de dados.
    """

    
    def to_lower(value):
        return value.lower() if isinstance(value, str) else value


    cursor = connection.cursor()

    for index, row in df_ml.iterrows():
        try:
            command = f"""INSERT INTO mercadoLivre (codigo, nome, marca, valor, link)
            VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(command, (to_lower(row['code']), to_lower(row['title']), to_lower(row['brand']), row['price'], to_lower(row['link'])))
            connection.commit()

            print(f'Inserção da linha {index} bem sucedida')

        except Exception as e:
            print(f'Erro ao inserir a linha {index}: {e}')

    connection.close()


if __name__ == '__main__':
    
    load_dotenv()
    headers = load_json_file(os.getenv('credentials_path'))[1]

    1