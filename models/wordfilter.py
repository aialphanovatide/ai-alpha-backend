from openai import OpenAI
import json
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

client = OpenAI(
    api_key=OPENAI_API_KEY,
)

def obtener_keywords_por_coin(json_path, coin_keyword):
    # Obtener la ruta completa al archivo JSON
    script_dir = os.path.dirname(__file__)
    json_path = os.path.join(script_dir, json_path)

    with open(json_path, 'r') as file:
        data = json.load(file)

    resultado = {}

    for item in data:
        if 'coins' in item and isinstance(item['coins'], list):
            for coin in item['coins']:
                if 'coin_keyword' in coin and coin['coin_keyword'] == coin_keyword and 'keywords' in coin:
                    resultado[item['main_keyword']] = coin['keywords']

    return resultado

# Ingresa el nombre del archivo JSON y el coin_keyword que estás buscando
nombre_json = "data.json"
coin_buscada = "gmx"

# Llama a la función y obtén el resultado
resultado_json = obtener_keywords_por_coin(nombre_json, coin_buscada)

# Crea un nuevo archivo JSON con el nombre de la moneda
nombre_archivo_salida = f"{coin_buscada}_keywords.json"
with open(nombre_archivo_salida, 'w') as salida:
    json.dump(resultado_json, salida, indent=2)

# Lee el contenido del archivo recién creado
with open(nombre_archivo_salida, 'r') as archivo_keywords:
    contenido_keywords = json.load(archivo_keywords)

# Genera el prompt para GPT
prompt = f"You are an expert in generating cryptocurrency news and articles. Generate a list of 10 words that I can find in articles using only this list of words {json.dumps(contenido_keywords, indent=2)}. Select the most relevant words that an article could have. "

# Solicita la respuesta a GPT
response = client.chat.completions.create(
    model="gpt-4",
    messages=[{"role": "system", "content": prompt}],
    temperature=0.6,
    max_tokens=1024,
)

# Imprime la respuesta de GPT
print(response.choices[0].message.content)
