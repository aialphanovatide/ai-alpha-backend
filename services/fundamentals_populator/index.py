from typing import Dict, List, Optional, Any
import asyncio
from config import CoinBot, Session
from config import Revenue_model, Upgrades, Hacks, DApps, Competitor, Tokenomics
from routes.fundamentals.competitors import normalize_key
from services.coingecko.coingecko import get_competitors_data, get_tokenomics_data
from services.fundamentals_populator.perplexity import get_perplexity_reponse
from .utils import extract_data_by_section
from flask import Flask, jsonify
from collections import defaultdict

app = Flask(__name__)

class FundamentalAuto:
    """
    A class to handle automatic fundamental data population for cryptocurrencies.

    This class manages the retrieval and storage of various types of cryptocurrency data,
    including revenue, upgrades, hacks, DApps, competitors, and tokenomics.

    Attributes:
        session: SQLAlchemy session for database operations
        coin_bot_id (int): Unique identifier for the coin bot
        coin_name (str): Name of the cryptocurrency
        gecko_id (str): CoinGecko ID for the cryptocurrency
    """

    def __init__(self, coin_bot_id: int, coin_name: str, gecko_id: str):
        """
        Initialize the FundamentalAuto instance.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            coin_name (str): The name of the cryptocurrency
            gecko_id (str): The CoinGecko ID for the cryptocurrency
        """
        self.session = Session()
        self.coin_bot_id = coin_bot_id
        self.coin_name = coin_name
        self.gecko_id = gecko_id

    async def search_fundamental_data(self) -> None:
        """
        Main function to fetch and save data for all sections.

        This function orchestrates the data fetching and saving process for revenue,
        upgrades, hacks, and DApps sections.

        Raises:
            ValueError: If any section name is invalid
        """
        sections = ['revenue', 'upgrades', 'hacks', 'dapps']
        all_search_results = {}

        for section in sections:
            search_result = await self.search_data(section)
            if search_result is None:
                raise ValueError(f"Invalid section name: {section}")
            all_search_results[section] = search_result

        await self.save_all_data(self.coin_bot_id, all_search_results)

    async def search_data(self, section_name: str) -> Optional[Dict]:
        """
        Search for data based on the section and coin name.

        Args:
            section_name (str): The name of the section to search

        Returns:
            Optional[Dict]: The extracted data for the section, or None if the query is invalid
        """
        coins = [self.coin_name]
        total_content = {}

        max_attempts = 3
        for attempt in range(max_attempts):
            total_content = get_perplexity_reponse(coins)

            if section_name.lower() == 'revenue' and total_content.get(self.coin_name) is None:
                print(f"[WARNING] Attempt {attempt + 1} failed to retrieve revenue data for {self.coin_name}. Retrying...")
                await asyncio.sleep(1)
                continue

            break

        return extract_data_by_section(section_name, total_content)

    async def save_all_data(self, coin_bot_id: int, extracted_data: Dict) -> None:
        """
        Save all extracted data into the corresponding tables.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            extracted_data (Dict): The data extracted from the search
        """
        with app.app_context():
            await self.save_fundamental_data(coin_bot_id, extracted_data)
            await self.save_competitor_data(coin_bot_id)
            await self.save_tokenomics_data(coin_bot_id)
            
    async def save_fundamental_data(self, coin_bot_id: int, content: Dict[str, Any]) -> None:
        """
        Save fundamental data into the database.

        Processes and saves different types of fundamental data (revenue, upgrades, hacks, DApps)
        into their respective database models.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            content (Dict[str, Any]): Dictionary containing the extracted fundamental data

        Raises:
            ValueError: If an invalid section name is encountered
        """
        for section_name, data in content.items():
            if section_name.lower() == 'revenue':
                await self._save_revenue_data(coin_bot_id, data)
            elif section_name.lower() == 'upgrades':
                await self._save_upgrades_data(coin_bot_id, data)
            elif section_name.lower() == 'hacks':
                await self._save_hacks_data(coin_bot_id, data)
            elif section_name.lower() == 'dapps':
                await self._save_dapps_data(coin_bot_id, data)
            else:
                raise ValueError(f'Invalid section name: {section_name}')

    async def _save_revenue_data(self, coin_bot_id: int, data: Any) -> None:
        """
        Save revenue data into the database.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            data (Any): Revenue data to be saved
        """
        new_entry = Revenue_model(
            coin_bot_id=coin_bot_id,
            analized_revenue=str(data),
            fees_1ys=None,
            dynamic=True
        )
        self.session.add(new_entry)
        self.session.commit()
        print(f"[SUCCESS] Revenue data saved for coin_bot_id: {coin_bot_id}")

    async def _save_upgrades_data(self, coin_bot_id: int, data: Dict) -> None:
        """
        Save upgrades data into the database.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            data (Dict): Dictionary containing upgrades data
        """
        if isinstance(data, dict) and 'solana' in data:
            upgrades_list = data['solana']
            for upgrade in upgrades_list:
                new_entry = Upgrades(
                    coin_bot_id=coin_bot_id,
                    event=upgrade.get('Event'),
                    date=upgrade.get('Date'),
                    event_overview=upgrade.get('Event Overview'),
                    impact=upgrade.get('Impact'),
                    dynamic=True
                )
                self.session.add(new_entry)
            self.session.commit()
            print(f"[SUCCESS] Upgrades data saved for coin_bot_id: {coin_bot_id}")
        else:
            print("[WARNING] Upgrades data is not in the expected format for coin_bot_id:", coin_bot_id)

    async def _save_hacks_data(self, coin_bot_id: int, data: Dict) -> None:
        """
        Save hacks data into the database.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            data (Dict): Dictionary containing hacks data
        """
        if isinstance(data, dict) and 'solana' in data:
            hacks_list = data['solana']
            for hack in hacks_list:
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
            self.session.commit()
            print(f"[SUCCESS] Hacks data saved for coin_bot_id: {coin_bot_id}")
        else:
            print("[WARNING] Hacks data is not in the expected format for coin_bot_id:", coin_bot_id)

    async def _save_dapps_data(self, coin_bot_id: int, data: Dict) -> None:
        """
        Save DApps data into the database.

        Args:
            coin_bot_id (int): The ID of the CoinBot
            data (Dict): Dictionary containing DApps data
        """
        if isinstance(data, dict) and 'solana' in data:
            dapps_list = data['solana']
            for dapp in dapps_list:
                new_entry = DApps(
                    coin_bot_id=coin_bot_id,
                    dapps=dapp.get('DApp'),
                    description=dapp.get('Description'),
                    tvl=str(dapp.get('TVL')),
                    dynamic=True
                )
                self.session.add(new_entry)
            self.session.commit()
            print(f"[SUCCESS] DApps data saved for coin_bot_id: {coin_bot_id}")
        else:
            print("[WARNING] DApps data is not in the expected format for coin_bot_id:", coin_bot_id)

    async def save_competitor_data(self, coin_bot_id: int) -> None:
        """
        Save competitor data into the database.

        This function retrieves competitor data and saves it into the Competitor model.

        Args:
            coin_bot_id (int): The ID of the CoinBot
        """
        competitor_data = get_competitors_data(self.coin_name)
        if competitor_data:
            print(f"Saving competitor data: {competitor_data}")
            for competitor in competitor_data:
                new_entry = Competitor(
                    coin_bot_id=coin_bot_id,
                    name=competitor.get('name'),
                    market_cap=competitor.get('market_cap'),
                    volume=competitor.get('volume'),
                    dynamic=True
                )
                self.session.add(new_entry)
            self.session.commit()
            print(f"[SUCCESS] Competitor data saved for coin_bot_id: {coin_bot_id}")
        else:
            print("[WARNING] No competitor data found for coin_bot_id:", coin_bot_id)

    async def save_tokenomics_data(self, coin_bot_id: int) -> None:
        """
        Save tokenomics data into the database.

        This function retrieves tokenomics data and saves it into the Tokenomics model.

        Args:
            coin_bot_id (int): The ID of the CoinBot
        """
        tokenomics_data = get_tokenomics_data(self.gecko_id)
        if isinstance(tokenomics_data, dict):
            tokenomics_data = [tokenomics_data]

        if isinstance(tokenomics_data, list):
            print(f"Saving tokenomics data: {tokenomics_data}")
            for tokenomic in tokenomics_data:
                new_entry = Tokenomics(
                    coin_bot_id=coin_bot_id,
                    token=tokenomic.get('token'),
                    total_supply=tokenomic.get('Total Supply'),
                    circulating_supply=tokenomic.get('Circulating Supply'),
                    percentage_circulating_supply=tokenomic.get('% Circulating Supply'),
                    max_supply=tokenomic.get('Max Supply'),
                    supply_model=tokenomic.get('supply_model'),
                    dynamic=True
                )
                self.session.add(new_entry)
            self.session.commit()
            print(f"[SUCCESS] Tokenomics data saved for coin_bot_id: {coin_bot_id}")
        else:
            print("[WARNING] Tokenomics data is not in the expected format for coin_bot_id:", coin_bot_id)




# # Initialize parameters
# coin_bot_id = 4
# coin_name = 'dot'
# gecko_id = 'polkadot'

# # Create an instance of FundamentalAuto
# pipeline = FundamentalAuto(coin_bot_id, coin_name, gecko_id)

# # Call the search_fundamental_data method
# async def fetch_and_save_data():
#     try:
#         await pipeline.search_fundamental_data()
#         print("Data fetching and saving completed successfully.")
#     except Exception as e:
#         print(f"An error occurred: {e}")

        
# if __name__ == '__main__':
#     asyncio.run(fetch_and_save_data())