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

# # 1. POST /post_introduction
# swagger.add_or_update_endpoint(
#     endpoint_route='/introduction',
#     method='post',
#     tag='Introduction',
#     summary='Create a new introduction for a coin',
#     description='''
#     Creates a new introduction entry for a specific coin.
    
#     This endpoint allows you to create an introduction with required content, website, and whitepaper information.
#     Each coin can only have one introduction. Attempting to create multiple introductions for the same coin will result in an error.
#     ''',
#     params=[],
#     request_body={
#         'content-type': 'application/json',
#         'required': True,
#         'properties': {
#             'coin_id': {
#                 'type': 'integer',
#                 'description': 'ID of the coin',
#                 'example': 1
#             },
#             'content': {
#                 'type': 'string',
#                 'description': 'Introduction content',
#                 'example': 'This is a detailed introduction about the coin...'
#             },
#             'website': {
#                 'type': 'string',
#                 'description': 'Official website URL',
#                 'example': 'https://example.com'
#             },
#             'whitepaper': {
#                 'type': 'string',
#                 'description': 'Whitepaper URL',
#                 'example': 'https://example.com/whitepaper.pdf'
#             },
#             'dynamic': {
#                 'type': 'boolean',
#                 'description': 'Whether the introduction is dynamic',
#                 'example': False
#             }
#         }
#     },
#     responses={
#         '201': {
#             'description': 'Introduction created successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {
#                         'type': 'boolean',
#                         'example': True
#                     },
#                     'message': {
#                         'type': 'string',
#                         'example': 'Introduction created successfully'
#                     },
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'id': {'type': 'integer', 'example': 1},
#                             'coin_id': {'type': 'integer', 'example': 1},
#                             'content': {'type': 'string', 'example': 'Introduction content'},
#                             'website': {'type': 'string', 'example': 'https://example.com'},
#                             'whitepaper': {'type': 'string', 'example': 'https://example.com/whitepaper.pdf'},
#                             'dynamic': {'type': 'boolean', 'example': False},
#                             'created_at': {'type': 'string', 'format': 'date-time'},
#                             'updated_at': {'type': 'string', 'format': 'date-time'}
#                         }
#                     }
#                 }
#             }
#         },
#         '400': {
#             'description': 'Invalid request',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': False},
#                     'message': {'type': 'string', 'example': 'content is required'}
#                 }
#             }
#         },
#         '409': {
#             'description': 'Conflict - Introduction already exists',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': False},
#                     'message': {'type': 'string', 'example': 'An introduction already exists for this coin'}
#                 }
#             }
#         }
#     }
# )

# # 2. GET /api/get_introduction
# swagger.add_or_update_endpoint(
#     endpoint_route='/introduction',
#     method='get',
#     tag='Introduction',
#     summary='Get introduction by coin ID or name',
#     description='Retrieve the introduction information for a specific coin using either the coin ID or coin name.',
#     params=[
#         {
#             'name': 'id',
#             'in': 'query',
#             'description': 'Coin ID',
#             'required': False,
#             'type': 'integer'
#         },
#         {
#             'name': 'coin_name',
#             'in': 'query',
#             'description': 'Name of the coin',
#             'required': False,
#             'type': 'string'
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Success',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': True},
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'id': {'type': 'integer', 'example': 1},
#                             'coin_id': {'type': 'integer', 'example': 1},
#                             'content': {'type': 'string', 'example': 'Introduction content'},
#                             'website': {'type': 'string', 'example': 'https://example.com'},
#                             'whitepaper': {'type': 'string', 'example': 'https://example.com/whitepaper.pdf'},
#                             'dynamic': {'type': 'boolean', 'example': False},
#                             'created_at': {'type': 'string', 'format': 'date-time'},
#                             'updated_at': {'type': 'string', 'format': 'date-time'}
#                         }
#                     }
#                 }
#             }
#         },
#         '400': {
#             'description': 'Invalid request',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': False},
#                     'message': {'type': 'string', 'example': 'Either id or coin_name is required'}
#                 }
#             }
#         },
#         '404': {
#             'description': 'Introduction not found',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': False},
#                     'message': {'type': 'string', 'example': 'No introduction found for the specified coin'}
#                 }
#             }
#         }
#     }
# )

# # 3. PUT /edit_introduction/{coin_bot_id}
# swagger.add_or_update_endpoint(
#     endpoint_route='/introduction/{coin_id}',
#     method='put',
#     tag='Introduction',
#     summary='Update introduction for a specific coin',
#     description='Update the content, website, or whitepaper information for an existing introduction.',
#     params=[
#         {
#             'name': 'coin_id',
#             'in': 'path',
#             'description': 'ID of the coin',
#             'required': True,
#             'type': 'integer'
#         }
#     ],
#     request_body={
#         'content-type': 'application/json',
#         'required': True,
#         'properties': {
#             'content': {
#                 'type': 'string',
#                 'description': 'Updated introduction content',
#                 'example': 'Updated introduction content...'
#             },
#             'website': {
#                 'type': 'string',
#                 'description': 'Updated website URL',
#                 'example': 'https://updated-example.com'
#             },
#             'whitepaper': {
#                 'type': 'string',
#                 'description': 'Updated whitepaper URL',
#                 'example': 'https://updated-example.com/whitepaper.pdf'
#             }
#         }
#     },
#     responses={
#         '200': {
#             'description': 'Introduction updated successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': True},
#                     'message': {'type': 'string', 'example': 'Introduction updated successfully'},
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'id': {'type': 'integer', 'example': 1},
#                             'coin_id': {'type': 'integer', 'example': 1},
#                             'content': {'type': 'string', 'example': 'Updated content'},
#                             'website': {'type': 'string', 'example': 'https://updated-example.com'},
#                             'whitepaper': {'type': 'string', 'example': 'https://updated-example.com/whitepaper.pdf'},
#                             'dynamic': {'type': 'boolean', 'example': False},
#                             'created_at': {'type': 'string', 'format': 'date-time'},
#                             'updated_at': {'type': 'string', 'format': 'date-time'}
#                         }
#                     }
#                 }
#             }
#         },
#         '400': {
#             'description': 'Invalid request',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': False},
#                     'message': {'type': 'string', 'example': 'At least one field (content, website, or whitepaper) is required'}
#                 }
#             }
#         },
#         '404': {
#             'description': 'Introduction not found',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean', 'example': False},
#                     'message': {'type': 'string', 'example': 'No introduction found for the specified coin'}
#                 }
#             }
#         }
#     }
# )

swagger = Swagger()

# GET /introduction/{coin_id}
swagger.add_or_update_endpoint(
    endpoint_route='/introduction/{coin_id}',
    method='get',
    tag='Introduction',
    summary='Get introduction by coin ID',
    description='Retrieve the introduction information for a specific coin using the coin ID.',
    params=[
        {
            'name': 'coin_id',
            'in': 'path',
            'description': 'ID of the coin',
            'required': True,
            'type': 'integer'
        }
    ],
    responses={
        '200': {
            'description': 'Success',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': True},
                    'data': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer', 'example': 1},
                            'coin_bot_id': {'type': 'integer', 'example': 1},
                            'content': {'type': 'string', 'example': 'Introduction content'},
                            'website': {'type': 'string', 'example': 'https://example.com'},
                            'whitepaper': {'type': 'string', 'example': 'https://example.com/whitepaper.pdf'},
                            'dynamic': {'type': 'boolean', 'example': False},
                            'created_at': {'type': 'string', 'format': 'date-time'},
                            'updated_at': {'type': 'string', 'format': 'date-time'}
                        }
                    }
                }
            }
        },
        '400': {
            'description': 'Invalid request',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'message': {'type': 'string', 'example': 'coin_id is required'}
                }
            }
        },
        '404': {
            'description': 'Introduction not found',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'message': {'type': 'string', 'example': 'No introduction found for the specified coin'}
                }
            }
        },
        '500': {
            'description': 'Server error',
            'schema': {
                'type': 'object',
                'properties': {
                    'success': {'type': 'boolean', 'example': False},
                    'message': {'type': 'string', 'example': 'Database error: [error details]'}
                }
            }
        }
    }
)

# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/api/get_introduction')
# print(message)


