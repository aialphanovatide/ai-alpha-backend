from config import Session
from models import Revenue_model, Upgrades, Hacks, DApps
from .utils import extract_data_by_section
from .perplexity import search_perplexity

class FundamentalPipeline:
    def __init__(self):
        self.session = Session()

    async def process_and_save(self, section_name: str, coin_bot_id: int, coin_name: str):
        # Realiza la consulta y obtiene los datos
        query = self.get_query(section_name, coin_name)
        if query is None:
            raise ValueError(f"Invalid section name: {section_name}")

        # Realiza la búsqueda
        search_result = await search_perplexity(query)
        extracted_data = extract_data_by_section(section_name, search_result)

        # Guarda los datos extraídos
        self.save_fundamental_data(section_name, coin_bot_id, extracted_data)

        # Confirma la sesión
        self.session.commit()

    def save_fundamental_data(self, section_name, coin_bot_id, content):
        if section_name.lower() == 'revenue':
            new_entry = Revenue_model(
                coin_bot_id=coin_bot_id,
                analized_revenue=str(content),  # Assuming content is the revenue value
                fees_1ys=None,
                dynamic=True
            )
            self.session.add(new_entry)

        elif section_name.lower() == 'upgrade':
            for upgrade in content:
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
            for hack in content:
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
            for dapp in content:
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

    def get_query(self, section_name, coin_name):
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