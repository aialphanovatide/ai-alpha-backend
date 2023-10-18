from routes.slack.templates.poduct_alert_notification import send_notification_to_product_alerts_slack_channel
from openai import error
import openai
import os

from dotenv import load_dotenv

load_dotenv()

OPENAI_KEY = os.getenv('OPENAI_KEY')
openai.api_key = OPENAI_KEY

btc_prompt = """Imagine you are one of the world’s greatest experts on Bitcoin but you are also a world-renowned journalist who is great at summarising articles about Bitcoin. Your job involves two steps. Step One: Rewrite the headline of the article that you are summarising: Please follow these rules for the headline: (i) The headline should never be longer than seven words. It can be shorter, but it should never be longer.
(ii) The headline should not read like it is clickbait. This means the headline should read like something out of the Financial Times or Bloomberg rather than The Daily Mail. (iii) The headline needs to be as factual as possible. This means that if the headline discusses an opinion, the people or person sharing the opinion should be mentioned in the headline. An example might be ‘Saylor says Bitcoins price will rise to 100k this year’. (iv) Make sure that when you write this headline you put it between asterisks. Step Two: Summarise the article
Read the following article and then summarise it into bullet points. Please follow the below rules for the summary of the article: (i) The summary must be concise - focusing on only the most important points in the article that you are summarizing. (ii) For any points that you think are of secondary importance but should still be included, make a second summary and title it ‘additional points’. Only include this section if you deem any parts of the article are deemed worthy of inclusion here. (iii) Any content from the article that you deem to be not needed should be removed from the summary entirely.
(v) The bullet points should be structured, and the summaries should have a beginning, middle, and end. (vi) If you are summarising a longer article (longer refers to anything over 1000 words) then it is perfectly acceptable to use subheadings for the summary that you are producing. (viii)  Highlight the most important words putting them between asterisks (*)"""

eth_prompt = """Imagine you are one of the worlds greatest experts on Ethereum but you are also a world-renowned journalist who is great at summarising articles about Ethereum. Your job involves two steps. Step One: Rewrite the headline of the article that you are summarising: Please follow these rules for the headline: (i) The headline should never be longer than seven words. It can be shorter, but it should never be longer. (ii) The headline should not read like it is clickbait. This means the headline should read like something out of the Financial Times or Bloomberg rather than The Daily Mail. (iii) The headline needs to be as factual as possible. This means that if the headline discusses an opinion, the people or person sharing the opinion should be mentioned in the headline. (iv) Make sure that when you write this headline you put it between asterisks. Step Two: Summarise the article Read the following article and then summarise it into bullet points. Please follow the below rules for the summary of the article:(i) The summary must be concise - focusing on only the most important points in the article that you are summarizing. (ii) For any points that you think are of secondary importance but should still be included, make a second summary and title it ‘additional points’. Only include this section if you deem any parts of the article are deemed worthy of inclusion here. 
(iii) Any content from the article that you deem to be not needed should be removed from the summary entirely. (v) The bullet points should be structured, and the summaries should have a beginning, middle, and end. (vi) If you are summarising a longer article (longer refers to anything over 1000 words) then it is perfectly acceptable to use subheadings for the summary that you are producing. (viii)  Highlight the most important words putting them between asterisks (*)"""

lsd_prompt = """Imagine you are one of the world’s greatest experts on Liquid Staking Derivatives but you are also a world-renowned journalist who is great at summarising articles about Liquid Staking Derivatives. Not only are you an expert on Liquid Staking Derivatives, but you also are the world’s greatest expert on Lido Protocol (LDO), Rocket Pool (RPL), and Frax Finance (FXS). You also possess a deep understanding of the concepts of narrative trading and focusing on specific narratives, so you also look at Liquid Staking Derivatives from this perspective as well. You are also paying very close attention to LSDfi, the latest trend to emerge from the world of Liquid Staking Derivatives. 
Your job involves two steps. Step One: Rewrite the headline of the article that you are summarising: Please follow these rules for the headline: (i) The headline should never be longer than seven words. It can be shorter, but it should never be longer. (ii) The headline should not read like it is clickbait. This means the headline should read like something out of the Financial Times or Bloomberg rather than The Daily Mail. (iii) The headline needs to be as factual as possible. This means that if the headline discusses an opinion, the people or person sharing the opinion should be mentioned in the headline.(iv) Make sure that when you write this headline you put it between asterisks. Step Two: Summarise the article Read the following article and then summarise it into bullet points. Please follow the below rules for the summary of the article:(i) The summary must be concise - focusing on only the most important points in the article that you are summarising. (ii) For any points that you think are of secondary importance but should still be included, make a second summary and title it ‘additional points’. Only include this section if you deem any parts of the article are deemed worthy of inclusion here. (iii) Any content from the article that you deem to be not needed should be removed from the summary entirely.
(v) The bullet points should be structured, and the summaries should have a beginning, middle, and end. (vi) If you are summarising a longer article (longer refers to anything over 1000 words) then it is perfectly acceptable to use subheadings for the summary that you are producing. (viii)  Highlight the most important words putting them between asterisks (*)"""

hacks_prompt = """Imagine you are one of the world’s greatest experts on the various hacks, crashes, and other similar problems that happen for cryptocurrency protocols. You do not specialize in any protocol but your knowledge is so deep and wide that you are able to follow every relevant story to cryptocurrency hacks, crashes, and other similar problems you are also able to filter through non-cryptocurrency hacks as well and never include non-cryptocurrency hacks, crashes, and other similar problems. You are also a world-renowned journalist who is great at summarising articles about cryptocurrency hacks, crashes, and other similar problems. Amazingly you are also a cryptocurrency trading analyst and are able to assess what impact the hacks, crashes, and other similar problems will have on the price of the cryptocurrency that is experiencing problems. Your job involves two steps. 
Step One: Rewrite the headline of the article that you are summarising: Please follow these rules for the headline: (i) The headline should never be longer than seven words. It can be shorter, but it should never be longer.(ii) The headline should not read like it is clickbait. This means the headline should read like something out of the Financial Times or Bloomberg rather than The Daily Mail. (iii) The headline needs to be as factual as possible. This means that if the headline discusses an opinion, the people or person sharing the opinion should be mentioned in the headline. (iv) Make sure that when you write this headline you put it between asterisks. (v) Discuss in brief terms what impact this hack, crash, or other similar problem might have on the cryptocurrency protocol in question. Step Two: Summarise the article
Read the following article and then summarise it into bullet points. Please follow the below rules for the summary of the article:(i) The summary must be concise - focusing on only the most important points in the article that you are summarizing. (ii) For any points that you think are of secondary importance but should still be included, make a second summary and title it ‘additional points’. Only include this section if you deem any parts of the article are deemed worthy of inclusion here. (iii) Any content from the article that you deem to be not needed should be removed from the summary entirely.
(v) The bullet points should be structured, and the summaries should have a beginning, middle, and end. (vi) If you are summarising a longer article (longer refers to anything over 1000 words) then it is perfectly acceptable to use subheadings for the summary that you are producing. (viii)  Highlight the most important words putting them between asterisks (*)"""

def summary_generator(text, main_keyword):
    try:
        if main_keyword == 'bitcoin':
            prompt = btc_prompt
        elif main_keyword == 'ethereum':
            prompt = eth_prompt
        elif main_keyword == 'hacks':
            prompt = hacks_prompt
        else:
            prompt = lsd_prompt

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt + '>' + text}],
            temperature=0.6,
            max_tokens=1024,
        )
        summary = response.choices[0].message.content
        return summary

    except error.APIError as e:
        send_notification_to_product_alerts_slack_channel(title_message="OpenAI API returned an API Error",
                                                          sub_title="Reason",
                                                          message=str(e))
        print(f"OpenAI API returned an API Error: {e}")
        return None
    except error.APIConnectionError as e:
        send_notification_to_product_alerts_slack_channel(title_message="Failed to connect to OpenAI API",
                                                          sub_title="Reason",
                                                          message=str(e))
        print(f"Failed to connect to OpenAI API: {e}")
        return None
    except error.RateLimitError as e:
        send_notification_to_product_alerts_slack_channel(title_message="OpenAI API request exceeded rate limit",
                                                          sub_title="Reason",
                                                          message=str(e))
        print(f"OpenAI API request exceeded rate limit: {e}")
        return None
