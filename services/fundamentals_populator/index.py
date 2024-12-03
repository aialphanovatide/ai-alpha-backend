import asyncio
from config import CoinBot, Session
from models import Revenue_model, Upgrades, Hacks, DApps, Competitor, Tokenomics, Token_distribution, Token_utility, Value_accrual_mechanisms
from routes.fundamentals.competitors import normalize_key
from services.coingecko.coingecko import get_competitors_data, get_tokenomics_data
from .utils import extract_data_by_section
from .perplexity import search_perplexity
from flask import jsonify, request
from collections import defaultdict


class FundamentalAuto:
    def __init__(self, coin_bot_id: int, coin_name: str):
        """Initialize the FundamentalAuto with necessary parameters.

        Args:
            coin_bot_id (int): The ID of the CoinBot.
            coin_name (str): The name of the cryptocurrency.
        """
        self.session = Session()
        self.coin_bot_id = coin_bot_id
        self.coin_name = coin_name

    async def search_fundamental_data(self):
        """Main function to fetch and save data for all sections.

        This function orchestrates the data fetching and saving process for all sections.
        
        Raises:
            ValueError: If any section name is invalid.
        """
        sections = ['revenue', 'upgrade', 'hacks', 'dapps']
        all_search_results = {}

        for section in sections:
            search_result = await self.search_data(section)
            if search_result is None:
                raise ValueError(f"Invalid section name: {section}")
            all_search_results[section] = search_result

        # Save data to the corresponding tables
        await self.save_all_data(self.coin_bot_id, all_search_results)

    async def search_data(self, section_name: str):
        """Search for data based on the section and coin name.

        This function constructs a query and retrieves data from the search service.

        Args:
            section_name (str): The name of the section to search.

        Returns:
            dict or None: The extracted data for the section, or None if the query is invalid.
        """
        query = self.get_query(section_name, self.coin_name)
        if query is None:
            return None

        # Perform the search
        search_result = await search_perplexity(query)
        return extract_data_by_section(section_name, search_result)

    async def save_all_data(self, coin_bot_id: int, extracted_data):
        """Save all extracted data into the corresponding tables.

        This function calls individual save methods for different data types.

        Args:
            coin_bot_id (int): The ID of the CoinBot.
            extracted_data (dict): The data extracted from the search.
        """
        await self.save_fundamental_data(coin_bot_id, extracted_data)
        await self.save_competitor_data(coin_bot_id)
        await self.save_tokenomics_data(coin_bot_id)

    async def save_fundamental_data(self, coin_bot_id: int, content):
        """Save fundamental data into the database.

        This function processes the extracted data and saves it into the appropriate models.

        Args:
            coin_bot_id (int): The ID of the CoinBot.
            content (dict): The extracted fundamental data.
        
        Raises:
            ValueError: If an invalid section name is encountered.
        """
        for section_name, data in content.items():
            if section_name.lower() == 'revenue':
                new_entry = Revenue_model(
                    coin_bot_id=coin_bot_id,
                    analized_revenue=str(data),
                    fees_1ys=None,
                    dynamic=True
                )
                self.session.add(new_entry)

            elif section_name.lower() == 'upgrade':
                for upgrade in data:
                    new_entry = Upgrades(
                        coin_bot_id=coin_bot_id,
                        event=upgrade.get('Event'),
                        date=upgrade.get('Date'),
                        event_overview=upgrade.get('Event Overview'),
                        impact=upgrade.get('Impact'),
                        dynamic=True
                    )
                    self.session.add(new_entry)

            elif section_name.lower() == 'hacks':
                for hack in data:
                    new_entry = Hacks(
                        coin_bot_id=coin_bot_id,
                        hack_name=hack.get('Hack Name'),
                        date=hack.get('Date'),
                        incident_description=hack.get('Incident Description'),
                        consequences=hack.get('Consequences'),
                        mitigation_measure=hack.get('Risk Mitigation Measures'),
                        dynamic=True
                    )
                    self.session.add(new_entry)

            elif section_name.lower() == 'dapps':
                for dapp in data:
                    new_entry = DApps(
                        coin_bot_id=coin_bot_id,
                        dapps=dapp.get('DApp'),
                        description=dapp.get('Description'),
                        tvl=str(dapp.get('TVL')),
                        dynamic=True
                    )
                    self.session.add(new_entry)

            else:
                raise ValueError(f'Invalid section name: {section_name}')

    async def save_competitor_data(self, coin_bot_id: int):
        """Save competitor data into the database.

        This function retrieves competitor data and saves it into the Competitor model.

        Args:
            coin_bot_id (int): The ID of the CoinBot.
        """
        competitor_data = self.get_competitor_data(coin_bot_id)
        if competitor_data:
            for token, data in competitor_data.items():
                for key, value in data['attributes'].items():
                    new_entry = Competitor(
                        coin_bot_id=coin_bot_id,
                        token=token,
                        key=key,
                        value=value['value']
                    )
                    self.session.add(new_entry)

    async def save_tokenomics_data(self, coin_bot_id: int):
        """Save tokenomics data into the database.

        This function retrieves tokenomics data and saves it into the Tokenomics model.

        Args:
            coin_bot_id (int): The ID of the CoinBot.
        """
        tokenomics_data = self.get_tokenomics_data(coin_bot_id)
        if tokenomics_data:
            for tokenomic in tokenomics_data:
                new_entry = Tokenomics(
                    coin_bot_id=coin_bot_id,
                    token=tokenomic.get('token'),
                    total_supply=tokenomic.get('total_supply'),
                    circulating_supply=tokenomic.get('circulating_supply'),
                    percentage_circulating_supply=tokenomic.get('percentage_circulating_supply'),
                    max_supply=tokenomic.get('max_supply'),
                    supply_model=tokenomic.get('supply_model'),
                    dynamic=True
                )
                self.session.add(new_entry)

    def get_query(self, section_name, coin_name):
        """Return the appropriate query based on the section and coin name.

        This function constructs a query string for the specified section and coin.

        Args:
            section_name (str): The name of the section to query.
            coin_name (str): The name of the cryptocurrency.

        Returns:
            str or None: The constructed query string, or None if the section name is invalid.
        """
        queries = {
            "revenue": f"Please return only the current or past Annualised Revenue (Cumulative last 1yr revenue) for the ${coin_name} cryptocurrency as a single numerical value in JSON format.",
            "upgrade": f"""
            Please provide, in JSON code format, all available data related to UPGRADES in ${coin_name} cryptocurrency. Structure the information for each upgrade as follows:
            {{
              "Event": "",
              "Date": "",
              "Event Overview": "",
              "Impact": ""
            }}
            """,
            "hacks": f"""
            Please provide, ONLY IN JSON format, all available data related to hacks about ${coin_name} cryptocurrency. Structure the information for each hack as follows:
            {{
              "Hack Name": "",
              "Date": "",
              "Incident Description": "",
              "Consequences": "",
              "Risk Mitigation Measures": ""
            }}
            """,
            "dapps": f"""
            Please provide, in JSON code format, all available data related to top DApps about ${coin_name} cryptocurrency. Structure the information for each DApp as follows:
            {{
              "DApp": "",
              "Description": "",
              "TVL": ""
            }}
            """
        }
        return queries.get(section_name.lower(), None)

    def get_competitor_data(self, coin_bot_id):
        """Retrieve competitor data for the specified CoinBot.

        This function queries the database for competitor data and enriches it with data from CoinGecko.

        Args:
            coin_bot_id (int): The ID of the CoinBot.

        Returns:
            dict: A dictionary containing competitor data, or an error response if an exception occurs.
        """
        try:
            if coin_bot_id is None:
                return jsonify({'message': 'Coin ID is required', 'status': 400}), 400

            coin_data = self.session.query(Competitor).filter(Competitor.coin_bot_id == coin_bot_id).all()

            if not coin_data:
                return jsonify({'message': 'No data found for the requested coin', 'status': 404}), 404

            token_data = defaultdict(lambda: {'symbol': '', 'attributes': {}})

            for competitor in coin_data:
                token = competitor.token.strip().upper()
                key = competitor.key.strip()
                value = competitor.value

                if not token_data[token]['symbol']:
                    token_data[token]['symbol'] = token
                
                token_data[token]['attributes'][key] = {
                    'value': value,
                    'is_coingecko_data': False,
                    'id': competitor.id
                }

            for token in token_data:
                coingecko_data = get_competitors_data(token)  # Ensure this function is defined
                if isinstance(coingecko_data, dict):
                    for tokenomics_key, tokenomics_value in coingecko_data.items():
                        normalized_tokenomics_key = normalize_key(tokenomics_key)  # Ensure this function is defined
                        matched = False
                        for existing_key in list(token_data[token]['attributes'].keys()):
                            if set(normalized_tokenomics_key.split()) & set(normalize_key(existing_key).split()):
                                token_data[token]['attributes'][existing_key] = {
                                    'value': tokenomics_value,
                                    'is_coingecko_data': True,
                                    'id': token_data[token]['attributes'][existing_key]['id']
                                }
                                matched = True
                                break
                        if not matched:
                            token_data[token]['attributes'][tokenomics_key] = {
                                'value': tokenomics_value,
                                'is_coingecko_data': True,
                                'id': None
                            }

            # Create the final object
            final_data = {}
            for token, data in token_data.items():
                final_data[token] = {
                    'symbol': data['symbol'],
                    'attributes': {k: v for k, v in data['attributes'].items() if v['value'] is not None}
                }

            return final_data  # Return competitor data

        except Exception as e:
            original_data = {}
            for competitor in coin_data:
                token = competitor.token.strip().upper()
                if token not in original_data:
                    original_data[token] = {'symbol': token, 'attributes': {}}
                original_data[token]['attributes'][competitor.key.strip()] = {
                    'value': competitor.value,
                    'is_coingecko_data': False,
                    'id': competitor.id
                }

            return jsonify({
                'competitors': original_data, 
                'status': 200, 
                'message': f'Error processing data, returning original data: {str(e)}'
            }), 200
            
#test

async def main():
    # Initialize the pipeline with example parameters
    coin_bot_id = 1
    coin_name = 'Bitcoin'

    # Create an instance of FundamentalAuto
    pipeline = FundamentalAuto(coin_bot_id, coin_name)

    # Call the search_fundamental_data method
    try:
        await pipeline.search_fundamental_data()
        print("Data fetching and saving completed successfully.")
    except Exception as e:
        print(f"An error occurred: {e}")

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())