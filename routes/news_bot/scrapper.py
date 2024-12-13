
# import datetime
# from io import BytesIO
# from PIL import Image
# import os
# import requests
# import boto3
# from urllib.parse import urlparse
# from playwright.sync_api import sync_playwright
# from routes.news_bot.poster_generator import generate_poster_prompt
# from routes.news_bot.sites.ambcrypto import validate_ambcrypto_article
# from routes.news_bot.sites.blockworks import validate_blockworks_article
# from routes.news_bot.sites.coincodex import validate_coincodex_article
# from routes.news_bot.sites.coinpedia import validate_coinpedia_article
# from routes.news_bot.sites.criptonews import validate_cryptonews_article
# from routes.news_bot.sites.cryptodaily import validate_cryptodaily_article
# from routes.news_bot.sites.cryptopotato import validate_cryptopotato_article
# from routes.news_bot.sites.cryptoslate import validate_cryptoslate_article
# from routes.news_bot.sites.dailyhodl import validate_dailyhodl_article
# from routes.news_bot.sites.decrypto import validate_decrypt_article
# from routes.news_bot.sites.investing import validate_investing_article
# from routes.news_bot.sites.theblock import validate_theblock_article
# from routes.news_bot.sites.utoday import validate_utoday_article
# from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
# from ..slack.templates.news_message import send_NEWS_message_to_slack, send_INFO_message_to_slack_channel
# from routes.news_bot.sites.cointelegraph import validate_cointelegraph_article
# from routes.news_bot.sites.beincrypto import validate_beincrypto_article
# from routes.news_bot.sites.bitcoinist import validate_bitcoinist_article
# from routes.news_bot.validations import title_in_blacklist, url_in_db, title_in_db
# from routes.news_bot.sites.coindesk import validate_coindesk_article
# from routes.news_bot.sites.coingape import validate_coingape_article
# from routes.news_bot.sites.googlenews import validate_google_news_article
# from routes.twitter.index import send_tweets_to_twitter
# from playwright.sync_api import sync_playwright
# from .summarizer import summary_generator
# from sqlalchemy.orm import joinedload
# from dotenv import load_dotenv
# from playwright.async_api import TimeoutError
# from sqlalchemy.exc import IntegrityError, InternalError, InvalidRequestError, IllegalStateChangeError
# from playwright.sync_api import sync_playwright
# from config import ArticleImage, Session, CoinBot, AnalyzedArticle, Article, Category, Site, Keyword, Used_keywords

# load_dotenv()

# AWS_ACCESS = os.getenv('AWS_ACCESS')
# AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')

# btc_slack_channel_id = 'C05RK7CCDEK'
# eth_slack_channel_id = 'C05URLDF3JP'
# hacks_slack_channel_id = 'C05UU8JBKKN'
# layer_1_lmc_slack_channel_id = 'C05URM66B5Z'
# layer_0_slack_channel_id = 'C05URM3UY8K'
# layer_2_slack_channel = 'C05UB8G8B0F'
# layer_1_mmc_slack_channel_id = 'C067ZA4GGNM'
# cross_border_payment_slack_channel = 'C067P4CNC92'
# lsd_slack_channel_id = 'C05UNS3M8R3'
# oracles_slack_channel = 'C0600Q7UPS4'
# defi_slack_channel = 'C067P43P8MA'
# defi_perpetual_slack_channel = 'C05UU8EKME0'
# defi_others_slack_channel = 'C067HNE4V0D'
# ai_slack_channel = 'C067E1LJYKY'


# # Gets the initial links for BITCOIN, ETHEREUM AND SOLANA
# def get_links(site, main_container):
#     base_urls = [
#         "/news",
#         "/article",
#         "/post",
#         "/news/",
#         "/article/",
#         "/post/",
#         "https://cointelegraph.com",
#         "https://beincrypto.com",
#         "https://bitcoinist.com",
#         "https://www.google.com/url?",
#         "https://coingape.com/markets",
#         "https://www.coingape.com/markets",
#         "https://www.coindesk.com/markets/",
#         "https://www.coindesk.com/tech",
#         "https://www.coindesk.com/consensus-magazine",
#         "https://www.coindesk.com/business",
#         "https://www.cryptonews.net",
#         "https://cryptoslate.com",
#         "https://cryptopotato.com",
#         "https://www.theblock.co/news",
#         "https://blockworks.co/news",
#         "https://cryptodaily.co.uk/20",
#         "https://dailyhodl.com",
#         "https://cryptonews.net",
#         "https://www.investing.com/news/cryptocurrency-news",
#         "https://u.today",
#         "https://blockworks.co",
#         "https://www.theblock.co/post",
#         "https://theblock.co/post",
#         "https://coinpedia.org/news",
#         "https://coinpedia.org/press-release",
#         "https://coinpedia.org/guest-post",
#         "https://ambcrypto.com",
#         "https://coincodex.com",
#     ]

#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch(slow_mo=1000, headless=False)
#             page = browser.new_page()

#             page.goto(site, timeout=70000)
#             page.wait_for_load_state("domcontentloaded", timeout=70000)

#             elements = []

#             if main_container != "None":
#                 container = page.wait_for_selector(
#                     main_container, timeout=70000)
#                 a_elements = container.query_selector_all('a')

#                 for link in a_elements:
#                     href = link.get_attribute('href')
#                     article_title = link.text_content().strip().casefold()

#                     if href and article_title:
#                         # Verificar si href comienza con algún base_url
#                         if any(href.startswith(base_url) for base_url in base_urls):
#                             elements.append(
#                                 {'href': href, 'article_title': article_title})
#                             print('Link is VALID for saving:', href)
#                         else:
#                             continue
#                             # print('Link is not valid for saving:', href)

#             else:
#                 links = page.evaluate('''() => {
#                     const anchors = Array.from(document.querySelectorAll('a'));
#                     return anchors.map(a => ({
#                         href: a.href,
#                         text: a.textContent.trim().toLowerCase()
#                     }));
#                 }''')

#                 for link in links:
#                     href = link['href']
#                     article_title = link['text']

#                     if href and article_title:
#                         # Verificar si href comienza con algún base_url
#                         if any(href.startswith(base_url) for base_url in base_urls):
#                             elements.append(
#                                 {'href': href, 'article_title': article_title})
#                             print('Link is VALID for saving:', href)
#                         else:
#                             continue
#                             # print('Link is not valid for saving:', href)

#             browser.close()
#             return elements

#     except TimeoutError as e:
#         print('\nTimeout error in getting links: ' + str(e) + "\n")
#         return False

#     except Exception as e:
#         print("\nError getting links: " + str(e) + "\n")
#         return False


# def resize_and_upload_image_to_s3(image_data, bucket_name, image_filename, target_size=(512, 512)):
#     try:
#         response = requests.get(image_data)
#         if response.status_code == 200:
#             image_binary = response.content
#             image = Image.open(BytesIO(image_binary))
#             image_key = image_filename
            
#             s3 = boto3.client(
#                 's3',
#                 region_name='us-east-2',
#                 aws_access_key_id=AWS_ACCESS,
#                 aws_secret_access_key=AWS_SECRET_KEY
#             )
            
#             # Guardar la imagen original en el bucket mktnewsposters
#             s3.upload_fileobj(BytesIO(image_binary), 'mktnewsposters', image_key)
            
#             # Resize de la imagen
#             resized_image = image.resize(target_size)
            
#             # Subir la imagen redimensionada al bucket indicado
#             with BytesIO() as output:
#                 resized_image.save(output, format="JPEG")
#                 output.seek(0)
#                 s3.upload_fileobj(output, bucket_name, image_key)
            
#             # Obtener la URL de la imagen subida
#             image_url = f"https://{bucket_name}.s3.amazonaws.com/{image_key}"
#             return image_url
#         else:
#             print("Error:", response.status_code)
#             return None
#     except Exception as e:
#         print("Error:", str(e)) 
#         return None


# # Gets the valid article news from Google News - HELPER FOR get_google_news_links
# def resolve_redirects(url):
#     response = requests.get(url, allow_redirects=False)
#     if response.status_code in (300, 301, 302, 303):
#         return resolve_redirects(response.headers['location'])
#     else:
#         return response.url

# ## Gets the initial links for the rest of the categories
# def get_google_news_links(site, main_container, max_links=30):
    
#     base_url = "https://news.google.com/articles"
#     elements = []

#     root_dir = os.path.abspath(os.path.dirname(__file__))
#     user_data_dir = os.path.join(root_dir, 'userDataDir')   
    
#     # Sources we don't want articles from
#     blacklist = ['https://tech-gate.org', 'https://medium.com/', 'https://learn.bybit.com', 'https://www.roubaixxl.fr/',
#                  'https://cryptonews.com/editors/sead-fadilpasic', 'https://uk.movies.yahoo.com']

#     try:
#         with sync_playwright() as p:
#             browser = p.chromium.launch_persistent_context(
#                 user_data_dir=user_data_dir,
#                 headless=False,
#                 bypass_csp=True, 
#                 ignore_https_errors=True, 
#                 accept_downloads=True,
#                 slow_mo=200,
#                 args=['--disable-features=IsolateOrigins,site-per-process', '--no-first-run'], 
#                 )
#             page = browser.pages[0] if browser.pages else browser.new_page()

           
#             page.goto(site, timeout=70000)
#             page.wait_for_load_state("domcontentloaded", timeout=70000)
            
            
#             if main_container != "None":
#                 container = page.wait_for_selector(main_container, timeout=70000)
#                 a_elements = container.query_selector_all('a')
#             else:
#                 a_elements = page.query_selector_all('a')

#             for link in a_elements:
#                     href = link.get_attribute('href')
#                     article_title = link.text_content().strip().casefold()

#                     if href and len(href) > 1 and not href.startswith("https://"): 
#                         continue

#                     try:
#                         parsed_url = urlparse(href)
#                     except Exception as e:
#                         print(f"Invalid URL format: {href}")
#                         continue

#                     if parsed_url.scheme and parsed_url.netloc:
#                         if href.startswith(base_url):
#                             resolved_url = resolve_redirects(href)
#                             if resolved_url.startswith("https://"):
#                                 if not any(resolved_url.startswith(domain) for domain in blacklist):
#                                     elements.append(
#                                         {'href': resolved_url, 'article_title': article_title})
#                                     print('Link is VALID for saving:', resolved_url)
#                                     if len(elements) >= max_links:
#                                         break
#                             else:
#                                 print(f"Skipping URL: {resolved_url}")
#                                 continue
#                         else:
#                             continue
#                     else:
#                         continue
#             else:
#                 links = page.evaluate('''() => {
#                     const anchors = Array.from(document.querySelectorAll('a'));
#                     return anchors.map(a => ({
#                         href: a.href,
#                         text: a.textContent.trim().toLowerCase()
#                     }));
#                 }''')

#                 for link in links:
#                     href = link['href']
#                     article_title = link['text']

#                     if href and len(href) > 1 and not href.startswith("https://"): 
#                         continue

#                     try:
#                         parsed_url = urlparse(href)
#                     except Exception as e:
#                         print(f"Invalid URL format: {href}")
#                         continue

#                     if parsed_url.scheme and parsed_url.netloc:
#                         if href.startswith(base_url):
#                             resolved_url = resolve_redirects(href)
#                             if resolved_url.startswith("https://"):
#                                 if not any(resolved_url.startswith(domain) for domain in blacklist):
#                                     elements.append({'href': resolved_url, 'article_title': article_title})
#                                     print('Link is VALID for saving:',
#                                         resolved_url)
#                                     if len(elements) >= max_links:
#                                         break
#                             else:
#                                 continue
#                         else:
#                             continue
#                     else:
#                         continue

#             browser.close()
#             return elements[:max_links]

#     except TimeoutError as e:
#         print('\nTimeout error in getting links: ' + str(e) + "\n")
#         return False

#     except Exception as e:
#         print("\nError getting links: " + str(e) + "\n")
#         return False

# # Validate the initial links for all the categories
# def scrape_sites(data_source_url, base_url, site_name, category_name, main_container, session_instance):
#     article_urls = set()
#     elements = None

#     if category_name == 'bitcoin':
#         elements = get_links(site=data_source_url,
#                              main_container=main_container,
#                              )
#     else:
#         elements = get_google_news_links(site=data_source_url,
#                                          main_container=main_container,
#                                          )

#     if not elements:
#         print(
#             f"\n---No links found to validate in {site_name} of {category_name}---\n")
#         return (article_urls, site_name), 404

#     keywords = []

#     if category_name == 'bitcoin':
#         keywords = ['bitcoin', 'btc']
#     elif category_name == 'ethereum':
#         keywords = ['ethereum', 'ether', 'eth']

#     try:
#         print(
#             f'\n---{len(elements)} links found in {site_name} of {category_name}---')
#         for link in elements:
#             href = link['href']
#             article_title = link['article_title']

#             article_url = base_url + href.strip() if not href.startswith('http') else href.strip()

#             if article_url:

#                 # Check if the article is already analized
#                 url = article_url.casefold().strip()
#                 existing_article = session_instance.query(
#                     AnalyzedArticle).filter(AnalyzedArticle.url == url).first()

#                 if not existing_article or not existing_article.is_analyzed:

#                     new_article = AnalyzedArticle(
#                         source=site_name,
#                         url=url,
#                         is_analyzed=False
#                     )

#                     session_instance.add(new_article)
#                     session_instance.commit()

#                     # proceed to make first verification
#                     is_title_in_db = title_in_db(
#                         article_title, session_instance)
#                     is_title_in_blacklist = title_in_blacklist(
#                         article_title, session_instance)
#                     is_url_in_db = url_in_db(url, session_instance)

#                     if not is_title_in_blacklist and not is_url_in_db and not is_title_in_db:

#                         if category_name == 'bitcoin' or category_name == 'ethereum':
#                             if any(keyword in article_title.lower() for keyword in keywords):
#                                 article_urls.add(url)
#                         else:
#                             article_urls.add(url)

#         return (article_urls, site_name), 200

#     except InternalError as e:
#         print('Internal error: ' + str(e))
#         return 'Internal error: ' + str(e), 500

#     except IllegalStateChangeError as e:
#         print('Illegal state change: ' + str(e))
#         return 'Illegal state change: ' + str(e), 500

#     except InvalidRequestError as e:
#         print('Invalid request: ' + str(e))
#         return 'Invalid request: ' + str(e), 400

#     except IntegrityError as e:
#         print(f'Integrity error: ' + str(e))
#         return f'Integrity error: ' + str(e), 400

#     except Exception as e:
#         print(f'An error occurred in scrape_sites ' + str(e))
#         return f'An error occurred in scrape_sites ' + str(e), 500


# def scrape_google_news_articles(article_urls, site_name, category_name, coin_bot_name, session):
#     counter_articles_saved = 0
#     for article_link in article_urls:
#         article_to_save = []

#         if site_name == 'Google News':
#             title, content, matched_keywords = validate_google_news_article(
#                 article_link, coin_bot_name, session)
#             if title and content:
#                 article_to_save.append(
#                     (title, content, article_link, site_name, matched_keywords))
#             else:
#                 continue

#             if not article_to_save:
#                 print(
#                     f"Article did not pass {site_name} validations in {category_name}")

#             for article_data in article_to_save:
#                 title, content, article_link, site_name, matched_keywords = article_data
#                 summary = summary_generator(content, category_name)
#                 if summary is not None:
#                     channel_mapping = {
#                         'btc': btc_slack_channel_id,
#                         'eth': eth_slack_channel_id,
#                         'hacks': hacks_slack_channel_id,
#                         'ldo': lsd_slack_channel_id,
#                         'rpl': lsd_slack_channel_id,
#                         'fxs': lsd_slack_channel_id,
#                         'atom': layer_0_slack_channel_id,
#                         'dot': layer_0_slack_channel_id,
#                         'qnt': layer_0_slack_channel_id,
#                         'ada': layer_1_lmc_slack_channel_id,
#                         'sol': layer_1_lmc_slack_channel_id,
#                         'avax': layer_1_lmc_slack_channel_id,
#                         'near': layer_1_mmc_slack_channel_id,
#                         'ftm': layer_1_mmc_slack_channel_id,
#                         'kas': layer_1_mmc_slack_channel_id,
#                         'matic': layer_2_slack_channel,
#                         'arb': layer_2_slack_channel,
#                         'op': layer_2_slack_channel,
#                         'link': oracles_slack_channel,
#                         'api3': oracles_slack_channel,
#                         'band': oracles_slack_channel,
#                         'xlm': cross_border_payment_slack_channel,
#                         'algo': cross_border_payment_slack_channel,
#                         'xrp': cross_border_payment_slack_channel,
#                         'dydx': defi_perpetual_slack_channel,
#                         'velo': defi_perpetual_slack_channel,
#                         'gmx': defi_perpetual_slack_channel,
#                         'uni': defi_slack_channel,
#                         'sushi': defi_slack_channel,
#                         'cake': defi_slack_channel,
#                         'aave': defi_others_slack_channel,
#                         'pendle': defi_others_slack_channel,
#                         '1inch': defi_others_slack_channel,
#                         'ocean': ai_slack_channel,
#                         'fet': ai_slack_channel,
#                         'rndr': ai_slack_channel,
#                     }

#                     channel_id = channel_mapping.get(coin_bot_name, None)
#                     image = generate_poster_prompt(summary)
#                     article_image = image[0] if image else 'No image'
#                     slack_image = image[1] if image else 'No image'

#                     matched_keywords = article_data[-1]

#                     # Format the list of matched keywords as a string
#                     matched_keywords_string = ', '.join(
#                         keyword[1] for keyword in matched_keywords) if matched_keywords else 'No keywords found.'

                   

#                     bot = session.query(CoinBot).filter(
#                         CoinBot.bot_name == coin_bot_name).first()
#                     site_source = session.query(Site).filter(
#                         Site.site_name == site_name, Site.coin_bot_id == bot.bot_id).first()
#                     coin_bot_id = site_source.coin_bot_id

#                     new_article = Article(
#                         title=title,
#                         summary=summary,
#                         date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                         url=article_link,
#                         coin_bot_id=coin_bot_id
#                     )

#                     session.add(new_article)
#                     session.commit()

#                     article_id = new_article.article_id
#                     image_filename = f"{article_id}.jpg"

                    
                        
#                     if image:
#                             try:
#                                 # Resize and upload the image to S3
#                                 resized_image_url = resize_and_upload_image_to_s3(image, 'apparticleimages', image_filename)

#                                 if resized_image_url:
#                                     print("Image resized and uploaded to S3 successfully.")
#                                 else:
#                                     print("Error resizing and uploading the image to S3.")
#                             except Exception as e:
#                                 print("Error:", e)
#                     else:
#                         print("Image not generated.")
                    
#                     counter_articles_saved += 1
#                     image_url=f'https://apparticleimages.s3.us-east-2.amazonaws.com/{image_filename}'
#                      #Send the message to Slack
#                     send_NEWS_message_to_slack(channel_id=channel_id,
#                                                 title=title,
#                                                 date_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                                                 url=article_link,
#                                                 summary=summary,
#                                                 image=image_url,
#                                                 category_name=category_name,
#                                                 extra_info=matched_keywords_string
#                                                 )

#                     # current_datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#                     new_used_keyword = Used_keywords(
#                         article_id=new_article.article_id,
#                         article_content=summary,
#                         article_date=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                         article_url=article_link,
#                         keywords=matched_keywords_string,
#                         source=article_link.split(".com")[0],
#                         coin_bot_id=coin_bot_id
#                     )

#                     session.add(new_used_keyword)
#                     session.commit()

#                     print(f'Iteration completed and saved for {title}')
#                     print(
#                         f'\nArticle: "{title}" has been added to the DB, Link: {article_link} from {site_name} in {category_name}.')
#                 else:
#                     print('------ THERE IS NO AN AVAILABLE SUMMARY -----')
#                     continue

#     # print('counter_articles_saved: ', counter_articles_saved)


# def scrape_articles(article_urls, site_name, category_name, coin_bot_name, session):
#     if category_name == 'bitcoin' or category_name == 'solana':
#         try:
#             counter_articles_saved = 0

#             for article_link in article_urls:

#                 article_to_save = []

#                 if site_name == 'Ambcrypto':
#                     title, content, valid_date, image_urls, matched_keywords = validate_ambcrypto_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Beincrypto':
#                     title, content, valid_date, image_urls, matched_keywords = validate_beincrypto_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Bitcoinist':
#                     title, content, valid_date, image_urls, matched_keywords = validate_bitcoinist_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Blockworks':
#                     title, content, valid_date, image_urls, matched_keywords = validate_blockworks_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Coincodex':
#                     title, content, valid_date, image_urls, matched_keywords = validate_coincodex_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Cointelegraph':
#                     title, content, valid_date, image_urls, matched_keywords = validate_cointelegraph_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Coingape':
#                     title, content, valid_date, image_urls, matched_keywords = validate_coingape_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Coindesk':
#                     title, content, valid_date, image_urls, matched_keywords = validate_coindesk_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Coinpedia':
#                     title, content, valid_date, image_urls, matched_keywords = validate_coinpedia_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Dailyhodl':
#                     title, content, valid_date, image_urls, matched_keywords = validate_dailyhodl_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Cryptodaily':
#                     title, content, valid_date, image_urls, matched_keywords = validate_cryptodaily_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Utoday':
#                     title, content, valid_date, image_urls, matched_keywords = validate_utoday_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Cryptonews':
#                     title, content, valid_date, image_urls, matched_keywords = validate_cryptonews_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Cryptopotato':
#                     title, content, valid_date, image_urls, matched_keywords = validate_cryptopotato_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Cryptoslate':
#                     title, content, valid_date, image_urls, matched_keywords = validate_cryptoslate_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Decrypt':
#                     title, content, valid_date, image_urls, matched_keywords = validate_decrypt_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Investing':
#                     title, content, valid_date, image_urls, matched_keywords = validate_investing_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if site_name == 'Theblock':
#                     title, content, valid_date, image_urls, matched_keywords = validate_theblock_article(
#                         article_link, coin_bot_name, session)
#                     if title and content and valid_date:
#                         article_to_save.append(
#                             (title, content, valid_date, article_link, site_name, image_urls, matched_keywords))
#                     else:
#                         continue

#                 if not article_to_save:
#                     print(
#                         f"Article did not passed {site_name} validations in {category_name}")

#                 for article_data in article_to_save:
#                     title, content, valid_date, article_link, site_name, image_urls, matched_keywords = article_data
#                     # images from the source
#                     image_urls_list = list(image_urls)

#                     summary = summary_generator(content, category_name)

#                     channel_mapping = {
#                         'btc': btc_slack_channel_id,
#                         'eth': eth_slack_channel_id,
#                         'hacks': hacks_slack_channel_id,
#                         'ldo': lsd_slack_channel_id,
#                         'rpl': lsd_slack_channel_id,
#                         'fxs': lsd_slack_channel_id,
#                         'atom': layer_0_slack_channel_id,
#                         'dot': layer_0_slack_channel_id,
#                         'qnt': layer_0_slack_channel_id,
#                         'ada': layer_1_lmc_slack_channel_id,
#                         'sol': layer_1_lmc_slack_channel_id,
#                         'avax': layer_1_lmc_slack_channel_id,
#                         'near': layer_1_mmc_slack_channel_id,
#                         'ftm': layer_1_mmc_slack_channel_id,
#                         'kas': layer_1_mmc_slack_channel_id,
#                         'matic': layer_2_slack_channel,
#                         'arb': layer_2_slack_channel,
#                         'op': layer_2_slack_channel,
#                         'link': oracles_slack_channel,
#                         'api3': oracles_slack_channel,
#                         'band': oracles_slack_channel,
#                         'xlm': cross_border_payment_slack_channel,
#                         'algo': cross_border_payment_slack_channel,
#                         'xrp': cross_border_payment_slack_channel,
#                         'dydx': defi_perpetual_slack_channel,
#                         'velo': defi_perpetual_slack_channel,
#                         'gmx': defi_perpetual_slack_channel,
#                         'uni': defi_slack_channel,
#                         'sushi': defi_slack_channel,
#                         'cake': defi_slack_channel,
#                         'aave': defi_others_slack_channel,
#                         'pendle': defi_others_slack_channel,
#                         '1inch': defi_others_slack_channel,
#                         'ocean': ai_slack_channel,
#                         'fet': ai_slack_channel,
#                         'rndr': ai_slack_channel,
#                     }

#                     channel_id = channel_mapping.get(coin_bot_name, None)

#                     if summary:
#                         image = generate_poster_prompt(summary)
#                         article_image = image[0] if image else 'No image'
#                         slack_image = image[1] if image else 'No image'

#                         matched_keywords = article_data[-1]

#                         # Format the list of matched keywords as a string
#                         matched_keywords_string = ', '.join(
#                             keyword[1] for keyword in matched_keywords) if matched_keywords else 'No keywords found.'

                        

#                         # if category_name == 'bitcoin':
#                         #     response, status = send_tweets_to_twitter(content=summary,
#                         #                                             title=title)

#                         #     if status == 200:
#                         #         send_INFO_message_to_slack_channel(channel_id=channel_id,
#                         #                                         title_message="New Notification from AI Alpha",
#                         #                                         sub_title="Response",
#                         #                                         message=response
#                         #                                         )

#                         bot = session.query(CoinBot).filter(
#                             CoinBot.bot_name == coin_bot_name).first()
#                         site_source = session.query(Site).filter(
#                             Site.site_name == site_name, Site.coin_bot_id == bot.bot_id).first()
#                         coin_bot_id = site_source.coin_bot_id

#                         new_article = Article(
#                             title=title,
#                             summary=summary,
#                             date=valid_date,
#                             url=article_link,
#                             coin_bot_id=coin_bot_id
#                         )

#                         session.add(new_article)
#                         session.commit()
                        
#                         article_id = new_article.article_id
#                         image_filename = f"{article_id}.jpg"
                        
#                         if image:
#                             try:
#                                 # Resize and upload the image to S3
#                                 resized_image_url = resize_and_upload_image_to_s3(image, 'apparticleimages', image_filename)

#                                 if resized_image_url:
#                                     print("Image resized and uploaded to S3 successfully.")
#                                 else:
#                                     print("Error resizing and uploading the image to S3.")
#                             except Exception as e:
#                                 print("Error:", e)
#                         else:
#                             print("Image not generated.")
                            
#                         counter_articles_saved += 1
#                         image_url=f'https://apparticleimages.s3.us-east-2.amazonaws.com/{image_filename}'
                        
#                         #Send the message to Slack
#                         send_NEWS_message_to_slack(channel_id=channel_id,
#                                                     title=title,
#                                                     date_time=datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
#                                                     url=article_link,
#                                                     summary=summary,
#                                                     image=image_url,
#                                                     category_name=category_name,
#                                                     extra_info=matched_keywords_string
#                                                     )

#                         # current_datetime_str = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')

#                         new_used_keyword = Used_keywords(
#                             article_id=new_article.article_id,
#                             article_content=summary,
#                             article_date=valid_date,
#                             article_url=article_link,
#                             keywords=matched_keywords_string,
#                             source=article_link.split(".com")[0],
#                             coin_bot_id=coin_bot_id
#                         )

#                         session.add(new_used_keyword)
#                         session.commit()
#                         print('Keywords saved')

#                         print(
#                             f'\nArticle: "{title}" has been added to the DB, Link: {article_link} from {site_name} in {category_name}.')
#                     else:
#                         print('------ THERE IS NO AN AVAILABLE SUMMARY -----')
#                         continue

#             print(
#                 f'\n--- {len(article_urls)} article were analized for {site_name} and {counter_articles_saved} were SAVED\n ---')
#             return list(article_urls), 200

#         except Exception as e:
#             print(f'Error scraping the article link in {site_name}: {str(e)}')
#             return f'Error scraping the article link in {site_name}: {str(e)}', 500
#     else:
#         scrape_google_news_articles(article_urls, site_name, category_name, coin_bot_name, session)
#         return list(article_urls), 200


# def start_periodic_scraping(category_name):
#     with Session() as session:
#         category = session.query(Category).filter(
#             Category.category == category_name).first()

#         if category:
#             category_id = category.category_id

#             # Using joinedload to eager load the associated coin_bots and sites
#             category_with_coin_bots = (
#                 session.query(Category)
#                 .options(joinedload(Category.coin_bot).joinedload(CoinBot.sites))
#                 .filter_by(category_id=category_id)
#                 .first()
#             )

#             if category_with_coin_bots:
#                 coin_bots = category_with_coin_bots.coin_bot
#                 for coin_bot in coin_bots:
#                     bot_id = coin_bot.bot_id
#                     coin_bot_name = coin_bot.bot_name

#                     # Fetch the sites associated with the current bot_id
#                     sites = session.query(Site).filter(
#                         Site.coin_bot_id == bot_id).all()

#                     for site in sites:
#                         site_name = site.site_name
#                         data_source_url = site.data_source_url
#                         base_url = site.base_url
#                         main_container = site.main_container

#                         result, status = scrape_sites(site_name=site_name,
#                                                       data_source_url=data_source_url,
#                                                       base_url=base_url,
#                                                       category_name=category_name,
#                                                       main_container=main_container,
#                                                       session_instance=session
#                                                       )

#                         if status == 200:
#                             article_urls, site_name = result
#                             print(f'--- {len(article_urls)} ARTICLES TO ANALYZE FOR {site_name} --- \n',
#                                   'Truncated data...' if len(article_urls) > 20 else article_urls)
#                             result, status = scrape_articles(article_urls=article_urls,
#                                                              site_name=site_name,
#                                                              category_name=category_name,
#                                                              coin_bot_name=coin_bot_name,
#                                                              session=session
#                                                              )
#                             if status != 200:
#                                 continue
#                         else:
#                             continue

#                     print(f'All {coin_bot_name} sites scrapped')

#                 return f'All {category_name.capitalize()} sites were analized', 200

#             else:
#                 print(f"No coin bots found for category: {category_name}")
#                 return f"No coin bots found for category: {category_name}", 204
#         else:
#             print(f"No category found with name: {category_name}")
#             return f"No category found with name: {category_name}", 404


# # get_google_news_links(site="https://news.google.com/search?q=fetch%20ai%20when%3A1d&hl=en-US&gl=US&ceid=US%3Aen", main_container="None")
