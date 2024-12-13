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

# swagger.add_or_update_endpoint(
#     endpoint_route='/analysis',
#     method='post',
#     tag='Content Creation',
#     summary='Create a new analysis',
#     description='''
#     Create a new analysis with a pre-generated image.
    
#     Note:
#     - All fields are required
#     - coin_id and section_id must be valid integers
#     - image_url should be a valid URL (either temporary DALL-E URL or permanent S3 URL)
#     - content should include a title followed by <br> and then the main content
#     ''',
#     params=[
#         {
#             'name': 'coin_id',
#             'in': 'formData',
#             'description': 'ID of the coin',
#             'required': True,
#             'type': 'string',
#             'example': '1'
#         },
#         {
#             'name': 'section_id',
#             'in': 'formData',
#             'description': 'ID of the section',
#             'required': True,
#             'type': 'string',
#             'example': '1'
#         },
#         {
#             'name': 'content',
#             'in': 'formData',
#             'description': 'Analysis content with title and body separated by <br>',
#             'required': True,
#             'type': 'string',
#             'example': 'Bitcoin Analysis<br>This is the main content of the analysis...'
#         },
#         {
#             'name': 'category_name',
#             'in': 'formData',
#             'description': 'Name of the category',
#             'required': True,
#             'type': 'string',
#             'example': 'Technical Analysis'
#         },
#         {
#             'name': 'image_url',
#             'in': 'formData',
#             'description': 'URL of the pre-generated image (DALL-E or S3)',
#             'required': True,
#             'type': 'string',
#             'example': 'https://appanalysisimages.s3.amazonaws.com/image.jpg'
#         }
#     ],
#     responses={
#         '201': {
#             'description': 'Analysis created successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {
#                         'type': 'object',
#                         'description': 'Created analysis data',
#                         'properties': {
#                             'id': {'type': 'integer'},
#                             'coin_id': {'type': 'integer'},
#                             'content': {'type': 'string'},
#                             'image_url': {'type': 'string'},
#                             'category_name': {'type': 'string'},
#                             'created_at': {'type': 'string', 'format': 'date-time'}
#                         }
#                     },
#                     'message': {'type': 'string', 'example': 'Analysis published successfully'},
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
#                     'error': {'type': 'string', 'example': 'Missing required parameters: coin_id, content'},
#                     'success': {'type': 'boolean', 'example': False}
#                 }
#             }
#         },
#         '500': {
#             'description': 'Server error',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {'type': 'null'},
#                     'error': {'type': 'string', 'example': 'An unexpected error occurred'},
#                     'success': {'type': 'boolean', 'example': False}
#                 }
#             }
#         }
#     },
#     request_body=None  # Remove request_body since we're using formData parameters
# )
# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/schedule_post')
# print(message)


