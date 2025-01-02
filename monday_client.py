import os
import time
from typing import Optional 
from bs4 import BeautifulSoup
from monday import MondayClient 
import requests
import json
from ast import literal_eval
from monday.exceptions import MondayError
from dotenv import load_dotenv
load_dotenv()

MONDAY_API_KEY_NOVATIDE=os.getenv('MONDAY_API_KEY_NOVATIDE')

monday_client = MondayClient(MONDAY_API_KEY_NOVATIDE)
monday_url = "https://api.monday.com/v2"

headers = {
    "Content-Type": "application/json",
    "Authorization": MONDAY_API_KEY_NOVATIDE
}

# Handle the SUM in the formula
def SUM(*args):
    return sum(args)

# ---------------------------- NV BOT ----------------------

# Get all private board, if search param is passed, the board that match the param will be return
def get_all_boards(search_param=None, board_kind='private'):
    """
    Retrieve all private boards, with optional filtering by a search parameter.

    This function queries a Monday.com API to get all boards of a specified kind 
    (default is 'private'). If a search parameter is provided, only the boards 
    whose names contain the search parameter (case-insensitive) will be returned.

    Parameters:
    search_param (str, optional): The term to filter board names by. Defaults to None.
    board_kind (str, optional): The kind of boards to retrieve (e.g., 'private', 'public'). 
                                Defaults to 'private'.
 
    Returns:
    dict: A dictionary containing the result of the operation:
          - 'error' (str or None): Error message if an error occurred, else None.
          - 'success' (bool): True if the operation was successful, False otherwise.
          - 'data' (list or None): A list of boards if successful, else None.
    """
    query = f"""
    query {{
      boards(board_kind: {board_kind}, limit: 200) {{
        id 
        name
        board_kind
      }}
    }}
    """
    
    result = {
        'error': None,
        'success': False,
        'data': None
    }

    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()

        # Check for errors in the response
        if 'errors' in data:
            result['error'] = data['errors']
        else:
            boards = data['data']['boards']
            if search_param:
                # Filter boards based on the search parameter
                boards = [board for board in boards if search_param.lower() in board['name'].lower()]
            
            result['success'] = True
            result['data'] = boards
    
    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


# Get column id, name and value of each column and row in the boards
def get_board_item_general(board_ids, limit=500):
    result = {'error': None, 'data': [], 'success': False}
    
    if not board_ids or not isinstance(board_ids, list):
        result['error'] = 'Invalid board_ids parameter. It should be a non-empty list.'
        return result
    
    if not isinstance(limit, int) or limit <= 0:
        result['error'] = 'Invalid limit parameter. It should be a positive integer.'
        return result

    board_ids_str = ', '.join(map(str, board_ids))
    
    query = f'''
    query {{
        boards(ids: [{board_ids_str}]) {{
            id
            name
            columns {{
                title
                id
            }}
            items_page(limit: {limit}) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                    }}
                }}
            }}
        }}
    }}
    '''
    
    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        
        if 'errors' in data:
            result['error'] = data['errors']
        else:
            boards = data['data']['boards']
            transformed_data = []
            
            for board in boards:
                board_data = {
                    'board_name': board['name'],
                    'board_id': board['id'],
                    'data': []
                }
                
                columns_dict = {col['id']: col['title'] for col in board['columns']}
                
                for item in board['items_page']['items']:
                    item_data = {
                        'column_id': item['id'],
                        'column_name': item['name'],
                        'column_values': [
                            {
                                'column_id': col_val['id'],
                                'column_name': columns_dict[col_val['id']],
                                'column_value': col_val['text']
                            } for col_val in item['column_values'] if col_val['text'] is not None
                        ]
                    }
                    board_data['data'].append(item_data)
                
                transformed_data.append(board_data)
            
            result['data'] = transformed_data
            result['success'] = True

    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
    
    except Exception as e:
        result['error'] = str(e)
    
    return result

# Get column id, name and value of each column and row in the boards
def get_board_item_general_test(board_ids, limit=500):
    result = {'error': None, 'data': [], 'success': False}
    
    if not board_ids or not isinstance(board_ids, list):
        result['error'] = 'Invalid board_ids parameter. It should be a non-empty list.'
        return result
    
    if not isinstance(limit, int) or limit <= 0:
        result['error'] = 'Invalid limit parameter. It should be a positive integer.'
        return result

    board_ids_str = ', '.join(map(str, board_ids))
    
    query = f'''
    query {{
        boards(ids: [{board_ids_str}]) {{
            id
            name
            columns {{
                title
                id
                settings_str
            }}
            items_page(limit: {limit}) {{
                items {{
                    id
                    name
                    column_values {{
                        id
                        text
                    }}
                }}
            }}
        }}
    }}
    '''
    
    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        response.raise_for_status()  # Check for HTTP errors

        data = response.json()
        
        if 'errors' in data:
            result['error'] = data['errors']
        else:
            boards = data['data']['boards']
            transformed_data = []
            
            for board in boards:
                board_data = {
                    'board_name': board['name'],
                    'board_id': board['id'],
                    'data': []
                }
                
                columns_dict = {col['id']: col['title'] for col in board['columns']}
                columns_formulas = {col['id']: col['settings_str'] for col in board['columns']}
                
                for item in board['items_page']['items'][:1]:
                    item_data = {
                        'item_id': item['id'],
                        'item_name': item['name'],
                        'column_values': []
                    }

                    column_values_dict = {col_val['id']: col_val['text'] for col_val in item['column_values']}
                   
                    for col_val in item['column_values']:
                        column_formula = json.loads(columns_formulas[col_val['id']])
                        is_formula = column_formula.get('formula', None)

                        # Replace column IDs with actual values
                        formula = is_formula
                        if is_formula:
                            for column_id, column_value in column_values_dict.items():
                                column_value = column_value if column_value else 0
                                formula = str(formula).replace("\n", "")
                                formula = formula.replace(f"{{{column_id}}}", str(column_value))

                        column_value_final = col_val['text']
                        # Evaluate the formula
                        if is_formula:
                            
                            try:
                                column_value_final = eval(formula, {"SUM": SUM, "__builtins__": {}})
                            except Exception as e:
                                column_value_final = f'Error in formula: {str(e)}'
                       
                        
                        item_data['column_values'].append({
                            'type': 'formula' if is_formula else 'string',
                            'column_id': col_val['id'],
                            'column_name': columns_dict[col_val['id']],
                            'column_value': column_value_final,
                            'formula': formula if is_formula else None,
                            'raw_formula': is_formula if is_formula else None
                        })

                    board_data['data'].append(item_data)
                
                transformed_data.append(board_data)
            
            result['data'] = transformed_data
            result['success'] = True

    except requests.exceptions.RequestException as e:
        result['error'] = str(e)
    
    except Exception as e:
        result['error'] = str(e)
    
    return result


# ----------------------- NV Functions -------------------------

# Creates a new notification in the Monday Notification center - MONDAY NATIVE API
def create_notification(user_id, item_id, value):
    """
    Creates a new notification in the Monday.com Notification center using the MONDAY NATIVE API.

    This function sends a GraphQL mutation to create a notification for a specified user and item.

    Parameters:
    user_id (int): The ID of the user to notify.
    item_id (int): The ID of the item to associate with the notification.
    value (str): The text content of the notification.

    Returns:
    bool: True if the notification was created successfully, False otherwise.
    """

    new_query = f'''
            mutation {{
                create_notification(
                    text: "{value}",
                    user_id: {user_id},
                    target_id: {item_id},
                    target_type: Project
                ) {{
                    id
                }}
            }}
        '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': new_query})
        if response.status_code == 200:
            print(f"Notification created successfully for User ID  {user_id}")
            return True
        else:
            print(f'Error creating new notififcation: {response.content}')
            return False

    except Exception as e:
        print(f'Error found creating update {str(e)}')
        return False

# Calculate the profit of a coin compared to the Buy Price
def calculate_profit(current_price, buy_price, total_quantity):
    try:
        if not current_price or not buy_price or not total_quantity:
            print("Can't calculate profit, not all required values are present")
            return {'message': "Can't calculate profit, not all required values are present", 'status': False}

        # Ensure input values are numeric
        current_price = float(current_price)
        buy_price = float(buy_price)
        total_quantity = float(total_quantity)

        # Ensure non-negative values for prices and number of coins
        if current_price < 0 or buy_price < 0 or total_quantity < 0:
            raise ValueError("Prices and number of coins must be non-negative.")

        # Calculate profit using the provided formula
        profit = (current_price - buy_price) * total_quantity

        return {'message': profit, 'status': True}

    except ValueError as ve:
        print(f"Error: {ve}")
        return {'message': f"Error: {ve}", 'status': False}

    except Exception as e:
        print(f"An unexpected error occurred: {e}" )
        return {'message': f"An unexpected error occurred: {e}", 'status': False}


# Gets the items of the boards along with its, ID, name, column values, buy price of the coin and board details - MONDAY NATIVE API
def get_board_items(board_ids, limit=500):

    query = f'''
        query {{
            boards(ids: {board_ids}) {{
                id
                name
                columns{{
                    title
                    id
                }}
                items_page(limit: {limit}) {{
                    items {{
                        id
                        name
                        column_values {{
                            id
                            text
                        }}
                    }}
                }}
            }}
        }}
    '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        if response.status_code == 200:
            response_data = response.json()

            coins_data = []
            boards = response_data['data']['boards']
            for board in boards:
                board_id = board['id']
                board_name = board['name']
                columns = board['columns']
                items = board['items_page']['items']
                
                column_ids = {}

                # Finds the column ID of the Code column
                code_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Code".casefold().strip():
                        code_column_id = item["id"]
                        column_ids['code_column_id'] = item["id"]
                
                # Finds the column ID of the Quantities column
                quantity_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Quantity".casefold().strip():
                        quantity_column_id = item["id"]
                
                second_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "2nd Quantity".casefold().strip():
                        second_quantity = item["id"]
                
                third_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "3rd Quantity".casefold().strip():
                        third_quantity = item["id"]
                
                fouth_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "4th Quantity".casefold().strip():
                        fouth_quantity = item["id"]
                
                fifth_quantity = None
                for item in columns:
                    if item["title"].casefold().strip() == "5th Quantity".casefold().strip():
                        fifth_quantity = item["id"]

                # Finds the column ID of the Buy Price column
                buy_price_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Buy Price".casefold().strip():
                        buy_price_column_id = item["id"]
                        column_ids['buy_price_column_id'] = item["id"]

                # Finds the column ID of the Valuation Price column
                valuation_price_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Valuation Price".casefold().strip():
                        valuation_price_column_id = item["id"]
                        column_ids['valuation_price_column_id'] = item["id"]

                # Finds the column ID of the % Change column
                percentage_change_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "% Change".casefold().strip():
                        percentage_change_column_id = item["id"]
                        column_ids['percentage_change_column_id'] = item["id"]

                # Finds the column ID of the PProjected Value column
                projected_value_column_id = None
                for item in columns:
                    if item["title"].casefold().strip() == "Projected Value".casefold().strip():
                        projected_value_column_id = item["id"]
                        column_ids['projected_value_column_id'] = item["id"]

                total_coins = 0  # Contador para el total de monedas

                for item in items:
                    item_name = item['name'].casefold().strip()
                    item_id = item['id']
                    column_values = item['column_values']

                    symbol = None
                    buy_price = None
                    total_quantity_value = 0
                    for row in column_values:
                        if row['id'] == code_column_id:
                            symbol = row['text'].casefold().strip()

                        if row['id'] == buy_price_column_id:
                            buy_price = row['text']
                        
                        if quantity_column_id and row['id'] == quantity_column_id:
                            if row['text']:
                                total_quantity_value = float(row['text'])
                        if second_quantity and row['id'] == second_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])
                        if third_quantity and row['id'] == third_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])
                        if fouth_quantity and row['id'] == fouth_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])
                        if fifth_quantity and row['id'] == fifth_quantity:
                            if row['text']:
                                total_quantity_value = total_quantity_value + float(row['text'])

                    coins_data.append({'coin_name': item_name, 'coin_id': item_id, 'board_id': board_id, 
                                      'total_quantity_value': total_quantity_value, 'column_ids': column_ids,
                                    'board_name': board_name, 'coin_symbol': symbol, 'buy_price': buy_price,
                                    })
                    total_coins += 1  # Incrementar el contador por cada moneda encontrada

                print(f"Total number of coins in Monday dashboard '{board_name}': {total_coins}")  # Print informativo

            # Save coins_data to a text file
            # with open('coins_data.txt', 'w') as file:
            #     for coin in coins_data:
            #         file.write(str(coin) + '\n')
            # print('Len coins:', len(coins_data))
            return coins_data
        else:
            print(f'Error getting board items: {response.content}')
            return None

    except Exception as e:
        print(f'Error found getting board items: {str(e)}')
        return None
    
def change_column_value(item_id, board_id, column_id, value):
    print(f"-- Changing column value for Item ID: {item_id} --")
    print(f"Board ID: {board_id}")
    print(f"Column ID: {column_id}")
    print(f"New Value: {value}")

    # If the value is a dictionary, extract the 'usd' value
    if isinstance(value, dict) and 'usd' in value:
        value = value['usd']

    # Convert the value to a string and escape it properly
    value = json.dumps(str(value))

    mutation_query = f'''
    mutation {{
        change_simple_column_value(
            item_id: {item_id},
            board_id: {board_id},
            column_id: "{column_id}",
            value: {value}
        ) {{
            id
        }}
    }}
    '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': mutation_query})
        print('Change column value response', response.content)
        response_data = response.json()
        
        if 'errors' in response_data:
            error_message = response_data['errors'][0]['message']
            print(f'Error changing column value: {error_message}')
            return False
        elif 'data' in response_data:
            print(f'Column value changed successfully')
            return True
        else:
            print('Unexpected response format')
            return False
    except Exception as e:
        print(f'Error found changing column value: {str(e)}')
        return False


def write_new_update(item_id, value):
    """
    Updates the item with a new message using the MONDAY LIBRARY.

    This function attempts to create a new update for a given item ID with the provided value.
    It uses the `monday_client` to interact with the Monday.com API.

    Args:
        item_id (int): The ID of the item to be updated.
        value (str): The value of the update to be written.

    Returns:
        bool: True if the update was successfully created, False otherwise.
    """
    try:
        # Create a new update for the specified item
        update = monday_client.updates.create_update(item_id=item_id, update_value=value)
        print('\nUpdate Monday Item:', update)
        # Check if the update was successfully created
        if 'data' in update and update['data']['create_update']['id']:
            return True
        else:
            return False
    except Exception as e:
        # Handle any exceptions that occur during the update process
        print(f"Error writing new update: {str(e)}")
        return False
    
# Get column IDs for one board - MONDAY LIBRARY
def get_column_ids(board_id):
    try:
        board_info = monday_client.boards.fetch_columns_by_board_id(board_ids=[1716371627])
        columns = board_info['data']['boards'][0]['columns']
        
        columns_data = []
        for column in columns:
            title = column['title']
            column_id = column['id']
            columns_data.append({'column_title': title, 'column_id': column_id})
        return columns_data

    except MondayError as e:
        print(f'Error getting column IDs, Monday error: {str(e)}')
        return None

    except Exception as e:
        print(f'Error getting column IDs, error: {str(e)}')
        return None




# --------- TESTS ------------------------------

# Example usage
# user_email = "s.tamulyte@novatidelabs.com"
# print(get_user_id(user_email))

#print(get_column_ids(board_id=1678221568))
# print(write_new_update(item_id=1355566235, value=f'new test'))
# create_notification(user_id=53919924, item_id=1355566235, value="test")
#print(change_column_value(board_id=1652251054, item_id=1652272796, column_id="valuation_price__1", value=0.407181))


#print(get_board_items(board_ids=[1652251054]))
#print(get_all_boards(search_param="Low Top 20 "))
#print(get_board_item_general_test(board_ids=[1652251054]))


# --------- Coingecko ------------------------------


    
# ================

def get_coin_list(api_key):
    url = "https://pro-api.coingecko.com/api/v3/coins/list"
    params = {
        "include_platform": "false",
        "x_cg_pro_api_key": api_key
    }
    
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return {coin['symbol'].lower(): coin['id'] for coin in response.json()}
    except requests.RequestException as e:
        print(f"Error al obtener la lista de monedas: {e}")
        return {}
    
    
# Cache para almacenar precios
price_cache = {}
cache_duration = 600  # Duración del caché en segundos (10 minutos)

def get_cached_price(symbol):
    current_time = time.time()
    if symbol in price_cache:
        price, timestamp = price_cache[symbol]
        if current_time - timestamp < cache_duration:
            return price
    return None

def cache_price(symbol, price):
    price_cache[symbol] = (price, time.time())

def get_coin_prices(api_key: str, coins: list) -> dict:
    coin_map = get_coin_list(api_key)
    symbol_to_id = {}
    
    for coin in coins:
        symbol = coin['coin_symbol'].lower()
        name = coin['coin_name'].lower()
        
        # Normalizar el nombre y símbolo para mejorar la coincidencia
        normalized_name = name.replace(" ", "").replace("-", "").strip()
        normalized_symbol = symbol.replace(" ", "").replace("-", "").strip()
        
        # Manejo especial para Ethereum
        if (normalized_name == "ethereum" or "Wrapped rsETH" in normalized_name or "wrapped rseth" in normalized_name  or "Mantle Staked Ether" in normalized_name or "mantle staked ether" in normalized_name and normalized_symbol == "eth" or normalized_symbol == "weth" or normalized_symbol == "rseth"):
            symbol_to_id[symbol] = "ethereum"  # Asignar directamente el ID de Ethereum
            continue 

        # Agregar apartado para Frax Share
        if (normalized_name == "fraxshare" or normalized_name == "frax share" and normalized_symbol == "fxs"):
            symbol_to_id[symbol] = "frax-share"  # ID en CoinGecko
            continue 

        # Agregar apartado especial para Lido DAO
        if (normalized_name == "Lido" or normalized_name == "lido" or normalized_name == "Lido dao" or normalized_name == "lido dao" and normalized_symbol == "ldo"):
            symbol_to_id[symbol] = "lido-dao"  # Asignar directamente el ID de Lido DAO
            continue 

        # Agregar apartado especial para Smart Layer Network
        if (normalized_name == "smartlayernetwork" or normalized_name == "smart layer network" and normalized_symbol == "sln"):
            symbol_to_id[symbol] = "smart-layer-network"  # Asignar directamente el ID de Smart Layer Network
            continue 
        
        # Agregar apartado especial para Dogecoin
        if (normalized_name == "dogecoin" and normalized_symbol == "doge"):
            symbol_to_id[symbol] = "dogecoin"  # Asignar directamente el ID de Dogecoin
            continue 
        
        if (normalized_name == "bittensor" or normalized_symbol == "tao"):
            symbol_to_id[symbol] = "bittensor"  # Asignar directamente el ID de Bittensor
            continue 
        
        if (normalized_name == "lido dao" and normalized_symbol == "ldo"):
            symbol_to_id[symbol] = "lido-dao"  # Asignar directamente el ID de Lido DAO
            continue 
        
        if (normalized_name == "pyth network" and normalized_symbol == "pyth"):
            symbol_to_id[symbol] = "pyth-network"  # Asignar directamente el ID de Pyth Network
            continue 
            
        if (normalized_name == "illuvium" and normalized_symbol == "ilv"):
            symbol_to_id[symbol] = "illuvium"  # Asignar directamente el ID de Illuvium
            continue 
        
        if (normalized_name == "skale" or normalized_name == 'SKALE' and normalized_symbol == "skl"):
            symbol_to_id[symbol] = "skale"  # Asignar directamente el ID de SKALE
            continue 
        
        if (normalized_name == "kamino" and normalized_symbol == "kmno"):
            symbol_to_id[symbol] = "kamino"  # Asignar directamente el ID de Kamino
            continue 
        
        if (normalized_name == "chainlink" and normalized_symbol == "link"):
            symbol_to_id[symbol] = "chainlink"  # Asignar directamente el ID de Chainlink
            continue 
        
        if (normalized_name == "blur" and normalized_symbol == "blur"):
            symbol_to_id[symbol] = "blur"  # Asignar directamente el ID de Blur
            continue 
        
        if (normalized_name == "cosmos hub" or normalized_name == "Cosmos Hub" or normalized_name == "Cosmos" or normalized_name == "Cosmos-hub" or normalized_name == "Cosmos-Hub" and normalized_symbol == "atom"):
            symbol_to_id[symbol] = "cosmos"
            continue 
        
        if (normalized_name == "optimism" and normalized_symbol == "op"):
            symbol_to_id[symbol] = "optimism"
            continue 
        
        if (normalized_name == "the graph" or normalized_name == 'The Graph' and normalized_symbol == "grt"):
            symbol_to_id[symbol] = "the-graph"
            continue 
        
        if (normalized_name == "gmx" and normalized_symbol == "gmx"):
            symbol_to_id[symbol] = "gmx"
            continue 
        
        if (normalized_name == "grass" and normalized_symbol == "grass"):
            symbol_to_id[symbol] = "grass"
            continue 
        
        if (normalized_name == "xai" and normalized_symbol == "xai"):
            symbol_to_id[symbol] = "xai"
            continue 
        
        if (normalized_name == "dojo token" and normalized_symbol == "dojo"):
            symbol_to_id[symbol] = "dojo-token"
            continue 
        
      
        if (normalized_name == "akash-network" or normalized_name == "Akash Network" or "akash" in normalized_name and normalized_symbol == "akt"):
            symbol_to_id[symbol] = "akash-network"
            continue 
        
        if (normalized_name == "sei" and normalized_symbol == "sei"):
            symbol_to_id[symbol] = "sei-network"
            continue 
        
        if (normalized_name == "bullbar" or "bullbar" in normalized_name and normalized_symbol == "bull"):
            symbol_to_id[symbol] = "bullbar"
            continue 
        
        if (normalized_name == "aura-network" or "aura" in normalized_name and normalized_symbol == "aura"):
            symbol_to_id[symbol] = "aura-network"
            continue 
        
        if (normalized_name == "hedera" and normalized_symbol == "hbar"):
            symbol_to_id[symbol] = "hedera-hashgraph"
            continue 
        
        if (normalized_name == "edge matrix computing" or "edge matrix computing" in normalized_name or "matrix" in normalized_name and normalized_symbol == "emc"):
            symbol_to_id[symbol] = "edge-matrix-computing"
            continue 
        
        if (normalized_name == "picasso" or "picasso" in normalized_name and normalized_symbol == "pica"):
            symbol_to_id[symbol] = "picasso"
            continue 
        
        if (normalized_name == "wicrypt" or "wicrypt" in normalized_name and normalized_symbol == "wnt"):
            symbol_to_id[symbol] = "wicrypt"
            continue 
        
        if (normalized_name == "ait-protocol" or "ait-protocol" in normalized_name  or "ait" in normalized_name and normalized_symbol == "ait"):
            symbol_to_id[symbol] = "ait-protocol"
            continue 
        
        if (normalized_name == "moe" or "moe" in normalized_name and normalized_symbol == "moe"):
            symbol_to_id[symbol] = "moe"
            continue 
        
        if (normalized_name == "CovalentX" or normalized_name == "covalentx" and normalized_symbol == "cqt"):
            symbol_to_id[symbol] = "covalent-x-token"
            continue 
        
        if (normalized_name == "casper network" and normalized_symbol == "cspr"):
            symbol_to_id[symbol] = "casper-network"
            continue 
        
        if (normalized_name == "ava" or "ava" in normalized_name and normalized_symbol == "ava"):
            symbol_to_id[symbol] = "concierge-io"
            continue
        
        if (normalized_name == "binancecoin" or normalized_name == "BNB" or "WrappedBNB" in normalized_name or "wrappedbnb" in normalized_name and normalized_symbol == "bnb" or normalized_symbol == "wBNB"):
            symbol_to_id[symbol] = "binancecoin"
            continue
        
        if (normalized_name == "soil" and normalized_symbol == "soil"):
            symbol_to_id[symbol] = "soil"
            continue 
        
        if (normalized_name == "realio" and normalized_symbol == "rio"):
            symbol_to_id[symbol] = "realio-network"
            continue 
        
        if (normalized_name == "morpho" and normalized_symbol == "morpho"):
            symbol_to_id[symbol] = "morpho"
            continue 
            
        if (normalized_name == "moby" and normalized_symbol == "moby"):
            symbol_to_id[symbol] = "moby"
            continue 
        
        if (normalized_name == "Fact0rn" or normalized_name == "fact0rn" and normalized_symbol == "FACT" or normalized_symbol == "fact"):
            symbol_to_id[symbol] = "fact0rn"
            continue 
        
        if (normalized_name == "layerai" or normalized_name == "layer ai" or normalized_name == "layerAi" and normalized_symbol == "lai"):
            symbol_to_id[symbol] = "cryptogpt-token"
            continue 
        if (normalized_name == "banana gun" or normalized_name == "bananagun" and normalized_symbol == "BANANA" or normalized_symbol == "banana"):
            symbol_to_id[symbol] = "banana-gun"
            continue 
        
        if (normalized_name == "aerodrome finance" or normalized_name == "aerodromefinance" or normalized_name == "aerodrome" or "aerodrome" in normalized_name and normalized_symbol == "aero" or normalized_symbol == "AERO"):
            symbol_to_id[symbol] = "aerodrome-finance"
            continue 
        
        if (normalized_name == "spacemesh" or normalized_name == "Spacemesh" and normalized_symbol == "SMH"):
            symbol_to_id[symbol] = "spacemesh"
            continue 
        
        if (normalized_name == "injective-protocol" or normalized_name == "Injective"  or "injective" in normalized_name  or "Hydro Staked INJ" in normalized_name or "hydro staked inj" in normalized_name or normalized_name == "Injective Protocol" and normalized_symbol == "inj" or normalized_symbol == "inj" or normalized_symbol == "hinj"):
            symbol_to_id[symbol] = "injective-protocol"
            continue 
        
        
        if (normalized_name == "gearbox" and normalized_symbol == "gear"):
            symbol_to_id[symbol] = "gearbox"
            continue 
        
        if (normalized_name == "bob-token" or normalized_name == "bob" or "bob" in normalized_name or normalized_name == "bob token" or normalized_name == "BOB token" and normalized_symbol == "bob"):
            symbol_to_id[symbol] = "bob-token"
            continue 
            
        if (normalized_name == "bonk" and normalized_symbol == "bonk"):
            symbol_to_id[symbol] = "bonk"
            continue 
        
        if (normalized_name == "decred" and normalized_symbol == "dcr"):
            symbol_to_id[symbol] = "decred"
            continue 
        
        if (normalized_name == "degen base" or "degen" in normalized_name and normalized_symbol == "degen"):
            symbol_to_id[symbol] = "degen-base"
            continue 
        
        if (normalized_name == "inspect" or "inspect" in normalized_name and normalized_symbol == "insp"):
            symbol_to_id[symbol] = "inspect"
            continue 
        
        if (normalized_name == "quant" and normalized_symbol == "qnt"):
            symbol_to_id[symbol] = "quant-network"
            continue 
        
        if (normalized_name == "harmony" and normalized_symbol == "one"):
            symbol_to_id[symbol] = "harmony"
            continue 
        
        if (normalized_name == "cardano" and normalized_symbol == "ada"):
            symbol_to_id[symbol] = "cardano"
            continue 
        
        if (normalized_name == "core" and normalized_symbol == "core"):
            symbol_to_id[symbol] = "coredaoorg"
            continue 
        
        if (normalized_name == "pancakeswap" or normalized_name == "pancake" or "mcake" in normalized_name or normalized_name == "pancake swap" or normalized_name == "pancake swap" and normalized_symbol == "cake" or normalized_symbol == "mcake"):
            symbol_to_id[symbol] = "pancakeswap-token"
            continue 
        
        if (normalized_name == "pepe" or "pepe" in normalized_name and normalized_symbol == "pepe"):
            symbol_to_id[symbol] = "pepe"
            continue 
        
        if (normalized_name == "ape" or normalized_name == "apecoin" or normalized_name == "ape coin" and normalized_symbol == "ape"):
            symbol_to_id[symbol] = "ape"
            continue 
        
        if (normalized_name == "notcoin" and normalized_symbol == "not"):
            symbol_to_id[symbol] = "notcoin"
            continue

        if (normalized_name == "masknetwork"  or normalized_name == "mask network" or normalized_name == "Mask Network" and normalized_symbol == "mask"):
            symbol_to_id[symbol] = "mask-network"
            continue

        if (normalized_name == "flow" and normalized_symbol == "flow"):
            symbol_to_id[symbol] = "flow"
            continue

        if (normalized_name == "measurabledata" or normalized_name == "measurable data" or normalized_name == "measurable data token" and normalized_symbol == "mdt"):
            symbol_to_id[symbol] = "measurable-data-token"
            continue

        if (normalized_name == "dogwifhat" or normalized_name == "dog wif hat" or normalized_name == "dog wif hat" and normalized_symbol == "wif"):
            symbol_to_id[symbol] = "dogwifcoin"
            continue

        if (normalized_name == "celestia" or "Stride Staked TIA" in normalized_name  or "stride staked TIA" in normalized_name or "MilkyWay Staked TIA" in normalized_name or "staked tia" in normalized_name and normalized_symbol == "tia" or normalized_symbol == "milktia" or normalized_symbol == "sttia"):
            symbol_to_id[symbol] = "celestia"
            continue
        
        if (normalized_name == "entangle" and normalized_symbol == "ngl"):
            symbol_to_id[symbol] = "entangle"
            continue
        
        if (normalized_name == "marinade staked sol" or "marinade staked sol" in normalized_name or "marinade" in normalized_name and normalized_symbol == "msol"):
            symbol_to_id[symbol] = "solana"
            continue
        
        if (normalized_name == "metis" or "metis" in normalized_name and normalized_symbol == "metis" or normalized_symbol == "wmetis"):
            symbol_to_id[symbol] = "metis-token"
            continue
        
        if (normalized_name == "decentraland" and normalized_symbol == "mana"):
            symbol_to_id[symbol] = "decentraland"
            continue

        if (normalized_name == "xrp" and normalized_symbol == "xrp"):
            symbol_to_id[symbol] = "ripple"
            continue

        if (normalized_name == "stacks" and normalized_symbol == "stx"):
            symbol_to_id[symbol] = "blockstack"
            continue

        if (normalized_name == "treasure" or "treasure" in normalized_name and normalized_symbol == "magic"):
            symbol_to_id[symbol] = "magic"
            continue

        if (normalized_name == "toncoin" and normalized_symbol == "ton"):
            symbol_to_id[symbol] = "the-open-network"
            continue

        if (normalized_name == "memecoin" and normalized_symbol == "meme"):
            symbol_to_id[symbol] = "memecoin-2"
            continue

        if (normalized_name == "tensor" and normalized_symbol == "tnsr"):
            symbol_to_id[symbol] = "tensor"
            continue

        if (normalized_name == "aethir" and normalized_symbol == "ath"):
            symbol_to_id[symbol] = "aethir"
            continue
        
        if (normalized_name == "usd-coin" or "bridged usdc" in normalized_name or normalized_name == "usdc" and normalized_symbol == "usdc" or normalized_symbol == "m.usdc"):
            symbol_to_id[symbol] = "usd-coin"
            continue
        
        if ("do" in normalized_name and normalized_symbol == "dojo"):
            symbol_to_id[symbol] = "dojo-token"
            continue
        
        if (normalized_name == "mantle"  or "manMantle Staked Ethertle" in normalized_name or "mantle staked ether" in normalized_name or "mantle" in normalized_name and normalized_symbol == "mnt" or normalized_symbol == "meth"):
            symbol_to_id[symbol] = "mantle"
            continue
        
        if (normalized_name == "zeusnetwork" and normalized_symbol == "zeus"):
            symbol_to_id[symbol] = "zeus-network"
            continue

        if (normalized_name == "joe"  or "sjoe" in normalized_name and normalized_symbol == "joe" or normalized_symbol == "sjoe"):
            symbol_to_id[symbol] = "joe"
            continue

        if (normalized_name == "thesandbox" or normalized_name == "The Sandbox" or normalized_name == "the sandbox" and normalized_symbol == "sand"):
            symbol_to_id[symbol] = "the-sandbox"
            continue

        if (normalized_name == "mantra" and normalized_symbol == "om"):
            symbol_to_id[symbol] = "mantra-dao"
            continue

        if (normalized_name == "worldcoin" and normalized_symbol == "wld"):
            symbol_to_id[symbol] = "worldcoin-wld"
            continue

        if (normalized_name == "maker" and normalized_symbol == "mkr"):
            symbol_to_id[symbol] = "maker"
            continue

        if (normalized_name == "conflux" and normalized_symbol == "cfx"):
            symbol_to_id[symbol] = "conflux-token"
            continue

        if (normalized_name == "oasis" and normalized_symbol == "rose"):
            symbol_to_id[symbol] = "oasis-network"
            continue

        if (normalized_name == "neo" and normalized_symbol == "neo"):
            symbol_to_id[symbol] = "neo"
            continue

        if (normalized_name == "pixels" and normalized_symbol == "pixel"):
            symbol_to_id[symbol] = "pixels"
            continue

        if (normalized_name == "sillydragon" or normalized_name == "silly dragon" and normalized_symbol == "silly"):
            symbol_to_id[symbol] = "silly-dragon"
            continue

        if (normalized_name == "polylastic" and normalized_symbol == "polx"):
            symbol_to_id[symbol] = "polylastic"
            continue

        if (normalized_name == "xai" and normalized_symbol == "xai"):
            symbol_to_id[symbol] = "xai-blockchain"
            continue

        if (normalized_name == "hacken" and normalized_symbol == "hai"):
            symbol_to_id[symbol] = "hackenai"
            continue

        if (normalized_name == "acent" and normalized_symbol == "ace"):
            symbol_to_id[symbol] = "acent"
            continue
        
        
        if (normalized_name == "empirex" or "empire" in normalized_name and normalized_symbol == "x"):
            symbol_to_id[symbol] = "x-empire"
            continue
        
        
        if (normalized_name == "brett" or "brett" in normalized_name and normalized_symbol == "brett"):
            symbol_to_id[symbol] = "based-brett"
            continue
        
        
        if (normalized_name == "landshare" or "landshare" in normalized_name and normalized_symbol == "land"):
            symbol_to_id[symbol] = "landshare"
            continue
        
        
        if (normalized_name == "phoenix" or "phoenix" in normalized_name and normalized_symbol == "phb"):
            symbol_to_id[symbol] = "phoenix-global"
            continue
        
        if (normalized_name == "banana" or "banana" in normalized_name and normalized_symbol == "banana"):
            symbol_to_id[symbol] = "banana-gun"
            continue
        
        if (normalized_name == "aimedis" or "aimedis" in normalized_name and normalized_symbol == "aimx"):
            symbol_to_id[symbol] = "aimedis-new"
            continue
        
        match_found = False
        for coingecko_id, coingecko_data in coin_map.items():
            if isinstance(coingecko_data, dict):
                coingecko_normalized_name = coingecko_data['name'].lower().replace(" ", "").replace("-", "").strip()
                coingecko_normalized_id = coingecko_data['id'].lower().replace(" ", "").replace("-", "").strip()
                coingecko_normalized_symbol = coingecko_data['symbol'].lower().replace(" ", "").replace("-", "").strip()
                
                # Verificar coincidencias exactas
                if normalized_name == coingecko_normalized_id and normalized_symbol == coingecko_normalized_symbol:
                    symbol_to_id[symbol] = coingecko_id
                    match_found = True
                    break

        
        # Si no se encontró coincidencia, volver al método anterior
        if not match_found:
            if normalized_symbol in coin_map:
                symbol_to_id[symbol] = coin_map[normalized_symbol]
            elif normalized_name in coin_map:
                symbol_to_id[symbol] = coin_map[normalized_name]

    url = "https://pro-api.coingecko.com/api/v3/simple/price"
    prices = {}
    batch_size = 50

    for i in range(0, len(symbol_to_id), batch_size):
        batch = list(symbol_to_id.values())[i:i+batch_size]
        params = {
            "ids": ",".join(batch),
            "vs_currencies": "usd",
            "x_cg_pro_api_key": api_key
        }

        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            for symbol, id in symbol_to_id.items():
                if id in data:
                    # Check cache first
                    cached_price = get_cached_price(symbol)
                    if cached_price is not None:
                        prices[symbol] = cached_price
                    else:
                        prices[symbol] = data[id]
                        cache_price(symbol, data[id])  # Cache the new price
            time.sleep(1)
        except requests.RequestException as e:
            print(f"Error al obtener datos: {e}")

    return prices



def update_coin_prices(json_data):
    # Iterate through each board in the JSON data
    for board in json_data['boards']:
        coins = board['coins']  # Get the coins for the current board
        board_id = board['board_id']  # Get the board_id for the current board
        prices = get_coin_prices("CG-4uzPgs2oyq4aL8vqJEoB2zfD", coins)  # Get prices for the coins

        for coin in coins:
            symbol = coin['coin_symbol'].lower()
            if symbol in prices:
                price_data = prices[symbol]  # Obtener el diccionario de precios
                price = price_data.get('usd', 0)  # Acceder al valor en 'usd', o usar 0 si no existe
                
                # Aquí se aplica el nuevo código para formatear el valor de valuation_price
                valuation_price = price if price else 0  # Cambiar a 0 si no existe
                try:
                    valuation_price = float(valuation_price)  # Intentar convertir a float
                    # Formatear el precio de valoración para que tenga hasta 7 decimales solo si es necesario
                    valuation_price = f"{valuation_price:.7f}".rstrip('0').rstrip('.')  # Limitar a 7 decimales y eliminar ceros innecesarios
                except ValueError:
                    valuation_price = "0.0000000"  # Si falla, asignar 0 con 7 decimales

                # Si price es un número, usarlo directamente
                coin['column_ids']['updated_price'] = valuation_price
                
                # Update the price in Monday.com using the board_id of the current board
                result = change_column_value(
                    item_id=int(coin['coin_id']),
                    board_id=int(board_id),
                    column_id=coin['column_ids']['valuation_price_column_id'],
                    value=valuation_price  # Usar el valor formateado
                )
                
                if result:
                    print(f"Precio actualizado para {coin['coin_name']} ({symbol}) en el board '{board['board_name']}'")
                else:
                    print(f"Error al actualizar el precio para {coin['coin_name']} ({symbol}) en el board '{board['board_name']}'")
            else:
                coin['column_ids']['updated_price'] = None
                print(f"No se encontró precio para {coin['coin_name']} ({symbol}) en el board '{board['board_name']}'")
    
    return json_data

def search_and_get_board_items(search_param):
    board_info = get_all_boards(search_param=search_param)
    
    # Initialize the result structure
    result = {"boards": []}

    if board_info['success'] and len(board_info['data']) > 0:
        # Filter boards that do not contain "Subitems" in their name
        filtered_boards = [board for board in board_info['data'] if "Subitems" not in board['name']]
        
        # Check if there are filtered boards
        if filtered_boards:
            # Get the IDs of the selected boards
            board_ids = [int(board['id']) for board in filtered_boards]
            
            for board_id in board_ids:
                # Get the current board's details
                current_board = next(board for board in filtered_boards if int(board['id']) == board_id)
                
                # Get items for the current board
                items = get_board_items(board_ids=[board_id])  # Ensure this function fetches items for the specific board
                
                # Create a board entry for the current board
                board_entry = {
                    "board_id": board_id,
                    "board_name": current_board['name'],  # Use the correct board name
                    "board_kind": current_board['board_kind'],  # Use the correct board kind
                    "coins": []  # Initialize coins list
                }
                
                # Add items to the coins list
                for item in items:
                    formatted_item = {
                        "coin_name": item.get("coin_name", ""),
                        "coin_symbol": item.get("coin_symbol", ""),
                        "coin_id": item.get("coin_id", ""),
                        "total_quantity_value": item.get("total_quantity_value", 0),
                        "buy_price": item.get("buy_price", None),
                        "column_ids": item.get("column_ids", {})
                    }
                    board_entry['coins'].append(formatted_item)  # Add the formatted item to the coins list
                
                # Append the board entry to the result
                result['boards'].append(board_entry)

            # Save the result to a single JSON file after processing all boards
            save_to_json(result)
            return result
        else:
            return {"error": "No boards found with that name."}
    else:
        return {"error": "No boards found with that name."}

def save_to_json(data):
    json_file_name = 'all_boards_data.json'  # Name of the final JSON file

    # Save the result to the JSON file
    with open(json_file_name, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"Saved all board data to '{json_file_name}'")

def format_board_items_to_json(board_items):
    if not board_items:
        return json.dumps({"error": "No hay items en el tablero"}, indent=2)
    
    formatted_items = []
    for item in board_items:
        formatted_item = {
            "coin_name": item.get("coin_name", ""),
            "coin_symbol": item.get("coin_symbol", ""),
            "coin_id": item.get("coin_id", ""),
            "total_quantity_value": item.get("total_quantity_value", 0),
            "buy_price": item.get("buy_price", None),
            "column_ids": item.get("column_ids", {})
        }
        formatted_items.append(formatted_item)
    
    result = {
        "board_id": board_items[0].get("board_id", ""),
        "board_name": board_items[0].get("board_name", ""),
        "board_kind": board_items[0].get("board_kind", ""),
        "coins": formatted_items
    }
    
    return json.dumps(result, indent=2)


def get_formatted_board_items(search_param):
    """
    Retrieve and format board items based on the search parameter.

    Parameters:
    - search_param: The parameter to search for in board names.

    Returns:
    - JSON formatted string of the board items or an error message.
    """
    # Get the board information and its items
    board_result = search_and_get_board_items(search_param)

    # Check if board_result is valid
    if board_result is None or 'board_items' not in board_result:
        print("Error: Board result is None or does not contain 'board_items'.")
        return json.dumps({"error": "Board not found or insufficient results"}, indent=2)

    # Format the items from the board
    formatted_items = []
    for item in board_result['board_items']:
        formatted_item = {
            "coin_name": item.get("coin_name", ""),
            "coin_symbol": item.get("coin_symbol", ""),
            "coin_id": item.get("coin_id", ""),
            "total_quantity_value": item.get("total_quantity_value", 0),
            "buy_price": item.get("buy_price", None),
            "column_ids": item.get("column_ids", {})
        }
        formatted_items.append(formatted_item)

    # Access the first board's details from the boards list
    if board_result['boards']:
        first_board = board_result['boards'][0]
        result = {
            "board_id": first_board['id'],
            "board_name": first_board['name'],
            "board_kind": first_board['board_kind'],
            "coins": formatted_items
        }
    else:
        print("Error: No boards found.")
        return json.dumps({"error": "No boards found."}, indent=2)

    # Print the current working directory
    current_directory = os.getcwd()
    print(f"Current working directory: {current_directory}")

    # Name of the JSON file
    json_file_name = 'all_board_items.json'

    # Check if the file already exists
    if not os.path.exists(json_file_name):
        print(f"The file '{json_file_name}' does not exist. A new one will be created.")

    # Save the result to a JSON file
    try:
        with open(json_file_name, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"Data successfully saved to '{json_file_name}'.")
    except Exception as e:
        print(f"Error saving the JSON file: {str(e)}")

    return json.dumps(result, indent=2)



def get_specific_wallets_data():
    """
    Get detailed information from specific wallet groups in CEX Master Board.
    """
    print("Starting function...")
    result = {'success': False, 'data': {}, 'error': None}
    board_name = "cex master board"
    target_groups = [
        {"title": "Rajan's Tangem Wallet #2 (from NV OKX)", "id": "new_group26777__1"},
        {"title": "Aman's Tangem Wallet #1 (from OKX Sepia)", "id": "new_group81323__1"},
        {"title": "CLOSED - OKX Sepia Wallet", "id": "group_title"},
        {"title": "CLOSED - OKX Sepia International Wallet", "id": "new_group5225__1"},
        {"title": "Rajan's Tangem Wallet #1 (from KuCoin)", "id": "new_group32432__1"},
        {"title": "Aman's Tangem Wallet #2 (from Bybit Sepia)", "id": "new_group37173__1"},
        {"title": "Aman's Tangem Wallet #3 (from Rabby BNB)", "id": "new_group_mkk9zkqg"}
    ]
    
    try:
        # Step 1: Get board ID and groups (esto ya funciona, lo dejamos igual)
        print("Step 1: Getting board info...")
        initial_query = '''
        query {
            boards(limit: 100) {
                id
                name
                groups {
                    id
                    title
                }
            }
        }
        '''
        
        response = requests.post(monday_url, headers=headers, json={'query': initial_query})
        response.raise_for_status()
        data = response.json()
        
        boards = data['data']['boards']
        target_board = next((board for board in boards if board['name'].lower() == board_name.lower()), None)
        
        if not target_board:
            print(f"Board '{board_name}' not found")
            result['error'] = f"Board '{board_name}' not found"
            return result
            
        print(f"Found board: {target_board['name']} (ID: {target_board['id']})")
        
        # Step 2: Get items
        print("\nStep 2: Getting items...")
        items_query = '''
        query {
            boards(ids: [1652251054]) {
                name
                columns {
                    id
                    title
                }
                items_page(limit: 100) {
                    cursor
                    items {
                        id
                        name
                        group {
                            id
                            title
                        }
                        column_values {
                            id
                            text
                        }
                    }
                }
            }
        }
        '''
        
        print("Executing items query...")
        all_items = []
        cursor = None
        
        # Get first response to create columns dictionary
        response = requests.post(monday_url, headers=headers, json={'query': items_query})
        print(f"Initial response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"Response content: {response.text}")
            response.raise_for_status()
            
        items_data = response.json()
        if 'errors' in items_data:
            print(f"GraphQL errors: {items_data['errors']}")
            result['error'] = items_data['errors']
            return result
        
        # Create columns dictionary from first response
        columns_dict = {
            col['id']: col['title'] 
            for col in items_data['data']['boards'][0]['columns']
        }
        print(f"Found {len(columns_dict)} columns")
        
        # Process first page of items
        page_items = items_data['data']['boards'][0]['items_page']['items']
        all_items.extend(page_items)
        
        # Get cursor for next page
        cursor = items_data['data']['boards'][0]['items_page'].get('cursor')
        
        # Get remaining pages
        while cursor:
            current_query = items_query.replace('items_page(limit: 100)', f'items_page(limit: 100, cursor: "{cursor}")')
            
            response = requests.post(monday_url, headers=headers, json={'query': current_query})
            print(f"Response status: {response.status_code}")
            
            if response.status_code != 200:
                print(f"Response content: {response.text}")
                response.raise_for_status()
                
            items_data = response.json()
            if 'errors' in items_data:
                print(f"GraphQL errors: {items_data['errors']}")
                result['error'] = items_data['errors']
                return result
                
            page_items = items_data['data']['boards'][0]['items_page']['items']
            all_items.extend(page_items)
            
            # Get cursor for next page
            cursor = items_data['data']['boards'][0]['items_page'].get('cursor')
                
        print(f"Found {len(all_items)} total items")
        
        # Imprimir todos los grupos que tienen items
        print("\nGroups with items:")
        groups_with_items = {}
        for item in all_items:
            group_id = item['group']['id']
            group_title = item['group']['title']
            if group_id not in groups_with_items:
                groups_with_items[group_id] = {'title': group_title, 'count': 0}
            groups_with_items[group_id]['count'] += 1
            
        for group_id, info in groups_with_items.items():
            print(f"Group ID: {group_id} - Title: {info['title']} - Items: {info['count']}")
        
        # Process items for each target group
        filtered_result = {'success': True, 'data': {}, 'error': None}
        
        for group in target_groups:
            print(f"\nProcessing group: {group['title']} (ID: {group['id']})")
            group_items = [
                item for item in all_items
                if item['group']['id'] == group['id']
            ]
            
            print(f"Found {len(group_items)} items in group")
            processed_items = []
            
            for item in group_items:
                # Obtenemos los valores de las columnas que necesitamos
                valuation_price = next(
                    (col for col in item['column_values'] 
                     if columns_dict[col['id']] == 'Valuation Price'), 
                    {'id': '', 'text': ''}
                )
                
                # Procesamos cada item con solo los campos necesarios
                processed_item = {
                    'id': item['id'],
                    'name': item['name'],
                    'columns': {
                        'Subitems': next(
                            (
                                {'id': col['id'], 'value': col.get('text')}
                                for col in item['column_values']
                                if columns_dict[col['id']] == 'Subitems'
                            ),
                            {'id': '', 'value': None}
                        ),
                        'Code': next(
                            (
                                {'id': col['id'], 'value': col.get('text')}
                                for col in item['column_values']
                                if columns_dict[col['id']] == 'Code'
                            ),
                            {'id': '', 'value': ''}
                        ),
                        'Valuation Price': {
                            'id': valuation_price['id'],
                            'value': valuation_price.get('text', '')
                        }
                    }
                }
                processed_items.append(processed_item)
            
            if processed_items:
                filtered_result['data'][group['title']] = processed_items
                print(f"Processed {len(processed_items)} items in {group['title']}")
        
        # Save results to JSON file
        json_filename = 'all_items_minimal.json'
        try:
            with open(json_filename, 'w', encoding='utf-8') as f:
                json.dump(filtered_result, f, ensure_ascii=False, indent=2)
            print(f"\nResults saved to {json_filename}")
        except Exception as e:
            print(f"\nError saving results to JSON: {str(e)}")
        
        return filtered_result
    
    except requests.exceptions.RequestException as e:
        print(f"Request error occurred: {str(e)}")
        result['error'] = f"Request error: {str(e)}"
    except Exception as e:
        print(f"Unexpected error occurred: {str(e)}")
        result['error'] = f"Unexpected error: {str(e)}"
        
    print("Function completed")
    return result

def get_sentx_price() -> Optional[float]:
    """
    Obtiene el precio actual de SENTX usando web scraping de GeckoTerminal.
    
    Returns:
        float: El precio actual de SENTX, o None si no se puede obtener
    """
    try:
        # Headers necesarios para simular un navegador
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0'
        }

        url = "https://www.geckoterminal.com/hedera-hashgraph/pools/0x77944cda575c4ac09cbb72809c2551b3f134b4e0"
        print(f"Requesting page from: {url}")
        
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Parsear el HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Buscar el elemento específico que contiene el precio
        price_element = soup.find('span', id='pool-price-display')
        
        if price_element:
            # Obtener el span interno que contiene el precio
            price_span = price_element.find('span')
            if price_span:
                # Extraer el precio y limpiarlo
                price_text = price_span.text.strip()
                price = float(price_text.replace('$', '').replace(',', ''))
                
                # Crear el formato de datos requerido
                output_data = {
                    "coins": [{
                        "coin_name": "SENTX",
                        "coin_symbol": "SENTX",
                        "buy_price": price
                    }]
                }
                
                # Guardar en archivo
                with open('sentx_data.json', 'w') as f:
                    json.dump(output_data, f, indent=4)
                
                return price
            else:
                print("Price span not found inside pool-price-display")
        else:
            print("Price element not found")
            # Para debug, guardar el HTML
            with open('debug_page.html', 'w', encoding='utf-8') as f:
                f.write(response.text)
            print("Saved HTML to debug_page.html for inspection")
        
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        if hasattr(e, 'response') and hasattr(e.response, 'text'):
            print(f"Response text: {e.response.text[:500]}...")
        return None
    except Exception as e:
        print(f"Unexpected error: {e}")
        print(f"Error details: {str(e)}")
        return None

def update_sentx_prices():
    try:
        sentx_price = get_sentx_price()
        if sentx_price:
            # Read the JSON file
            with open('all_boards_data.json', 'r') as f:
                data = json.load(f)
            
            # Find and update SENTX items
            for board in data.get('boards', []):
                for coin in board.get('coins', []):
                    if coin['coin_symbol'].lower() == 'sentx':
                        change_column_value(
                            item_id=int(coin['coin_id']),
                            board_id=int(board['board_id']),
                            column_id=coin['column_ids']['valuation_price_column_id'],
                            value=str(sentx_price)
                        )
                        print(f"Updated SENTX price to {sentx_price} for item {coin['coin_id']}")
    except Exception as e:
        print(f"Error updating SENTX prices: {e}")


# Ejemplo de uso
def main():
    """
    Main execution flow for updating cryptocurrency prices and wallet data.
    """
    try:
        print("\n=== Starting Price Update Process ===")
        
        # # 1. Get Master Board data
        print("\n1. Getting Master Board data...")
        search_param = "Master"
        formatted_json = get_formatted_board_items(search_param)
        print(" Master Board data saved to 'board_items.json'")

        # 2. Load and update prices
        print("\n2. Updating prices for Master Board...")
        with open('all_boards_data.json', 'r') as f:
            master_board_data = json.load(f)
        updated_master = update_coin_prices(master_board_data)
        print("✓ Master Board prices updated")

        # 1. Get wallet data
        print("\n1. Getting wallet data...")
        wallets_data = get_specific_wallets_data()
        if not wallets_data['success']:
            raise Exception(f"Failed to get wallet data: {wallets_data['error']}")
        print("✓ Wallet data retrieved")

        # 2. Update prices directly using change_column_value
        print("\n2. Updating prices in Monday.com...")
        board_id = 1652251054  # CEX MASTER BOARD ID
        
        for group_name, items in wallets_data['data'].items():
            print(f"\nProcessing group: {group_name}")
            for item in items:
                try:
                    item_id = item['id']
                    code = item['columns']['Code']['value']
                    valuation_column_id = item['columns']['Valuation Price']['id']
                    
                    if code:
                        print(f"\nProcessing wallet item: {item['name']} with code: {code}")
                        # Usar exactamente la misma estructura que en la función principal
                        prices = get_coin_prices("CG-4uzPgs2oyq4aL8vqJEoB2zfD", [
                            {
                                "coin_symbol": code,
                                "coin_name": item['name']
                            }
                        ])
                        
                        # Obtener el precio usando el código en minúsculas
                        price = prices.get(code.lower(), {}).get('usd', 0)
                        print(f"Found price for {code}: ${price}")
                        
                        # Formatear el precio como en la función principal
                        try:
                            price = float(price)
                            formatted_price = f"{price:.7f}".rstrip('0').rstrip('.')
                        except ValueError:
                            formatted_price = "0"
                        
                        result = change_column_value(
                            item_id=int(item_id),
                            board_id=board_id,
                            column_id=valuation_column_id,
                            value=formatted_price
                        )
                        print(f"{'✓' if result else '⚠️'} Updated {code}: {item['name']} with price {formatted_price}")
                    
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"⚠️ Error updating {item['name']}: {str(e)}")
                    continue
        
        # 4. Updating SENTX prices...   
        print("\n4. Updating SENTX prices...")
        update_sentx_prices()
        
        # 5. Clean up
        print("\n5. Cleaning up...")
        # Clean all_boards_data.json
        with open('all_boards_data.json', 'w') as f:
            json.dump({"boards": []}, f, indent=2)
        # Clean all_items_minimal.json
        with open('all_items_minimal.json', 'w') as f:
            json.dump({"success": True, "data": {}, "error": None}, f, indent=2)
        print("✓ Temporary files cleaned")

        print("\n=== Process Completed Successfully ===")
    except Exception as e:
        print(f"\n⚠️ Error in main process: {str(e)}")
        print("Process terminated with errors")

if __name__ == "__main__":  
    main()

