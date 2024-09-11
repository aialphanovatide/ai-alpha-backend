# Helper function to updated the Swagger JSON file

import os
import json

class Swagger:
    def __init__(self):
        self.path = os.path.join('static', 'swagger.json')

    def load(self):
        try:
            with open(self.path, 'r') as file:
                self.swagger_json = json.load(file)
            return self.swagger_json
        except FileNotFoundError:
            print(f"Error: Swagger file not found at {self.path}")
            return None
        except json.JSONDecodeError:
            print(f"Error: Invalid JSON in Swagger file at {self.path}")
            return None
        except Exception as e:
            print(f"Unexpected error loading Swagger file: {str(e)}")
            return None

    def add_or_update_endpoint(self, endpoint_route: str, method: str, tag: str, description: str, params: list, responses: dict):
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
            for param in params:
                parameter = {
                    'name': param['name'],
                    'in': param.get('in', 'query'),
                    'description': param.get('description', ''),
                    'required': param.get('required', False),
                    'type': param['type']
                }
                swagger_json['paths'][endpoint_route][method]['parameters'].append(parameter)

            # Update the Swagger JSON file
            with open(self.path, 'w') as file:
                json.dump(swagger_json, file, indent=2)

            action = "updated" if endpoint_exists else "added"
            return True, f'Endpoint {endpoint_route} [{method}] {action} successfully'
        except Exception as e:
            return False, f'Error adding/updating endpoint {endpoint_route} [{method}]: {str(e)}'

    def delete_endpoint(self, endpoint_route: str):
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
#     endpoint_route='/get_analysis/test',
#     method='get',
#     tag='analysis',
#     description='Retrieve analyses with their associated images, with pagination.',
#     params=[
#         {
#             'name': 'page',
#             'in': 'query',
#             'type': 'integer',
#             'description': 'The page number (default: 1)',
#             'required': False,
#             'default': 1
#         },
#         {
#             'name': 'limit',
#             'in': 'query',
#             'type': 'integer',
#             'description': 'The number of items per page (default: 10, max: 100)',
#             'required': False,
#             'default': 10,
#             'maximum': 100
#         }
#     ],
#     responses={
#         '200': {
#             'description': 'Successful response',
#         },
#         '400': {
#             'description': 'Bad Request - Invalid pagination parameters',
#         },
#         '500': {
#             'description': 'Internal Server Error',
#         }
#     }
# )
# print(message)


# ____Delete an endpoint____

# success, message = swagger.delete_endpoint(endpoint_route='/get_analysis/test')
# print(message)


