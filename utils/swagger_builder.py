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

    def add_or_update_endpoint(self, endpoint_route: str, method: str, tag: str, description: str, params: list, responses: dict) -> Tuple[bool, str]:
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
                'summary': description.capitalize(),
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


# success, message = swagger.add_or_update_endpoint(
#     endpoint_route='/schedule-narrative-trading',
#     method='post',
#     tag='Narrative Trading',
#     description='Schedule a narrative trading post for future publishing.',
#     params=[
#         {
#             'name': 'coin_id',
#             'in': 'formData',
#             'type': 'string',
#             'description': 'ID of the coin bot',
#             'required': True
#         },
#         {
#             'name': 'category_name',
#             'in': 'formData',
#             'type': 'string',
#             'description': 'Name of the category',
#             'required': False
#         },
#         {
#             'name': 'content',
#             'in': 'formData',
#             'type': 'string',
#             'description': 'Content of the post',
#             'required': True
#         },
#         {
#             'name': 'scheduled_date',
#             'in': 'formData',
#             'type': 'string',
#             'description': 'Scheduled date and time for publishing (format: "%a, %b %d, %Y, %I:%M:%S %p")',
#             'required': True
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Post scheduled successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean'},
#                     'message': {'type': 'string'}
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad request - Missing required parameters or invalid date format',
#         },
#         '500': {
#             'description': 'Internal server error',
#         }
#     }
# )
# print(message)

# success, message = swagger.add_or_update_endpoint(
#     endpoint_route='/scheduled-narrative-tradings',
#     method='get',
#     tag='Narrative Trading',
#     description='Retrieve a list of all scheduled narrative trading jobs.',
#     params=[],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved scheduled jobs',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean'},
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'jobs': {
#                                 'type': 'array',
#                                 'items': {
#                                     'type': 'object',
#                                     'properties': {
#                                         'id': {'type': 'string'},
#                                         'name': {'type': 'string'},
#                                         'trigger': {'type': 'string'},
#                                         'args': {'type': 'string'},
#                                         'next_run_time': {'type': 'string'}
#                                     }
#                                 }
#                             }
#                         }
#                     }
#                 }
#             }
#         },
#         '500': {
#             'description': 'Internal server error',
#         }
#     }
# )
# print(message)


# success, message = swagger.add_or_update_endpoint(
#     endpoint_route='/scheduled-narrative-tradings/{job_id}',
#     method='delete',
#     tag='Narrative Trading',
#     description='Delete a scheduled narrative trading job by job ID.',
#     params=[
#         {
#             'name': 'job_id',
#             'in': 'path',
#             'type': 'string',
#             'description': 'ID of the job to delete',
#             'required': True
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Scheduled job deleted successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'success': {'type': 'boolean'},
#                     'message': {'type': 'string'}
#                 }
#             }
#         },
#         '404': {
#             'description': 'Scheduled job not found',
#         },
#         '500': {
#             'description': 'Internal server error',
#         }
#     }
# )
# print(message)

# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/schedule_narrative_post')
# print(message)


