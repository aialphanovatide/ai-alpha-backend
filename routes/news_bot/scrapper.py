from routes.news_bot.validations import title_in_blacklist, url_in_db, title_in_db
from routes.news_bot.sites.cointelegraph import validate_cointelegraph_article
from routes.news_bot.sites.beincrypto import validate_beincrypto_article
from routes.news_bot.sites.bitcoinist import validate_bitcoinist_article
from routes.news_bot.sites.coindesk import validate_coindesk_article
from routes.news_bot.sites.coingape import validate_coingape_article
from models.news_bot.news_bot_model import SCRAPPING_DATA
from playwright.sync_api import sync_playwright
from config import session
import re


def scrape_sites(site,base_url, website_name, is_URL_complete, main_keyword, main_container):

    article_urls = set()

    print('main_container > ', main_container)
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()


            page.goto(site)
            page.wait_for_load_state('networkidle')

            if main_container != "None":
                container = page.wait_for_selector(main_container)
                a_elements = container.query_selector_all('a')
            else:
                a_elements = page.query_selector_all('a')
                print('a_elements > ', a_elements)

                

            for link in a_elements:
                href = link.get_attribute('href')
                article_title = link.text_content().strip().casefold()

                if href and article_title:
                    if is_URL_complete == False:
                        article_url = base_url + href.strip()
                    else:
                        article_url = href.strip()

                    
                    # if main_keyword == 'bitcoin':
                    #     input_title_formatted = str(article_title).strip().casefold()
                    #     title_validation = bool(re.search(main_keyword, input_title_formatted, re.IGNORECASE))
                    # else:
                    #     title_validation = True
    
                    is_url_in_db = url_in_db(article_url)
                    # is_title_in_db = title_in_db(article_title)
                    is_title_in_blacklist = title_in_blacklist(article_title)
            
                    # if title_validation == True:
                    if is_title_in_blacklist == False:
                        # if is_url_in_db == False and is_title_in_db == False:
                        if is_url_in_db == False:
                            article_urls.add(article_url)


            browser.close()
            return article_urls, website_name
        
    except Exception as e:
        print(f'An error occurred: {str(e)}')
        return f'An error occurred: {str(e)}'
                 


def scrape_articles(sites, main_keyword):

    try:
        site = sites.site
        base_url = sites.base_url
        website_name = sites.website_name
        is_URL_complete = sites.is_URL_complete
        main_container = sites.main_container

        print(f'Web scrape of {main_keyword} STARTED for {website_name}')

        article_urls, website_name = scrape_sites(site,base_url,
                                                   website_name,
                                                   is_URL_complete,
                                                   main_keyword,
                                                   main_container)
        
        if not article_urls:
            print(f'No articles found for {website_name}')
            return f'No articles found for {website_name}'
        

        print('article_urls > ', article_urls)
        if article_urls:
            for article_link in article_urls:

                article_to_save = []

                if website_name == 'Beincrypto':
                    title, content, valid_date, image_urls = validate_beincrypto_article(article_link, main_keyword)
                    if title and content and valid_date:
                        article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                if website_name == 'Bitcoinist':
                    title, content, valid_date, image_urls = validate_bitcoinist_article(article_link, main_keyword)
                    if title and content and valid_date:
                        article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                if website_name == 'Cointelegraph':
                    title, content, valid_date, image_urls = validate_cointelegraph_article(article_link, main_keyword)
                    if title and content and valid_date:
                        article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                if website_name == 'Coingape':
                    title, content, valid_date, image_urls = validate_coingape_article(article_link, main_keyword)
                    if title and content and valid_date:
                        article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                if website_name == 'Coindesk':
                    title, content, valid_date, image_urls = validate_coindesk_article(article_link, main_keyword)
                    if title and content and valid_date:
                        article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                
                if len(article_to_save) > 0:
                    print('\narticle_to_save > ', article_to_save)
                
            #     for article_data in article_to_save:
            #         title, content, valid_date, article_link, website_name, image_urls = article_data

            #         new_article = ARTICLE(title=title,
            #                             content=content,
            #                             date=valid_date,
            #                             url=article_link,
            #                             website_name=website_name
            #                             )

            #         session.add(new_article)
            #         session.commit()
                    
                    
            #         if main_keyword == 'bitcoin':
            #             channel_id = btc_slack_channel_id
            #         elif main_keyword == 'ethereum':
            #             channel_id = eth_slack_channel_id
            #         elif main_keyword == 'hacks':
            #             channel_id = hacks_slack_channel_id
            #         else:
            #             channel_id = lsd_slack_channel_id

            #         summary = summary_generator(content, main_keyword)

            #         if summary:
            #             send_NEWS_message_to_slack(channel_id=channel_id, 
            #                                 title=title,
            #                                 date_time=valid_date,
            #                                 url=article_link,
            #                                 summary=summary,
            #                                 images_list=image_urls
            #                                 )
            #             print(f'\nArticle: "{title}" has been added to the DB, Link: {article_link} from {website_name} in {main_keyword.capitalize()}.')
            #         else:
            #             send_INFO_message_to_slack_channel(channel_id=channel_id, title_message='Error generating summary',sub_title='Reason', message=f'OpenAI did not respond for the article: {title} with link: {article_link}.')
            
            return f'Web scrapping of {website_name} finished', 200
        
    except Exception as e:
        return f'Error in scrape_articles: {str(e)}', 500
    

def start_periodic_scraping(main_keyword):

    scrapping_data_objects = session.query(SCRAPPING_DATA).filter(SCRAPPING_DATA.main_keyword == main_keyword).all()

    if not scrapping_data_objects:
        print(f'Bot with keyword {main_keyword} was not found')
        return f'Bot with keyword {main_keyword} was not found'
    else:
        sites = scrapping_data_objects[0].sites
        for site in sites:
            scrape_articles(site, main_keyword)

        return f'All {str(main_keyword).casefold().capitalize()} sites scraped', 200