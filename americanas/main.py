import os
import sys
import random
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.americanas_functions import Americanas
from utils.database_functions import connect_database, insert_into_americanas_database, get_mercado_livre_codes_from_database
from utils.json_functions import load_json_file
from dotenv import load_dotenv


load_dotenv()
headers = load_json_file(os.getenv('credentials_path'))[2]

americanas = Americanas(url = ('https://www.americanas.com.br/categoria/celulares-e-smartphones/g/condicao-novo/tipo-de-produto-celular/tipo-de-produto-Smartphone?viewMode=list'), 
                     headers = headers, 
                     num_threads = 2)
    
americanas_df = americanas.main()

connection = connect_database()

ml_codes = get_mercado_livre_codes_from_database(connection=connection)

matching_codes = americanas.americanas_mercado_livre_matching_codes(df_americanas=americanas_df, df_mercadoLivre=ml_codes)

connection = connect_database()

insert_into_americanas_database(connection = connection, df_americanas= americanas_df)

1