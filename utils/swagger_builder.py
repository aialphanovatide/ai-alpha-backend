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
                'tags': [tag.capitalize()],
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


# # Documentation for /alerts/categories endpoint
# success, message = swagger.add_or_update_endpoint(
#     endpoint_route='/alerts/categories',
#     method='post',
#     tag='Alerts',
#     summary='Retrieve alerts for multiple categories',
#     description='''Retrieve alerts for multiple categories with timeframe filtering and pagination support.
    
# The endpoint allows filtering alerts by timeframe (1h, 4h, 1d, 1w) extracted from the alert name.
# Results are ordered by creation date (newest first) with optional pagination.''',
#     params=[
#         {
#             'name': 'body',
#             'in': 'body',
#             'required': True,
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'categories': {
#                         'type': 'array',
#                         'items': {'type': 'string'},
#                         'description': 'List of category names',
#                         'example': ['bitcoin', 'ethereum']
#                     },
#                     'timeframe': {
#                         'type': 'string',
#                         'enum': ['1h', '4h', '1d', '1w'],
#                         'description': 'Filter alerts by timeframe',
#                         'example': '4h'
#                     },
#                     'page': {
#                         'type': 'integer',
#                         'description': 'Page number (default: 1)',
#                         'default': 1,
#                         'minimum': 1
#                     },
#                     'per_page': {
#                         'type': 'integer',
#                         'description': 'Items per page (default: 10)',
#                         'default': 10,
#                         'minimum': 1
#                     }
#                 },
#                 'required': ['categories']
#             }
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved alerts by categories',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'categories': {
#                         'type': 'object',
#                         'additionalProperties': {
#                             'type': 'object',
#                             'properties': {
#                                 'data': {
#                                     'type': 'array',
#                                     'items': {
#                                         'type': 'object',
#                                         'properties': {
#                                             'alert_id': {'type': 'integer'},
#                                             'alert_name': {'type': 'string'},
#                                             'alert_message': {'type': 'string'},
#                                             'symbol': {'type': 'string'},
#                                             'price': {'type': 'number'},
#                                             'coin_bot_id': {'type': 'integer'},
#                                             'created_at': {'type': 'string', 'format': 'date-time'},
#                                             'updated_at': {'type': 'string', 'format': 'date-time'},
#                                             'timeframe': {
#                                                 'type': 'string',
#                                                 'enum': ['1h', '4h', '1d', '1w'],
#                                                 'nullable': True
#                                             }
#                                         }
#                                     }
#                                 },
#                                 'total': {'type': 'integer'},
#                                 'pagination': {
#                                     'type': 'object',
#                                     'properties': {
#                                         'current_page': {'type': 'integer'},
#                                         'per_page': {'type': 'integer'},
#                                         'total_pages': {'type': 'integer'},
#                                         'has_next': {'type': 'boolean'},
#                                         'has_prev': {'type': 'boolean'}
#                                     }
#                                 }
#                             }
#                         }
#                     },
#                     'total_alerts': {'type': 'integer'}
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad Request - Invalid input parameters',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'error': {
#                         'type': 'string',
#                         'example': 'Invalid timeframe. Must be one of: 1h, 4h, 1d, 1w'
#                     }
#                 }
#             }
#         },
#         '500': {
#             'description': 'Internal Server Error',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'error': {'type': 'string'}
#                 }
#             }
#         }
#     }
# )

# print(message)

# # Documentation for /alerts/coins endpoint
# success, message = swagger.add_or_update_endpoint(
#     endpoint_route='/alerts/coins',
#     method='post',
#     tag='Alerts',
#     summary='Retrieve alerts for multiple coins',
#     description='''Retrieve alerts for multiple coins with timeframe filtering and pagination support.
    
# The endpoint allows filtering alerts by timeframe (1h, 4h, 1d, 1w) extracted from the alert name.
# Results are ordered by creation date (newest first) with optional pagination.''',
#     params=[
#         {
#             'name': 'body',
#             'in': 'body',
#             'required': True,
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'coins': {
#                         'type': 'array',
#                         'items': {'type': 'string'},
#                         'description': 'List of coin symbols',
#                         'example': ['btc', 'eth']
#                     },
#                     'timeframe': {
#                         'type': 'string',
#                         'enum': ['1h', '4h', '1d', '1w'],
#                         'description': 'Filter alerts by timeframe',
#                         'example': '4h'
#                     },
#                     'page': {
#                         'type': 'integer',
#                         'description': 'Page number (default: 1)',
#                         'default': 1,
#                         'minimum': 1
#                     },
#                     'per_page': {
#                         'type': 'integer',
#                         'description': 'Items per page (default: 10)',
#                         'default': 10,
#                         'minimum': 1
#                     }
#                 },
#                 'required': ['coins']
#             }
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved alerts by coins',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'coins': {
#                         'type': 'object',
#                         'additionalProperties': {
#                             'type': 'object',
#                             'properties': {
#                                 'data': {
#                                     'type': 'array',
#                                     'items': {
#                                         'type': 'object',
#                                         'properties': {
#                                             'alert_id': {'type': 'integer'},
#                                             'alert_name': {'type': 'string'},
#                                             'alert_message': {'type': 'string'},
#                                             'symbol': {'type': 'string'},
#                                             'price': {'type': 'number'},
#                                             'coin_bot_id': {'type': 'integer'},
#                                             'created_at': {'type': 'string', 'format': 'date-time'},
#                                             'updated_at': {'type': 'string', 'format': 'date-time'},
#                                             'timeframe': {
#                                                 'type': 'string',
#                                                 'enum': ['1h', '4h', '1d', '1w'],
#                                                 'nullable': True
#                                             }
#                                         }
#                                     }
#                                 },
#                                 'total': {'type': 'integer'},
#                                 'pagination': {
#                                     'type': 'object',
#                                     'properties': {
#                                         'current_page': {'type': 'integer'},
#                                         'per_page': {'type': 'integer'},
#                                         'total_pages': {'type': 'integer'},
#                                         'has_next': {'type': 'boolean'},
#                                         'has_prev': {'type': 'boolean'}
#                                     }
#                                 }
#                             }
#                         }
#                     },
#                     'total_alerts': {'type': 'integer'}
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad Request - Invalid input parameters',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'error': {
#                         'type': 'string',
#                         'example': 'Invalid timeframe. Must be one of: 1h, 4h, 1d, 1w'
#                     }
#                 }
#             }
#         },
#         '500': {
#             'description': 'Internal Server Error',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'error': {'type': 'string'}
#                 }
#             }
#         }
#     }
# )

# print(message)


# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/api/tv/alerts')
# print(message)


