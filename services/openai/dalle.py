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
        """
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OpenAI API key is not provided or not found in the environment variables.")
        
        try:
            self.client = OpenAI(api_key=self.api_key)
            # Verificar la conexión
            self.client.models.list()
        except Exception as e:
            raise ValueError(f"Failed to initialize OpenAI client: {str(e)}")

    def generate_image(self, article: str, size: str = "1024x1024") -> str:
        """
        Generate an image based on the given article using DALL-E.
        """
        try:
            gpt_prompt = (
                "Generate a DALL-E prompt related to this article. "
                "Create an abstract, artistic description without specific names, "
                "letters, numbers, or words. Maximum 400 characters:"
            )
            
            gpt_response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a creative prompt engineer."},
                    {"role": "user", "content": f"{gpt_prompt}\n\nArticle: {article}"}
                ],
                temperature=0.7,
                max_tokens=150,
            )
            
            final_prompt = gpt_response.choices[0].message.content.strip()[:400]

            dalle_prompt = f"{final_prompt} - in an artistic, abstract anime style"
            
            dalle_response = self.client.images.generate(
                model="dall-e-3",
                prompt=dalle_prompt,
                n=1,
                size=size,
                quality="standard",
                style="vivid"
            )
            
            image_url = dalle_response.data[0].url            
            return image_url
        
        except Exception as e:
            error_msg = f"Error generating image: {str(e)}"
            send_INFO_message_to_slack_channel(error_msg)
            raise Exception(error_msg)


        