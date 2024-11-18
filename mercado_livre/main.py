import os
from utils.mercado_livre_functions import MercadoLivre
from utils.database_functions import insert_into_mercado_livre_database, connect_database
from utils.json_functions import load_json_file
from dotenv import load_dotenv

load_dotenv()
headers = load_json_file(os.getenv('credentials_path'))[1]


ml = MercadoLivre(url='https://lista.mercadolivre.com.br/celulares-telefones/celulares-smartphones/novo/',
                  headers= headers,
                  num_threads= 3)

df = ml.main()

connection = connect_database()

insert_into_mercado_livre_database(connection=connection, df_ml=df)

1

