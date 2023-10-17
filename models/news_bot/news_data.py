from .news_bot_model import SCRAPPING_DATA, BLACKLIST, SITES, KEWORDS
from config import session
from pathlib import Path
import json

ROOT_DIRECTORY = Path(__file__).parent.resolve()

# Populates the sites and keyword tables
if not session.query(SCRAPPING_DATA).first():

    with open(f'{ROOT_DIRECTORY}\summary_bot\data.json', 'r') as data_file:
        config = json.load(data_file)

    for item in config:   
        keyword = item['main_keyword']
        keywords = item['keywords']
        sites = item['sites']
        black_list = item['black_list']

        scrapping_data = SCRAPPING_DATA(main_keyword=keyword.casefold())

        for keyword in keywords:
            scrapping_data.keywords.append(KEWORDS(keyword=keyword.casefold()))

        for word in black_list:
            scrapping_data.blacklist.append(BLACKLIST(black_Word=word.casefold()))

        for site_data in sites:
            site = SITES(
                site=site_data['site'],
                base_url=site_data['base_url'],
                website_name=site_data['website_name'],
                is_URL_complete=site_data['is_URL_complete']
            )
            scrapping_data.sites.append(site)

        
        session.add(scrapping_data)

    print('Initial site data saved to db')
    session.commit()