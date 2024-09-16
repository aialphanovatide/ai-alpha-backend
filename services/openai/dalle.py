# Image generator Class using DALL-E 

import os
from typing import Optional
from openai import OpenAI
from dotenv import load_dotenv
from routes.slack.templates.news_message import send_INFO_message_to_slack_channel

load_dotenv()

class ImageGenerator:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ImageGenerator with the OpenAI API key.

        Args:
            api_key (Optional[str]): The OpenAI API key. If not provided, it will be fetched from environment variables.

        Raises:
            ValueError: If the API key is not provided and not found in environment variables.

        Attributes:
            client (OpenAI): An instance of the OpenAI client.
            headers (dict): HTTP headers for API requests, including Content-Type and Authorization.
        """
        api_key = api_key or os.getenv('NEWS_BOT_API_KEY')
        if not api_key:
            raise ValueError("OpenAI API key is not provided or not found in the environment variables.")
        
        self.client = OpenAI(api_key=api_key)


    def generate_image(self, article: str, size: str = "1024x1024") -> str:
        """
        Generate an image based on the given article using DALL-E.

        This method performs the following steps:
        1. Generates a DALL-E prompt using GPT-4 based on the input article.
        2. Uses the generated prompt to create an image with DALL-E.

        Args:
            article (str): The article text to base the image on.
            size (str, optional): The size of the generated image. Default is "1024x1024".

        Returns:
            str: The URL of the generated image.

        Raises:
            Exception: If there's an error during the image generation process.

        Note:
            The method uses GPT-4 to create a prompt that is abstract and avoids specific names,
            letters, numbers, or words. The final image is generated in an anime style.
        """
        try:
            # Generate DALL-E prompt using GPT-4
            gpt_prompt = f'Generate a DALL-E prompt related to this {article}. It should be 400 characters or less and avoid specific names focused on abstract image without mention letters, numbers or words.'
            
            gpt_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": gpt_prompt},
                    {"role": "user", "content": gpt_prompt}
                ],
                temperature=0.6,
                max_tokens=1024,
            )
            final_prompt = gpt_response.choices[0].message.content[:450]

            # Generate image using DALL-E
            dalle_prompt = f'{final_prompt} - depicting an anime style.'
            
            dalle_response = self.client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                n=1,
                size=size
            )
            image_url = dalle_response.data[0].url
            return image_url
        
        except Exception as e:
            raise Exception(f"Error generating image: {str(e)}")
            


# Example usage
# if __name__ == "__main__":
#     image_generator = ImageGenerator()
#     article = """
#     Bitcoin successfully tests weekly key support at $58,000, despite a sudden crash on August 27.
#     A weekly close above $58,447.12 could confirm Bitcoin's return to an important price channel, potentially reaching $60,500-$61,500 in the short term.
#     • The crash served as an opportunity for Bitcoin to test the resistance of its previous downtrend channel as support on the daily timeframe.
#     • A successful retest of daily support would confirm the breakout and precede upside continuation, which has already occurred.
#     • Bitcoin may fill a new CME gap between $60,500 and $61,500, as it has filled every gap in the past six months.
#     • The sudden crash was not related to any major development in crypto or the macroeconomy, but rather a regular movement after Bitcoin got rejected at the $62,000 resistance.
#     • The crash resulted in $110 million in liquidations within an hour and $127 million in outflows from US spot Bitcoin ETFs, with ARK 21Shares' ARKB experiencing the most negative flows.
#     """
#     image_url = image_generator.generate_image(article)
#     print(f"Generated image URL: {image_url}")
        