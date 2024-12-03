import datetime
import time
import requests
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API configuration
MONDAY_API_KEY = os.getenv('MONDAY_API_KEY_NOVATIDE')
COINGECKO_API_KEY = "CG-4uzPgs2oyq4aL8vqJEoB2zfD"

monday_url = "https://api.monday.com/v2"
headers = {
    "Content-Type": "application/json",
    "Authorization": MONDAY_API_KEY
}

def get_board_items(board_ids, limit=500):
    coins_data = []
    cursor = None
    
    # Si board_ids es un solo ID, conviértelo en una lista
    if isinstance(board_ids, int):
        board_ids = [board_ids]
    
    for board_id in board_ids:  # Iterar sobre cada board_id
        cursor = None  # Reiniciar cursor para cada tablero
        while True:
            # Consulta para un solo tablero
            query = f'''
            query {{
                boards(ids: {board_id}) {{
                    id
                    name
                    columns {{
                        title
                        id
                    }}
                    items_page(limit: {limit}, cursor: {f'"{cursor}"' if cursor else "null"}) {{
                        cursor
                        items {{
                            id
                            name
                            group {{
                                id
                                title
                            }}
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
                response.raise_for_status()
                data = response.json()['data']['boards'][0]
                
                if not coins_data:
                    columns = {col['id']: col['title'] for col in data['columns']}
                
                for item in data['items_page']['items']:
                    coin_data = {
                        'coin_name': item['name'],
                        'coin_id': item['id'],
                        'board_id': data['id'],
                        'board_name': data['name'],
                        'group_id': item['group']['id'],
                        'group_name': item['group']['title']
                    }
                    
                    for column_value in item['column_values']:
                        column_title = columns.get(column_value['id'], column_value['id'])
                        coin_data[column_title] = column_value['text']
                    
                    # Calcular fórmulas (si es necesario)
                    buy_prices = [float(coin_data.get(f'Buy Price {i}', 0) or 0) for i in range(1, 11)]
                    non_zero_prices = [p for p in buy_prices if p > 0]
                   
                    coin_data['Average Buy Price'] = sum(non_zero_prices) / len(non_zero_prices) if non_zero_prices else 0
                    
                    valuation_price = coin_data.get('Valuation Price', '0')  # Cambiar a '0' si no existe
                    try:
                        valuation_price = float(valuation_price)  # Intentar convertir a float
                    except ValueError:
                        valuation_price = 0  # Si falla, asignar 0
                    
                    coin_data['% Price Change'] = ((valuation_price - coin_data['Average Buy Price']) / coin_data['Average Buy Price']) * 100 if coin_data['Average Buy Price'] != 0 else 0
                    
                    suffixes = ['st', 'nd', 'rd'] + ['th'] * 7  

                    quantities = [
                        float(coin_data.get(f'{i}{suffixes[i-1]} Quantity', 0) or 0)
                        for i in range(1, 11)
                    ]

                    coin_data['Total Quantity'] = sum(quantities)
                    
                    
                    total_quantities = [
                        float(coin_data.get(f'{i}{suffixes[i-1]} Quantity', 0) or 0) *
                        float(coin_data.get(f'Buy Price {i}', 0) or 0)
                        for i in range(1, 11)
                    ]

                    coin_data['Total Cost'] = sum(total_quantities)
                   
                    coin_data['Current Total Value'] = coin_data['Total Cost'] * (1 + coin_data['% Price Change'] / 100)
                    
                    coin_data['P/L'] = coin_data['Current Total Value'] - coin_data['Total Cost']

                    coin_data['ROI'] = (coin_data['P/L'] / coin_data['Total Cost']) * 100 if coin_data['Total Cost'] != 0 else 0
                
                    coins_data.append(coin_data)
                
                cursor = data['items_page'].get('cursor')
                if not cursor:
                    break
            
            except Exception as e:
                print(f'Error retrieving items from the board: {str(e)}')
                return None
    
    return coins_data



def save_board_items_to_json(board_items, filename="BOARD_DATA.json"):
    filtered_items = [
        item for item in board_items 
        if item.get('Type') == 'Holding' and item.get('Valuation Price') not in [None, '', ' ']
    ]
    
    # Guardar los elementos filtrados en el archivo JSON
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(filtered_items, f, ensure_ascii=False, indent=2)
    
    print(f"Filtered data (Type='Holding' and 'Valuation Price' present) saved to '{filename}'")



def save_to_json(data, filename):
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Data saved to '{filename}'")
    
def load_board_data(filename="BOARD_DATA.json"):
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"The file {filename} was not found.")
        return []
    except json.JSONDecodeError:
        print(f"Error decoding the JSON file {filename}.")
        return []

def get_column_ids_for_group(board_id, group_id):
    query = f'''
    query {{
        boards(ids: {board_id}) {{
            groups(ids: ["{group_id}"]) {{
                id
                title
            }}
            columns {{
                id
                title
                type
            }}
        }}
    }}
    '''
    
    try:
        response = requests.post(monday_url, headers=headers, json={'query': query})
        response.raise_for_status()
        data = response.json()['data']['boards'][0]
        
        print(f"\nColumn IDs for group {data['groups'][0]['title']}:")
        for column in data['columns']:
            print(f"Column: {column['title']}")
            print(f"ID: {column['id']}")
            print(f"Type: {column['type']}\n")
            
        return data['columns']
    except Exception as e:
        print(f"Error retrieving column IDs: {str(e)}")
        return None

def create_group_and_add_items(board_id, group_name, items_data):
    current_date = datetime.datetime.now().strftime("%m/%d/%Y")
    create_group_query = f'''
    mutation {{
        create_group (board_id: {board_id}, group_name: "Weekly ROI % Report - {current_date}") {{
            id
        }}
    }}
    '''
    
    try:
        # Create the group
        response = requests.post(monday_url, headers=headers, json={'query': create_group_query})
        response.raise_for_status()
        group_id = response.json()['data']['create_group']['id']
        
        # Add items to the group
        for item in items_data:
            # Build column_values
            column_values = {
                "name":  item['coin_name'],
                "texto1__1": item['Code'].upper(),
                "texto2__1": item['group_name'],
                "texto6__1": item['Category'],
                "valuation_price__1": f"${float(item['Valuation Price']):.12f}".rstrip('0').rstrip('.'),  # Limitar a 7 decimales y eliminar ceros a la derecha
                "texto__1": f"${round(float(item['Total Cost']), 2):.2f}",  # Redondear a 2 decimales
                "texto8__1": f"${float(item['Average Buy Price']):.7f}".rstrip('0').rstrip('.'),  # Limitar a 7 decimales y eliminar ceros a la derecha
                "texto4__1": f"${round(float(item['Current Total Value']), 2):.2f}",  # Redondear a 2 decimales
                "texto3__1": f"${round(float(item['P/L']), 2):.2f}",  # Redondear P/L a 2 decimales
                "texto30__1": f"{round(item['ROI'])}%",  # Redondear ROI a número entero
                "texto307__1": datetime.datetime.now().strftime("%d/%m/%Y")
            }
                

            create_item_query = f'''
            mutation {{
                create_item (
                    board_id: {board_id},
                    group_id: "{group_id}",
                    item_name: "{item['Code'].upper()}",
                    column_values: {json.dumps(json.dumps(column_values))}
                ) {{
                    id
                }}
            }}
            '''
            
            response = requests.post(monday_url, headers=headers, json={'query': create_item_query})
            try:
                response.raise_for_status()  # Raise an error for bad responses
                print("Item created successfully:", response.json())
            except requests.exceptions.HTTPError as err:
                print("HTTP error occurred:", err)
                print("Response content:", response.text)  # Print the response content for debugging
            time.sleep(0.5)
            
        return True
    except Exception as e:
        print(f"Error creating group or adding items: {str(e)}")
        print(f"Response content: {response.text if 'response' in locals() else 'No response'}")
        return False

def update_monday_boards():
    from datetime import datetime
    current_week = datetime.now().strftime("Week %V - %Y")
    
    try:
        # Cargar los datos de los archivos JSON
        with open('best.json', 'r') as f:
            best_20_data = json.load(f)
        with open('worst.json', 'r') as f:
            worst_20_data = json.load(f)
            
        # Actualizar el tablero de las mejores monedas
        print("Updating Weekly Best TOP 20...")
        success_best = create_group_and_add_items(
            board_id=1716371627,
            group_name=current_week,
            items_data=best_20_data
        )
        # Agregar retraso entre actualizaciones
        time.sleep(1)
        
        # Actualizar el tablero de las peores monedas
        print("Updating Weekly Lowest TOP 20...")
        success_worst = create_group_and_add_items(
            board_id=1721925921,
            group_name=current_week,
            items_data=worst_20_data
        )
        
        if success_best and success_worst:
            print(f"Data successfully updated in both boards for {current_week}")
        else:
            print("There were errors updating the boards")
            
    except Exception as e:
        print(f"Error loading or processing data: {str(e)}")
    
    finally:
        # Limpiar los archivos JSON utilizados
        try:
            # Eliminar los archivos JSON después de usarlos
            os.remove('best.json')
            os.remove('worst.json')
            os.remove('BOARD_DATA.json')
            print("Temporary JSON files cleaned up.")
        except Exception as e:
            print(f"Error cleaning up files: {str(e)}")

def main():
    CEX_MASTER = 1652251054
    DEX_MASTER = 1678221568
    
    # Retrieve and process data from Monday.com
    board_items = get_board_items(board_ids=[DEX_MASTER, CEX_MASTER])
    if board_items:
        save_board_items_to_json(board_items)
    else:
        print("Could not retrieve data from the board.")
        return

    # Load data and process for filtering
    board_data = load_board_data()
    
    # Filter for best and worst coins
    bestcoins = [
        coin for coin in board_data 
        if coin.get('ROI', 0) > 50 and coin.get('Valuation Price', None) is not None
    ]

    worstcoins = [
        coin for coin in board_data 
        if coin.get('ROI', 0) < -90 and coin.get('Valuation Price', None) is not None
    ]
        
    # Save results to respective JSON files
    save_to_json(bestcoins, "best.json")
    save_to_json(worstcoins, "worst.json")
    print("Results saved in best.json and worst.json")
    
    # Update Monday.com boards
    update_monday_boards()
    
if __name__ == "__main__":
    main()