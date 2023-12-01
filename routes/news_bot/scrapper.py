from routes.news_bot.sites.ambcrypto import validate_ambcrypto_article
from routes.news_bot.sites.blockworks import validate_blockworks_article
from routes.news_bot.sites.coincodex import validate_coincodex_article
from routes.news_bot.sites.coinpedia import validate_coinpedia_article
from routes.news_bot.sites.cryptodaily import validate_cryptodaily_article
from routes.news_bot.sites.cryptopotato import validate_cryptopotato_article
from routes.news_bot.sites.cryptoslate import validate_cryptoslate_article
from routes.news_bot.sites.dailyhodl import validate_dailyhodl_article
from routes.news_bot.sites.decrypto import validate_decrypt_article
from routes.news_bot.sites.investing import validate_investing_article
from routes.news_bot.sites.theblock import validate_theblock_article
from routes.news_bot.sites.utoday import validate_utoday_article
from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from ..slack.templates.news_message import send_NEWS_message_to_slack, send_INFO_message_to_slack_channel
from routes.news_bot.sites.cointelegraph import validate_cointelegraph_article
from routes.news_bot.sites.beincrypto import validate_beincrypto_article
from routes.news_bot.sites.bitcoinist import validate_bitcoinist_article
from routes.news_bot.validations import title_in_blacklist, url_in_db, title_in_db
from routes.news_bot.sites.coindesk import validate_coindesk_article
from routes.news_bot.sites.coingape import validate_coingape_article
from routes.twitter.index import send_tweets_to_twitter
from playwright.sync_api import sync_playwright
from .summarizer import summary_generator
from config import session, CoinBot, AnalyzedArticle, Article, Category, Site

btc_slack_channel_id = 'C05RK7CCDEK'
eth_slack_channel_id = 'C05URLDF3JP'
hacks_slack_channel_id = 'C05UU8JBKKN'
layer_1_lmc_slack_channel_id = 'C05URM66B5Z' 
layer_0_slack_channel_id = 'C05URM3UY8K' 
layer_2_slack_channel = 'C05UB8G8B0F'
layer_1_mmc_slack_channel_id = 'C067ZA4GGNM' 
cross_border_payment_slack_channel = 'C067P4CNC92'
lsd_slack_channel_id = 'C05UNS3M8R3'
oracles_slack_channel = 'C0600Q7UPS4'
defi_slack_channel = 'C067P43P8MA'
defi_perpetual_slack_channel = 'C05UU8EKME0'
defi_others_slack_channel = 'C067HNE4V0D'
ai_slack_channel = 'C067E1LJYKY'

# Note: images_urls sometimes are a list[] and sometimes just return a single string of the a URL.

def get_links(site, main_container):

    try:
       
        with sync_playwright() as p:
                browser = p.chromium.launch()
                page = browser.new_page()

                page.goto(site, timeout=100000)
                page.wait_for_load_state("domcontentloaded")

                elements = []

                if main_container != "None":
                    container = page.wait_for_selector(main_container)
                    a_elements = container.query_selector_all('a')

                    for link in a_elements:
                        href = link.get_attribute('href')
                        article_title = link.text_content().strip().casefold()

                        if href and article_title:
                            elements.append({'href': href, 'article_title': article_title})
                else:
                    links = page.evaluate('''() => {
                        const anchors = Array.from(document.querySelectorAll('a'));
                        return anchors.map(a => ({
                            href: a.href,
                            text: a.textContent.trim().toLowerCase()
                        }));
                    }''')

                    for link in links:
                        href = link['href']
                        article_title = link['text']

                        if href and article_title:
                            elements.append({'href': href, 'article_title': article_title})

                browser.close()
                return elements
        
    except Exception as e:
        print("Error getting links" + str(e)) 


def scrape_sites(data_source_url, base_url, site_name, main_keyword, main_container):

    article_urls = set()
   
    elements = get_links(site=data_source_url,
              main_container=main_container,
              )

    keywords = []

    if main_keyword == 'bitcoin':
        keywords = ['bitcoin', 'btc']
    elif main_keyword == 'ethereum':
        keywords = ['ethereum', 'ether', 'eth']

           
    try:
        
        for link in elements:
            href = link['href']
            article_title = link['article_title']
            
            article_url = base_url + href.strip() if not href.startswith('http') else href.strip()

            if article_url:

                # Check if the article is already analized
                url = article_url.casefold().strip()
                existing_article = session.query(AnalyzedArticle).filter(AnalyzedArticle.url==url).first()

                if not existing_article:
                    new_article = AnalyzedArticle(
                        source=site_name,
                        url=url,
                        is_analyzed=False
                    )

                    session.add(new_article)
                    session.commit() 
                
                    # proceed to make first verification
                    is_title_in_db = title_in_db(article_title)
                    is_title_in_blacklist = title_in_blacklist(article_title)
                    is_url_in_db = url_in_db(url)

                    if not is_title_in_blacklist and not is_url_in_db and not is_title_in_db:

                        if main_keyword == 'bitcoin' or main_keyword == 'ethereum':
                            if any(keyword in article_title.lower() for keyword in keywords):
                                article_urls.add(url)
                        else:
                            article_urls.add(url)   

                if existing_article:
                    is_article_analyzed = existing_article.is_analyzed

                    if not is_article_analyzed:

                        # proceed to make first verification
                        is_title_in_db = title_in_db(article_title)
                        is_title_in_blacklist = title_in_blacklist(article_title)
                        is_url_in_db = url_in_db(article_url)

                        if not is_title_in_blacklist and not is_url_in_db and not is_title_in_db:

                            if main_keyword == 'bitcoin' or main_keyword == 'ethereum':
                                if any(keyword in article_title.lower() for keyword in keywords):
                                    article_urls.add(article_url)
                            else:
                                article_urls.add(article_url)         
        
                
        
        return article_urls, site_name
        
    except Exception as e:
        print(f'An error occurred in scrape_sites' + str(e))
        return f'An error occurred in scrape_sites' + str(e)
                 


def scrape_articles(site, main_keyword, coin_bot_name):

    try:
        site_name = site.site_name
        base_url = site.base_url
        data_source_url = site.data_source_url
        main_container = site.main_container

        print(f'---Web scrape of {main_keyword} STARTED for {site_name}---')

        article_urls, website_name = scrape_sites(data_source_url=data_source_url,
                                                  base_url=base_url,
                                                  site_name=site_name,
                                                  main_container=main_container,
                                                  main_keyword=main_keyword
                                                  )
        

        
        if not article_urls:
            print(f'---No articles found for {website_name} of {main_keyword}---')
            return f'No articles found for {website_name}'
         
       
        
        if article_urls:
            print(f'\n--- {len(article_urls)} ARTICLES TO ANALIZE --- \n', article_urls)
            try:
                counter_articles_saved = 0

                for article_link in article_urls:

                    article_to_save = []
                    
                    if website_name == 'Ambcrypto':
                        title, content, valid_date, image_urls = validate_ambcrypto_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                    if website_name == 'Beincrypto':
                        title, content, valid_date, image_urls = validate_beincrypto_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                    if website_name == 'Bitcoinist':
                        title, content, valid_date, image_urls = validate_bitcoinist_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Blockworks':
                        title, content, valid_date, image_urls = validate_blockworks_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Coincodex':
                        title, content, valid_date, image_urls = validate_coincodex_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                    if website_name == 'Cointelegraph':
                        title, content, valid_date, image_urls = validate_cointelegraph_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                    if website_name == 'Coingape':                        
                        title, content, valid_date, image_urls = validate_coingape_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))

                    if website_name == 'Coindesk':
                        title, content, valid_date, image_urls = validate_coindesk_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                            
                    if website_name == 'Coinpedia':
                        title, content, valid_date, image_urls = validate_coinpedia_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Dailyhodl':
                        title, content, valid_date, image_urls = validate_dailyhodl_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Cryptodaily':
                        title, content, valid_date, image_urls = validate_cryptodaily_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                            
                    if website_name == 'Utoday':
                        title, content, valid_date, image_urls = validate_utoday_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Cryptonews':
                        title, content, valid_date, image_urls = validate_coindesk_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                            
                    if website_name == 'Coincodex':
                        title, content, valid_date, image_urls = validate_coindesk_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Cryptopotato':
                        title, content, valid_date, image_urls = validate_cryptopotato_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Cryptoslate':
                        title, content, valid_date, image_urls = validate_cryptoslate_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Decrypt':
                        title, content, valid_date, image_urls = validate_decrypt_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                            
                    if website_name == 'Investing':
                        title, content, valid_date, image_urls = validate_investing_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls))
                    
                    if website_name == 'Theblock':
                        title, content, valid_date, image_urls = validate_theblock_article(article_link, coin_bot_name)
                        if title and content and valid_date:
                            article_to_save.append((title, content, valid_date, article_link, website_name, image_urls)) 

                    if not article_to_save:
                        print(f"Article did not passed {website_name} validations in {main_keyword}")
                    
                    for article_data in article_to_save:
                        title, content, valid_date, article_link, website_name, image_urls = article_data

                        # summary = summary_generator(content, main_keyword)
                        summary = True
                        
                        channel_mapping = {
                            'btc': btc_slack_channel_id,
                            'eth': eth_slack_channel_id,
                            'hacks': hacks_slack_channel_id,
                            'ldo': lsd_slack_channel_id,
                            'rpl': lsd_slack_channel_id,
                            'fxs': lsd_slack_channel_id,
                            'atom': layer_0_slack_channel_id,
                            'dot': layer_0_slack_channel_id,
                            'qnt': layer_0_slack_channel_id,
                            'ada': layer_1_lmc_slack_channel_id,
                            'sol': layer_1_lmc_slack_channel_id,
                            'avax': layer_1_lmc_slack_channel_id,
                            'near': layer_1_mmc_slack_channel_id,
                            'ftm': layer_1_mmc_slack_channel_id,
                            'kas': layer_1_mmc_slack_channel_id,
                            'matic': layer_2_slack_channel,
                            'arb': layer_2_slack_channel,
                            'op': layer_2_slack_channel,
                            'link': oracles_slack_channel,
                            'api3': oracles_slack_channel,
                            'band': oracles_slack_channel,
                            'xlm': cross_border_payment_slack_channel,
                            'algo': cross_border_payment_slack_channel,
                            'xrp': cross_border_payment_slack_channel,
                            'dydx': defi_perpetual_slack_channel,
                            'velo': defi_perpetual_slack_channel,
                            'gmx': defi_perpetual_slack_channel,
                            'uni': defi_slack_channel,
                            'sushi': defi_slack_channel,
                            'cake': defi_slack_channel,
                            'aave': defi_others_slack_channel,
                            'pendle': defi_others_slack_channel,
                            '1inch': defi_others_slack_channel,
                            'ocean': lsd_slack_channel_id,
                            'fet': lsd_slack_channel_id,
                            'rndr': lsd_slack_channel_id,
                        }

                        channel_id = channel_mapping.get(main_keyword, None)

                        if summary:
                            # send_NEWS_message_to_slack(channel_id=channel_id, 
                            #                     title=title,
                            #                     date_time=valid_date,
                            #                     url=article_link,
                            #                     summary=summary,
                            #                     images_list=image_urls,
                            #                     main_keyword=main_keyword
                            #                     )


                            # if main_keyword == 'bitcoin':
                            #     response, status = send_tweets_to_twitter(content=summary,
                            #                                             title=title)

                            #     if status == 200:
                            #         send_INFO_message_to_slack_channel(channel_id=channel_id,
                            #                                         title_message="New Notification from AI Alpha",
                            #                                         sub_title="Response",
                            #                                         message=response
                            #                                         )
                           
                            site_source = session.query(Site).filter(Site.site_name == site_name).first()
                            coin_bot_id = site_source.coin_bot_id
                            
                            new_article = Article(title=title,
                            summary=summary,
                            date=valid_date,
                            url=article_link,
                            coin_bot_id=coin_bot_id
                            )

                            session.add(new_article)
                            session.commit()
                            counter_articles_saved +=1
                            print(f'\nArticle: "{title}" has been added to the DB, Link: {article_link} from {website_name} in {main_keyword}.')
                        else:
                            print('------ THERE IS NO AN AVAILABLE SUMMARY -----')
                            continue

                
                print(f'\n--- {len(article_urls)} article were analized for {website_name} and {counter_articles_saved} were SAVED\n ---')       

                return f'Web scrapping of {website_name} finished', 200
            
            except Exception as e:
                print(f'Error processing {website_name}: {str(e)}')
        
    except Exception as e:
        return f'--- Error in scrape_articles: {str(e)} ---', 500
    

def start_periodic_scraping(bot_name):

    coin_bots = session.query(CoinBot).filter(CoinBot.bot_name == bot_name.casefold()).all()
    category_id = coin_bots[0].category_id
    category = session.query(Category).filter(Category.category_id == category_id).first()
    category_name = category.category

    for coin_bot in coin_bots:
        sites = coin_bot.sites
        coin_bot_name = coin_bot.bot_name
       
        for site in sites:
            scrape_articles(site, category_name, coin_bot_name)

    return f'All {str(category_name).capitalize()} sites scraped', 200  