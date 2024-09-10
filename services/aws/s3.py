import os
import boto3
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from typing import Tuple, Optional
from botocore.exceptions import BotoCoreError, ClientError
from requests.exceptions import RequestException

load_dotenv()


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
        self.aws_access_key = aws_access_key or os.getenv('AWS_ACCESS')
        self.aws_secret_key = aws_secret_key or os.getenv('AWS_SECRET_KEY')

        if not self.aws_access_key or not self.aws_secret_key:
            raise ValueError("AWS access key and secret key must be provided.")

        self.s3_client = boto3.client(
            's3',
            region_name=self.aws_region,
            aws_access_key_id=self.aws_access_key,
            aws_secret_access_key=self.aws_secret_key
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
            print(f"Error fetching image from {image_url}: {str(e)}")
        except IOError as e:
            print(f"Error processing image: {str(e)}")
        except (BotoCoreError, ClientError) as e:
            print(f"Error uploading to S3: {str(e)}")
        except Exception as e:
            print(f"Unexpected error: {str(e)}")
        return None



# Usage Example:
# if __name__ == "__main__":
#     image_processor = ImageProcessor()
#     image_url = "https://cdn.pixabay.com/photo/2024/05/26/10/15/bird-8788491_1280.jpg"
#     bucket_name = "aialphaicons"
#     image_filename = "test_image.jpg"
#     target_size = (256, 256)

#     uploaded_url = image_processor.process_and_upload_image(image_url, bucket_name, image_filename, target_size)
#     print(f"Uploaded image URL: {uploaded_url}")

