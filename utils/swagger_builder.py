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
# Add this to your swagger builder usage section


# Add this to your swagger builder usage section
swagger = Swagger()

swagger.add_or_update_endpoint(
    endpoint_route='/analyses',
    method='get',
    tag='Content Creation',
    summary='Get latest analyses across all types',
    description='''
    Retrieve latest analyses across all analysis types with advanced filtering and search capabilities.
    
    The endpoint queries all analysis tables (Deep Dive, Daily Macro, Narratives, Spotlight, Support & Resistance)
    and returns the latest posts with optional filtering and search functionality.
    
    Results are sorted by creation date in descending order (newest first).
    ''',
    params=[
        {
            'name': 'page',
            'in': 'query',
            'description': 'Page number for pagination',
            'required': False,
            'type': 'integer',
            'default': 1
        },
        {
            'name': 'per_page',
            'in': 'query',
            'description': 'Number of items per page (max: 100)',
            'required': False,
            'type': 'integer',
            'default': 10
        },
        {
            'name': 'search',
            'in': 'query',
            'description': 'Search term to filter analyses by content or title',
            'required': False,
            'type': 'string'
        },
        {
            'name': 'coin',
            'in': 'query',
            'description': 'Filter analyses by specific coin name',
            'required': False,
            'type': 'string'
        },
        {
            'name': 'category',
            'in': 'query',
            'description': 'Filter analyses by category name',
            'required': False,
            'type': 'string'
        }
    ],
    responses={
        '200': {
            'description': 'Successful operation',
            'schema': {
                'type': 'object',
                'properties': {
                    'data': {
                        'type': 'array',
                        'items': {
                            'type': 'object',
                            'properties': {
                                'category_icon': {'type': 'string', 'example': '/static/topmenu_icons_resize/bitcoin.png'},
                                'category_name': {'type': 'string', 'example': 'bitcoin'},
                                'coin_icon': {'type': 'string', 'example': '/static/topmenu_icons_resize/bitcoin.png'},
                                'coin_id': {'type': 'integer', 'example': 1},
                                'coin_name': {'type': 'string', 'example': 'btc'},
                                'content': {'type': 'string', 'example': '<p>This is a test analysis for Bitcoin...</p>'},
                                'created_at': {'type': 'string', 'format': 'date-time', 'example': '2024-12-12T22:22:32.350759-03:00'},
                                'id': {'type': 'integer', 'example': 11},
                                'image_url': {'type': 'string', 'example': 'https://appanalysisimages.s3.us-east-2.amazonaws.com/bitcoin-analysis.jpg'},
                                'section_id': {'type': 'integer', 'example': 12},
                                'section_name': {'type': 'string', 'example': 'Daily Macro'},
                                'title': {'type': 'string', 'example': 'Bitcoin Price Analysis'}
                            }
                        }
                    },
                    'meta': {
                        'type': 'object',
                        'properties': {
                            'page': {'type': 'integer', 'example': 1},
                            'per_page': {'type': 'integer', 'example': 10},
                            'total_items': {'type': 'integer', 'example': 66},
                            'total_pages': {'type': 'integer', 'example': 7}
                        }
                    },
                    'error': {'type': 'string', 'nullable': True},
                    'success': {'type': 'boolean', 'example': True}
                }
            }
        },
        '400': {
            'description': 'Bad Request - Invalid parameters',
            'schema': {
                'type': 'object',
                'properties': {
                    'data': {'type': 'array', 'items': {}},
                    'meta': {
                        'type': 'object',
                        'properties': {
                            'page': {'type': 'integer'},
                            'per_page': {'type': 'integer'},
                            'total_items': {'type': 'integer'},
                            'total_pages': {'type': 'integer'}
                        }
                    },
                    'error': {'type': 'string', 'example': 'Invalid pagination parameters'},
                    'success': {'type': 'boolean', 'example': False}
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'data': {'type': 'array', 'items': {}},
                    'meta': {
                        'type': 'object',
                        'properties': {
                            'page': {'type': 'integer'},
                            'per_page': {'type': 'integer'},
                            'total_items': {'type': 'integer'},
                            'total_pages': {'type': 'integer'}
                        }
                    },
                    'error': {'type': 'string', 'example': 'An unexpected error occurred'},
                    'success': {'type': 'boolean', 'example': False}
                }
            }
        }
    }
)

# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/schedule_post')
# print(message)


