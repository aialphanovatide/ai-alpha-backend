# Discord Bot

This is a Discord bot that allows user verification through a role-based system using email verification. The bot is designed to interact with members of a Discord server, assigning roles based on their email verification status.

## Features

- **User Verification**: Users can verify their account by responding to a message with their email address.
- **Role Assignment**: Depending on the verification, users will receive specific roles in the server.
- **Event Handling**: The bot listens for events such as reaction additions and connection to Discord.

## Requirements

- Python 3.8 or higher
- The following Python libraries:
  - `discord.py`
  - `python-dotenv`

You can install the necessary dependencies using pip:
pip install discord.py python-dotenv


This will start the bot and connect it to your Discord server. Once the bot is online, you can interact with it using the prefix `!`.

## Commands

- `!verify <your-email@example.com>`: This command allows users to verify their email and receive the corresponding role.

## Contributions

Contributions are welcome. If you would like to improve the bot, please open an issue or a pull request.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.