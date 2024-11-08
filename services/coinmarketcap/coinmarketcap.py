import os
import requests
from dotenv import load_dotenv

# Load environment variables from the .env file
load_dotenv()
COINMARKET_API_KEY = os.getenv("COINMARKET_API_KEY")

# Gets the Whitepaper of a Token
def get_crypto_metadata(coin_name):

    base_url = "https://pro-api.coinmarketcap.com/v2/cryptocurrency/info"
    headers = {
        'Accepts': 'application/json',
        'X-CMC_PRO_API_KEY': COINMARKET_API_KEY,
    }

    formatted_coin = str(coin_name).upper()

    params = {
        'symbol': formatted_coin,
    }

    try:
        response = requests.get(base_url, headers=headers, params=params)
        
        if response.status_code == 200:
            data = response.json()
            
            credit_count = data['status']['credit_count']

            if 'status' in data and not data['status']['error_message']:

                urls = data['data'][formatted_coin][0]['urls']
                if 'technical_doc' in urls and urls['technical_doc']:
                    return {'whitepaper': urls['technical_doc'][0], 'success': True, 'credit_count': credit_count}
                else:
                    return {'message ': 'No whitepaper was found', 'success': False}
            else:
                return {'message ': data['status']['error_message'], 'success': False}
        else:
            return {'message ': response.content.decode('utf-8'), 'success': False}

    except requests.exceptions.RequestException as e:
        return {'message ': f"Error in coinmarketcap: {str(e)}", 'success': False}
    except Exception as e:
        return {'message ': f"Error in coinmarketcap: {str(e)}", 'success': False}



# coin_name = 'eth'
# print(get_crypto_metadata(coin_name))