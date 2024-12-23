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

    def add_or_update_endpoint(self, endpoint_route: str, method: str, tag: str, 
                             summary: str, description: str, params: list, 
                             responses: dict, request_body: dict = None) -> Tuple[bool, str]:
        """
        Add a new endpoint to the Swagger JSON file or update an existing one
        
        Args:
            endpoint_route (str): The endpoint route
            method (str): HTTP method
            tag (str): API tag category
            summary (str): Short summary
            description (str): Detailed description
            params (list): List of parameters
            responses (dict): Response definitions
            request_body (dict, optional): Request body definition
        """
        try:
            swagger_json = self.load()
            if swagger_json is None:
                return False, "Failed to load Swagger JSON file"

            endpoint_exists = endpoint_route in swagger_json['paths'] and method in swagger_json['paths'][endpoint_route]
            
            if endpoint_exists:
                print(f'Endpoint {endpoint_route} [{method}] already exists. Updating...')
            else:
                print(f'Adding new endpoint {endpoint_route} [{method}]...')

            if endpoint_route not in swagger_json['paths']:
                swagger_json['paths'][endpoint_route] = {}
            
            # Create the endpoint definition
            endpoint_def = {
                'tags': [tag],
                'summary': summary.capitalize(),
                'description': description.capitalize(),
                'parameters': [],
                'responses': responses
            }

            # Add parameters if they exist
            if params:
                endpoint_def['parameters'].extend([
                    {
                        'name': param.get('name', ''),
                        'in': param.get('in', 'query'),
                        'description': param.get('description', ''),
                        'required': param.get('required', False),
                        'type': param.get('type', 'string')
                    } for param in params if param.get('name')
                ])

            # Add request body if provided
            if request_body:
                if method.lower() in ['post', 'put', 'patch']:
                    endpoint_def['consumes'] = [request_body.get('content-type', 'application/json')]
                    endpoint_def['parameters'].append({
                        'in': 'formData' if request_body.get('content-type') == 'multipart/form-data' else 'body',
                        'name': 'body',
                        'description': 'Request body',
                        'required': request_body.get('required', True),
                        'schema': {
                            'type': 'object',
                            'properties': request_body.get('properties', {})
                        }
                    })

            swagger_json['paths'][endpoint_route][method.lower()] = endpoint_def

            with open(self.path, 'w') as file:
                json.dump(swagger_json, file, indent=2)

            action = "updated" if endpoint_exists else "added"
            return True, f'Endpoint {endpoint_route} [{method}] {action} successfully'
        except Exception as e:
            return False, f'Error adding/updating endpoint {endpoint_route} [{method}]: {str(e)}'

    # def add_or_update_endpoint(self, endpoint_route: str, method: str, tag: str, summary: str, description: str, params: list, responses: dict) -> Tuple[bool, str]:
    #     """
    #     Add a new endpoint to the Swagger JSON file or update an existing one
    #     """
    #     try:
    #         # Open the Swagger JSON file
    #         swagger_json = self.load()
    #         if swagger_json is None:
    #             return False, "Failed to load Swagger JSON file"

    #         # Check if the endpoint already exists
    #         endpoint_exists = endpoint_route in swagger_json['paths'] and method in swagger_json['paths'][endpoint_route]
            
    #         if endpoint_exists:
    #             print(f'Endpoint {endpoint_route} [{method}] already exists. Updating...')
    #         else:
    #             print(f'Adding new endpoint {endpoint_route} [{method}]...')

    #         # Create or update the endpoint
    #         if endpoint_route not in swagger_json['paths']:
    #             swagger_json['paths'][endpoint_route] = {}
            
    #         # Add or update the endpoint with its details
    #         swagger_json['paths'][endpoint_route][method] = {
    #             'tags': [tag],
    #             'summary': summary.capitalize(),
    #             'description': description.capitalize(),
    #             'parameters': [],
    #             'responses': responses
    #         }
            
    #         # Add parameters if they exist
    #         try:
    #             for param in params:
    #                 parameter = {
    #                     'name': param.get('name', ''),
    #                     'in': param.get('in', 'query'),
    #                     'description': param.get('description', ''),
    #                     'required': param.get('required', False),
    #                     'type': param.get('type', 'string'),  # Default to string if type is missing
    #                     'schema': param.get('schema', {})  # Use an empty dict as fallback
    #                 }
    #                 # Only append valid parameters
    #                 if parameter['name']:
    #                     swagger_json['paths'][endpoint_route][method]['parameters'].append(parameter)
    #         except Exception as e:
    #             return False, f'Error processing parameters: {str(e)}'

    #         # Update the Swagger JSON file
    #         with open(self.path, 'w') as file:
    #             json.dump(swagger_json, file, indent=2)

    #         action = "updated" if endpoint_exists else "added"
    #         return True, f'Endpoint {endpoint_route} [{method}] {action} successfully'
    #     except Exception as e:
    #         return False, f'Error adding/updating endpoint {endpoint_route} [{method}]: {str(e)}'

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

# swagger.add_or_update_endpoint(
#     endpoint_route='/topics',
#     method='get',
#     tag='Notifications',
#     summary='Get all notification topics',
#     description='''
#     Retrieve all notification topics with optional filtering capabilities.
    
#     The endpoint returns a list of topics that can be filtered by coin reference, topic type, and timeframe.
#     If no filters are provided, it returns all available topics.
    
#     Topics are used for managing notification subscriptions and message routing in the system.
#     ''',
#     params=[
#         {
#             'name': 'coin',
#             'in': 'query',
#             'description': 'Filter topics by coin reference (e.g., "bitcoin", "ethereum")',
#             'required': False,
#             'type': 'string'
#         },
#         {
#             'name': 'type',
#             'in': 'query',
#             'description': 'Filter by topic type (e.g., "alerts", "support_resistance")',
#             'required': False,
#             'type': 'string'
#         },
#         {
#             'name': 'timeframe',
#             'in': 'query',
#             'description': 'Filter by timeframe (e.g., "1d", "1w")',
#             'required': False,
#             'type': 'string'
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Successful operation',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': True
#                     },
#                     'data': {
#                         'type': 'array',
#                         'items': {
#                             'type': 'object',
#                             'properties': {
#                                 'id': {
#                                     'type': 'integer',
#                                     'example': 1
#                                 },
#                                 'name': {
#                                     'type': 'string',
#                                     'example': 'bitcoin_alerts_1d'
#                                 },
#                                 'reference': {
#                                     'type': 'string',
#                                     'example': 'bitcoin, btc'
#                                 },
#                                 'timeframe': {
#                                     'type': 'string',
#                                     'example': '1d'
#                                 },
#                                 'type': {
#                                     'type': 'string',
#                                     'example': 'alerts'
#                                 },
#                                 'created_at': {
#                                     'type': 'string',
#                                     'format': 'date-time',
#                                     'example': '2024-03-20T12:00:00Z'
#                                 },
#                                 'updated_at': {
#                                     'type': 'string',
#                                     'format': 'date-time',
#                                     'example': '2024-03-20T12:00:00Z'
#                                 }
#                             }
#                         }
#                     },
#                     'count': {
#                         'type': 'integer',
#                         'example': 1
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
#                         'example': 'Database connection error'
#                     },
#                     'message': {
#                         'type': 'string',
#                         'example': 'Failed to fetch topics'
#                     }
#                 }
#             }
#         }
#     }
# )

# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/schedule_post')
# print(message)


