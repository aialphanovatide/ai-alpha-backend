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


# # GET /analyses endpoint
# swagger.add_or_update_endpoint(
#     endpoint_route='/analyses',
#     method='get',
#     tag='Analysis',
#     summary='Get all analyses',
#     description='Retrieve all analyses with pagination based on section',
#     params=[
#         {
#             'name': 'section_id',
#             'in': 'query',
#             'description': 'ID of the section',
#             'required': True,
#             'type': 'string'
#         },
#         {
#             'name': 'page',
#             'in': 'query',
#             'description': 'Page number',
#             'required': False,
#             'type': 'integer',
#             'default': 1
#         },
#         {
#             'name': 'limit',
#             'in': 'query',
#             'description': 'Items per page (max 100)',
#             'required': False,
#             'type': 'integer',
#             'default': 10
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved all analyses',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {'type': 'array', 'items': {'type': 'object'}},
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean'},
#                     'total': {'type': 'integer'},
#                     'page': {'type': 'integer'},
#                     'limit': {'type': 'integer'},
#                     'total_pages': {'type': 'integer'},
#                     'section_name': {'type': 'string'},
#                     'section_target': {'type': 'string'}
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad Request',
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

# # GET /analysis/last endpoint
# swagger.add_or_update_endpoint(
#     endpoint_route='/analysis/last',
#     method='get',
#     tag='Analysis',
#     summary='Get last analysis',
#     description='Retrieve the name and date of the last analysis created',
#     params=[],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved last analysis',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {'type': 'object'},
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean', 'example': True}
#                 }
#             }
#         },
#         '404': {
#             'description': 'No analysis found',
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

# # POST /scheduled-analyses endpoint
# swagger.add_or_update_endpoint(
#     endpoint_route='/scheduled-analyses',
#     method='post',
#     tag='Scheduled Analysis',
#     summary='Schedule new analysis',
#     description='Schedule a post for future publication',
#     params=[
#         {
#             'name': 'coin_id',
#             'in': 'formData',
#             'description': 'ID of the coin bot',
#             'required': True,
#             'type': 'string'
#         },
#         {
#             'name': 'section_id',
#             'in': 'formData',
#             'description': 'ID of the section',
#             'required': True,
#             'type': 'string'
#         },
#         {
#             'name': 'category_name',
#             'in': 'formData',
#             'description': 'Name of the category',
#             'required': True,
#             'type': 'string'
#         },
#         {
#             'name': 'content',
#             'in': 'formData',
#             'description': 'Content of the post',
#             'required': True,
#             'type': 'string'
#         },
#         {
#             'name': 'scheduled_date',
#             'in': 'formData',
#             'description': 'Scheduled date and time in ISO 8601 format (e.g., 2023-01-01T12:00:00.000Z)',
#             'required': True,
#             'type': 'string'
#         }
#     ],
#     responses={
#         '201': {
#             'description': 'Post scheduled successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'message': {'type': 'string'},
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean', 'example': True},
#                     'job_id': {'type': 'string'}
#                 }
#             }
#         },
#         '400': {
#             'description': 'Bad Request',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'message': {'type': 'null'},
#                     'error': {'type': 'string'},
#                     'success': {'type': 'boolean', 'example': False},
#                     'job_id': {'type': 'null'}
#                 }
#             }
#         }
#     }
# )

# # GET /scheduled-analyses endpoint
# swagger.add_or_update_endpoint(
#     endpoint_route='/scheduled-analyses',
#     method='get',
#     tag='Scheduled Analysis',
#     summary='Get all scheduled analyses',
#     description='Retrieve information about all scheduled jobs',
#     params=[],
#     responses={
#         '200': {
#             'description': 'Successfully retrieved scheduled jobs',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
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
#                     },
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean', 'example': True}
#                 }
#             }
#         },
#         '500': {
#             'description': 'Server Error',
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

# # GET /scheduled-analyses/{job_id} endpoint
# swagger.add_or_update_endpoint(
#     endpoint_route='/scheduled-analyses/{job_id}',
#     method='get',
#     tag='Scheduled Analysis',
#     summary='Get scheduled analysis by ID',
#     description='Get information about a specific scheduled job',
#     params=[
#         {
#             'name': 'job_id',
#             'in': 'path',
#             'description': 'ID of the scheduled job',
#             'required': True,
#             'type': 'string'
#         }
#     ],
#     responses={
#         '201': {
#             'description': 'Successfully retrieved job information',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'data': {
#                         'type': 'object',
#                         'properties': {
#                             'id': {'type': 'string'},
#                             'name': {'type': 'string'},
#                             'func': {'type': 'string'},
#                             'trigger': {'type': 'string'},
#                             'args': {'type': 'string'},
#                             'next_run_time': {'type': 'string'}
#                         }
#                     },
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean', 'example': True}
#                 }
#             }
#         },
#         '404': {
#             'description': 'Job not found',
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

# # DELETE /scheduled-analyses/{job_id} endpoint
# swagger.add_or_update_endpoint(
#     endpoint_route='/scheduled-analyses/{job_id}',
#     method='delete',
#     tag='Scheduled Analysis',
#     summary='Delete scheduled analysis',
#     description='Delete a scheduled job by its ID',
#     params=[
#         {
#             'name': 'job_id',
#             'in': 'path',
#             'description': 'ID of the scheduled job to delete',
#             'required': True,
#             'type': 'string'
#         }
#     ],
#     responses={
#         '201': {
#             'description': 'Job deleted successfully',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'message': {'type': 'string'},
#                     'error': {'type': 'null'},
#                     'success': {'type': 'boolean', 'example': True}
#                 }
#             }
#         },
#         '404': {
#             'description': 'Job not found',
#             'schema': {
#                 'type': 'object',
#                 'properties': {
#                     'message': {'type': 'null'},
#                     'error': {'type': 'string'},
#                     'success': {'type': 'boolean', 'example': False}
#                 }
#             }
#         }
#     }
# )


# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/api/tv/alerts')
# print(message)


