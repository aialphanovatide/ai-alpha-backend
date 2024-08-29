import logging
from typing import Tuple, Optional
import requests
from PIL import Image
from io import BytesIO
import boto3
import os
from dotenv import load_dotenv
from botocore.exceptions import BotoCoreError, ClientError
from requests.exceptions import RequestException

logger = logging.getLogger(__name__)
load_dotenv()

AWS_ACCESS = os.getenv('AWS_ACCESS')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY')

class ImageProcessor:
    def __init__(self, 
                 aws_region: str = 'us-east-2',
                 aws_access_key: Optional[str] = None,
                 aws_secret_key: Optional[str] = None):
        """
        Resize and upload to an AWS S3 Bucket

        Args:
            aws_region (str): AWS region for S3. Default is 'us-east-2'.
            aws_access_key (Optional[str]): AWS access key. If None, will use environment variables or IAM role.
            aws_secret_key (Optional[str]): AWS secret key. If None, will use environment variables or IAM role.
        """
        self.aws_region = aws_region
        self.s3_client = boto3.client(
            's3',
            region_name=aws_region,
            aws_access_key_id=aws_access_key,
            aws_secret_access_key=aws_secret_key
        )

    def fetch_image(self, image_url: str) -> bytes:
        """
        Fetch an image from a URL.

        Args:
            image_url (str): URL of the image to fetch.

        Returns:
            bytes: The image content.

        Raises:
            RequestException: If there's an error fetching the image.
        """
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        return response.content

    def resize_image(self, image_content: bytes, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize an image.

        Args:
            image_content (bytes): The image content.
            target_size (Tuple[int, int]): Desired size for the resized image.

        Returns:
            Image.Image: The resized image.

        Raises:
            IOError: If there's an error processing the image.
        """
        with Image.open(BytesIO(image_content)) as image:
            return image.resize(target_size, Image.LANCZOS)

    def upload_to_s3(self, image: Image.Image, bucket_name: str, image_filename: str) -> str:
        """
        Upload an image to S3.

        Args:
            image (Image.Image): The image to upload.
            bucket_name (str): Name of the S3 bucket.
            image_filename (str): Desired filename for the image in S3.

        Returns:
            str: URL of the uploaded image in S3.

        Raises:
            BotoCoreError, ClientError: If there's an error interacting with S3.
        """
        with BytesIO() as output:
            image.save(output, format="JPEG", quality=85, optimize=True)
            output.seek(0)
            self.s3_client.upload_fileobj(
                output, 
                bucket_name, 
                image_filename,
                ExtraArgs={'ContentType': 'image/jpeg'}
            )
        return f"https://{bucket_name}.s3.{self.aws_region}.amazonaws.com/{image_filename}"

    def process_and_upload_image(self, 
                                 image_url: str, 
                                 bucket_name: str, 
                                 image_filename: str, 
                                 target_size: Tuple[int, int] = (1024, 1024)) -> Optional[str]:
        """
        Fetch, resize, and upload an image to S3.

        Args:
            image_url (str): URL of the image to be processed and uploaded.
            bucket_name (str): Name of the S3 bucket.
            image_filename (str): Desired filename for the image in S3.
            target_size (Tuple[int, int]): Desired size for the resized image. Default is (256, 256).

        Returns:
            Optional[str]: URL of the uploaded image in S3, or None if an error occurred.
        """
        try:
            image_content = self.fetch_image(image_url)
            resized_image = self.resize_image(image_content, target_size)
            return self.upload_to_s3(resized_image, bucket_name, image_filename)
        except RequestException as e:
            logger.error(f"Error fetching image from {image_url}: {str(e)}")
        except IOError as e:
            logger.error(f"Error processing image: {str(e)}")
        except (BotoCoreError, ClientError) as e:
            logger.error(f"Error uploading to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
        return None



# Initialize the ImageProcessor
image = ImageProcessor(aws_access_key="YOUR_ACCESS_KEY", aws_secret_key="YOUR_SECRET_KEY")

# Use the processor
# image_url = "https://example.com/image.jpg"
# bucket_name = "my-bucket"
# image_filename = "resized_image.jpg"

# result_url = image.process_and_upload_image(image_url, bucket_name, image_filename)

# if result_url:
#     print(f"Image uploaded successfully. URL: {result_url}")
# else:
#     print("Failed to upload image.")