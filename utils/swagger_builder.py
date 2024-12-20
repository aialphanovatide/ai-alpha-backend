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

# Add this to the example usage section at the bottom of the file
# success, message = swagger.add_or_update_endpoint(
#    endpoint_route='/coin/{coin_id}/toggle-coin',
#    method='post',
#    tag='Coin',
#    summary='Toggle coin activation status',
#    description='Toggle a coin\'s active status. Activation requires an active category and valid coin data. Deactivation is always allowed.',
#    params=[
#        {
#            'name': 'coin_id',
#            'in': 'path',
#            'description': 'ID of the coin to toggle',
#            'required': True,
#            'type': 'integer'
#        }
#    ],
#    responses={
#        '200': {
#            'description': 'Successfully toggled coin status',
#            'schema': {
#                'type': 'object',
#                'properties': {
#                    'success': {'type': 'boolean'},
#                    'message': {'type': 'string'},
#                    'is_active': {'type': 'boolean'},
#                    'error': {'type': 'null'}
#                }
#            }
#        },
#        '400': {
#            'description': 'Invalid request (inactive category or failed validation)',
#            'schema': {
#                'type': 'object',
#                'properties': {
#                    'success': {'type': 'boolean', 'example': False},
#                    'message': {'type': 'string'},
#                    'is_active': {'type': 'boolean'},
#                    'error': {'type': 'string'}
#                }
#            }
#        },
#        '404': {
#            'description': 'Coin not found',
#            'schema': {
#                'type': 'object',
#                'properties': {
#                    'success': {'type': 'boolean', 'example': False},
#                    'message': {'type': 'string'},
#                    'is_active': {'type': 'boolean'},
#                    'error': {'type': 'string'}
#                }
#            }
#        },
#        '500': {
#            'description': 'Server error',
#            'schema': {
#                'type': 'object',
#                'properties': {
#                    'success': {'type': 'boolean', 'example': False},
#                    'message': {'type': 'string'},
#                    'is_active': {'type': 'boolean'},
#                    'error': {'type': 'string'}
#                }
#            }
#        }
#    }
# )
# print(message)
# PUT /analysis/{analysis_id}
# swagger.add_or_update_endpoint(
#     endpoint_route='/analysis/{analysis_id}',
#     method='put',
#     tag='Content Creation',
#     summary='Update analysis',
#     description='Update the content of an existing analysis',
#     params=[
#         {
#             'name': 'analysis_id',
#             'in': 'path',
#             'description': 'ID of the analysis to update',
#             'required': True,
#             'type': 'integer'
#         },
#         {
#             'name': 'body',
#             'in': 'body',
#             'description': 'Analysis update data',
#             'required': True,
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'section_id': {
#                         'type': 'integer',
#                         'description': 'ID of the section the analysis belongs to'
#                     },
#                     'content': {
#                         'type': 'string',
#                         'description': 'New content for the analysis'
#                     }
#                 },
#                 'required': ['section_id', 'content'],
#                 'example': {
#                     'section_id': 1,
#                     'content': 'Updated analysis content here'
#                 }
#             }
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Analysis updated successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'id': {'type': 'integer'},
#                             'analysis': {'type': 'string'},
#                             'created_at': {'type': 'string', 'format': 'date-time'},
#                             'updated_at': {'type': 'string', 'format': 'date-time'}
#                         }
#                     },
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean', 'example': True}
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad Request - Missing or invalid parameters',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {'type': 'null'},
#                     'error': {'type': 'string'},
#                     'success': {'type': 'boolean', 'example': False}
#                 }
#             }
#         },
#         '404': {
#             'description': 'Analysis or section not found',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {'type': 'null'},
#                     'error': {'type': 'string'},
#                     'success': {'type': 'boolean', 'example': False}
#                 }
#             }
#         }
#     }
# )


# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/categories/global-toggle')
# print(message)


