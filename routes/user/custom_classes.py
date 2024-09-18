from marshmallow import Schema, fields

class UserEditSchema(Schema):
    """
    Schema for validating user edit data.

    This schema defines the structure for editing user information.
    All fields are optional and can be None.

    Attributes:
        full_name (fields.Str): The full name of the user.
        nickname (fields.Str): The nickname or username of the user.
        birth_date (fields.Str): The birth date of the user.
    """
    full_name = fields.Str(allow_none=True)
    nickname = fields.Str(allow_none=True)
    birth_date = fields.Str(allow_none=True)


class UserRegistrationSchema(Schema):
    """
    Schema for validating user registration data.

    This schema defines the structure for registering a new user.
    It includes both required and optional fields.

    Attributes:
        full_name (fields.Str): The full name of the user (required).
        nickname (fields.Str): The nickname or username of the user (required).
        email (fields.Email): The email address of the user (required).
        email_verified (fields.Boolean): Whether the email has been verified (defaults to False).
        picture (fields.Url): URL to the user's profile picture (optional).
        auth0id (fields.Str): The Auth0 ID of the user (optional).
        provider (fields.Str): The authentication provider used (optional).
        birth_date (fields.Str): The birth date of the user (optional).
    """
    full_name = fields.Str(required=True)
    nickname = fields.Str(required=True)
    email = fields.Email(required=True)
    email_verified = fields.Boolean(missing=False)
    picture = fields.Url(allow_none=True)
    auth0id = fields.Str(allow_none=True)
    provider = fields.Str(allow_none=True)
    birth_date = fields.Str(allow_none=True)  # YYYY-MM-DD format
