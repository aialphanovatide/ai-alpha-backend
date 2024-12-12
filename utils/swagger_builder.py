# Helper function to updated the Swagger JSON file

import os
import json
from typing import Tuple

class Swagger:
    def __init__(self):
        self.path = os.path.join('static', 'swagger.json')

    def load(self) -> dict:
        """
        Load and parse the Swagger JSON file.

        Returns:
            dict: The parsed Swagger JSON data.

        Raises:
            FileNotFoundError: If the Swagger file is not found at the specified path.
            json.JSONDecodeError: If the Swagger file contains invalid JSON.
            Exception: For any other unexpected errors during file loading.
        """
        try:
            with open(self.path, 'r') as file:
                self.swagger_json = json.load(file)
            return self.swagger_json
        except FileNotFoundError:
            raise FileNotFoundError(f"Error: Swagger file not found at {self.path}")
        except json.JSONDecodeError:
            raise json.JSONDecodeError(f"Error: Invalid JSON in Swagger file at {self.path}")
        except Exception as e:
            raise Exception(f"Unexpected error loading Swagger file: {str(e)}")

    def add_or_update_endpoint(self, endpoint_route: str, method: str, tag: str, summary: str, description: str, params: list, responses: dict) -> Tuple[bool, str]:
        """
        Add a new endpoint to the Swagger JSON file or update an existing one
        """
        try:
            # Open the Swagger JSON file
            swagger_json = self.load()
            if swagger_json is None:
                return False, "Failed to load Swagger JSON file"

            # Check if the endpoint already exists
            endpoint_exists = endpoint_route in swagger_json['paths'] and method in swagger_json['paths'][endpoint_route]
            
            if endpoint_exists:
                print(f'Endpoint {endpoint_route} [{method}] already exists. Updating...')
            else:
                print(f'Adding new endpoint {endpoint_route} [{method}]...')

            # Create or update the endpoint
            if endpoint_route not in swagger_json['paths']:
                swagger_json['paths'][endpoint_route] = {}
            
            # Add or update the endpoint with its details
            swagger_json['paths'][endpoint_route][method] = {
                'tags': [tag],
                'summary': summary.capitalize(),
                'description': description.capitalize(),
                'parameters': [],
                'responses': responses
            }
            
            # Add parameters if they exist
            try:
                for param in params:
                    parameter = {
                        'name': param.get('name', ''),
                        'in': param.get('in', 'query'),
                        'description': param.get('description', ''),
                        'required': param.get('required', False),
                        'type': param.get('type', 'string'),  # Default to string if type is missing
                        'schema': param.get('schema', {})  # Use an empty dict as fallback
                    }
                    # Only append valid parameters
                    if parameter['name']:
                        swagger_json['paths'][endpoint_route][method]['parameters'].append(parameter)
            except Exception as e:
                return False, f'Error processing parameters: {str(e)}'

            # Update the Swagger JSON file
            with open(self.path, 'w') as file:
                json.dump(swagger_json, file, indent=2)

            action = "updated" if endpoint_exists else "added"
            return True, f'Endpoint {endpoint_route} [{method}] {action} successfully'
        except Exception as e:
            return False, f'Error adding/updating endpoint {endpoint_route} [{method}]: {str(e)}'

    def delete_endpoint(self, endpoint_route: str) -> Tuple[bool, str]:
        """
        Delete an endpoint from the Swagger JSON file
        """
        try:
            swagger_path = self.path
            
            # Check if the Swagger JSON file exists
            if not os.path.exists(swagger_path):
                return False, "Swagger JSON file not found"

            # Load the Swagger JSON file
            with open(swagger_path, 'r') as file:
                swagger_json = json.load(file)

            # Check if the endpoint exists
            if endpoint_route not in swagger_json.get('paths', {}):
                return False, f"Endpoint {endpoint_route} not found"

            # Delete the endpoint
            del swagger_json['paths'][endpoint_route]

            # Write the updated Swagger JSON back to the file
            with open(swagger_path, 'w') as file:
                json.dump(swagger_json, file, indent=2)

            return True, f"Endpoint {endpoint_route} deleted successfully"

        except Exception as e:
            return False, f"Error deleting endpoint {endpoint_route}: {str(e)}"
 


# Example usage
swagger = Swagger()

# ____Add or update an endpoint____
# Add this to your swagger builder usage section

# swagger.add_or_update_endpoint(
#     endpoint_route='/ask-ai',
#     method='get',
#     tag='Ask AI',
#     summary='Get detailed cryptocurrency information',
#     description='[CACHED FOR 5 MINUTES] Retrieve comprehensive tokenomics data for a specific cryptocurrency using its Coin ID. '
#                 'The response is cached to optimize performance and handle rate limiting. '
#                 'The endpoint provides detailed information including price, market cap, supply metrics, and icon URLs in various formats.',
#     params=[
#         {
#             'name': 'coin_id',
#             'in': 'query',
#             'description': 'The CoinGecko ID of the cryptocurrency (e.g., "bitcoin", "ethereum")',
#             'required': True,
#             'type': 'string',
#             'example': 'bitcoin'
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved cryptocurrency data',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': True
#                     },
#                     'error': {
#                         'type': 'null'
#                     },
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'website': {
#                                 'type': 'string',
#                                 'description': 'Main project website URL',
#                                 'example': 'https://bitcoin.org'
#                             },
#                             'whitepaper': {
#                                 'type': 'string',
#                                 'description': 'URL to project whitepaper (from CoinGecko or CoinMarketCap)',
#                                 'example': 'https://bitcoin.org/bitcoin.pdf'
#                             },
#                             'categories': {
#                                 'type': 'array',
#                                 'description': 'List of categories the coin belongs to',
#                                 'items': {'type': 'string'},
#                                 'example': ['Cryptocurrency', 'Store of Value']
#                             },
#                             'chains': {
#                                 'type': 'array',
#                                 'description': 'List of blockchain platforms where the token exists',
#                                 'items': {'type': 'string'},
#                                 'example': ['bitcoin']
#                             },
#                             'current_price': {
#                                 'type': 'number',
#                                 'description': 'Current price in USD',
#                                 'example': 50000.00
#                             },
#                             'market_cap_usd': {
#                                 'type': 'number',
#                                 'description': 'Market capitalization in USD',
#                                 'example': 1000000000000
#                             },
#                             'fully_diluted_valuation': {
#                                 'type': 'number',
#                                 'description': 'Fully diluted valuation in USD',
#                                 'example': 1100000000000
#                             },
#                             'ath': {
#                                 'type': 'number',
#                                 'description': 'All-time high price in USD',
#                                 'example': 69000.00
#                             },
#                             'ath_change_percentage': {
#                                 'type': 'number',
#                                 'description': 'Percentage change from ATH',
#                                 'example': -25.5
#                             },
#                             'circulating_supply': {
#                                 'type': 'number',
#                                 'description': 'Current circulating supply',
#                                 'example': 19000000
#                             },
#                             'icon': {
#                                 'type': 'object',
#                                 'description': 'Icon URLs in various formats',
#                                 'properties': {
#                                     'thumb': {
#                                         'type': 'string',
#                                         'description': 'Thumbnail size icon URL'
#                                     },
#                                     'small': {
#                                         'type': 'string',
#                                         'description': 'Small size icon URL'
#                                     },
#                                     'large': {
#                                         'type': 'string',
#                                         'description': 'Large size icon URL'
#                                     },
#                                     'svg': {
#                                         'type': 'string',
#                                         'description': 'SVG version of the icon (if conversion successful)'
#                                     }
#                                 }
#                             }
#                         }
#                     }
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad Request - Missing coin_id parameter',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': False
#                     },
#                     'error': {
#                         'type': 'string',
#                         'example': 'The parameter coin_id is required'
#                     },
#                     'data': {
#                         'type': 'null'
#                     }
#                 }
#             }
#         },
#         '404': {
#             'description': 'Cryptocurrency not found or API error',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': False
#                     },
#                     'error': {
#                         'type': 'string',
#                         'example': 'Cryptocurrency not found or API request failed'
#                     },
#                     'data': {
#                         'type': 'null'
#                     }
#                 }
#             }
#         },
#         '429': {
#             'description': 'Rate limit exceeded',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': False
#                     },
#                     'error': {
#                         'type': 'string',
#                         'example': 'Too many requests. Please try again later.'
#                     },
#                     'data': {
#                         'type': 'null'
#                     },
#                     'rate_limit': {
#                         'type': 'object',
#                         'properties': {
#                             'max_calls': {
#                                 'type': 'integer',
#                                 'example': 10
#                             },
#                             'period': {
#                                 'type': 'integer',
#                                 'example': 60
#                             },
#                             'current_calls': {
#                                 'type': 'integer',
#                                 'example': 11
#                             }
#                         }
#                     }
#                 }
#             }
#         },
#         '500': {
#             'description': 'Server error',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': False
#                     },
#                     'error': {
#                         'type': 'string',
#                         'example': 'An unexpected error occurred while fetching cryptocurrency data'
#                     },
#                     'data': {
#                         'type': 'null'
#                     }
#                 }
#             }
#         }
#     }
# )

# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/categories/global-toggle')
# print(message)


