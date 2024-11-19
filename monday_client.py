import os
import time 
from monday import MondayClient
from dotenv import load_dotenv
load_dotenv() 
import requests
import json
from ast import literal_eval
from monday.exceptions import MondayError



MONDAY_API_KEY_NOVATIDE = os.getenv("MONDAY_API_KEY_NOVATIDE")

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

    # Wrap the value in quotes and escape any existing quotes
    value = json.dumps(value)
    
    mutation_query = f'''
        mutation {{
            change_simple_column_value(
                item_id: {item_id},
                board_id: {board_id},
                column_id: "{column_id}",
                value: "{value}"
            ) {{
                id
            }}
        }}
    '''

    try:
        response = requests.post(monday_url, headers=headers, json={'query': mutation_query})
        print('Change column value response', response.content)
        response_data = response.json()
        
        if 'error_code' in response_data:
            error_message = response_data['error_message']
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
        board_info = monday_client.boards.fetch_columns_by_board_id(board_ids=[board_id])
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

# print(get_column_ids(board_id=1652251054))
# print(write_new_update(item_id=1355566235, value=f'new test'))
# create_notification(user_id=53919924, item_id=1355566235, value="test")
#print(change_column_value(board_id=1652251054, item_id=1652272796, column_id="valuation_price__1", value=0.407181))


# print(get_board_items(board_ids=[1537800320]))
# print(get_all_boards(search_param="KuCoin Wallet Master Sheet"))
# print(get_board_item_general_test(board_ids=[1414986103]))


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

def get_coin_prices(api_key: str, coins: list) -> dict:
    global coingecko_calls

    coin_map = get_coin_list(api_key)
    
    symbol_to_id = {}
    for coin in coins:
        symbol = coin['coin_symbol'].lower()
        name = coin['coin_name'].lower()
        if symbol in coin_map:
            symbol_to_id[symbol] = coin_map[symbol]
        elif name in coin_map:
            symbol_to_id[symbol] = coin_map[name]
    
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
            coingecko_calls += 1 
            data = response.json()
            
            for symbol, id in symbol_to_id.items():
                if id in data:
                    prices[symbol] = data[id]
            
            time.sleep(1)
        except requests.RequestException as e:
            print(f"Error al obtener datos: {e}")
    
    return prices

def update_coin_prices(json_data, api_key):
    # Iterate through each board in the JSON data
    for board in json_data['boards']:
        coins = board['coins']  # Get the coins for the current board
        board_id = board['board_id']  # Get the board_id for the current board
        prices = get_coin_prices(api_key, coins)  # Get prices for the coins

        for coin in coins:
            symbol = coin['coin_symbol'].lower()
            if symbol in prices and 'usd' in prices[symbol]:
                # Add the updated price
                coin['column_ids']['updated_price'] = prices[symbol]['usd']
                
                # Update the price in Monday.com using the board_id of the current board
                result = change_column_value(
                    item_id=int(coin['coin_id']),
                    board_id=int(board_id),
                    column_id=coin['column_ids']['valuation_price_column_id'],
                    value=prices[symbol]['usd']
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

# Ejemplo de uso
def main():
    search_param = ""
    formatted_json = get_formatted_board_items(search_param)
    print("The results have been saved in 'board_items.json'")

    with open('all_boards_data.json', 'r') as f:
        json_data = json.load(f)

    # Update prices and Monday.com
    updated_json = update_coin_prices(json_data, MONDAY_API_KEY_NOVATIDE)

    # Clear the JSON to make it ready for the next use
    with open('all_boards_data.json', 'w') as f:
        json.dump({"boards": []}, f, indent=2)  # Save an empty object

    print("The JSON has been cleared and is ready for the next use.")
    print(f"Number of calls made to Coingecko: {coingecko_calls}")  # Informative print

if __name__ == "__main__":
    main()

