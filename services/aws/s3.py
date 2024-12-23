import os
import boto3
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from urllib.parse import urlparse
from typing import Tuple, Optional
from requests.exceptions import RequestException
from botocore.exceptions import ClientError, BotoCoreError
import werkzeug

load_dotenv()

import os
import boto3
from typing import Optional

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
            bytes: The raw image content.

        Raises:
            RequestException: If there's an error fetching the image.
        """
        try:
            # Check if it's a DALL-E URL
            if "oaidalleapiprodscus.blob.core.windows.net" in image_url:
                # Use OpenAI client to regenerate the image
                from services.openai.dalle import ImageGenerator
                image_generator = ImageGenerator()
                new_url = image_generator.generate_image(
                    "Regenerate the previous image",
                    size="1024x1024"
                )
                # Use the new URL
                image_url = new_url

            # Add headers for better compatibility
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(image_url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.content
        except RequestException as e:
            raise RequestException(f"Error fetching image: {e}")

    def resize_image(self, image_content: bytes, target_size: Tuple[int, int]) -> Image.Image:
        """
        Resize an image to the specified target size.

        This method takes the raw image content as bytes and resizes it to the specified dimensions
        using the high-quality LANCZOS resampling filter.

        Args:
            image_content (bytes): The raw image content in bytes.
            target_size (Tuple[int, int]): The desired width and height of the resized image.

        Returns:
            Image.Image: A PIL Image object representing the resized image.

        Raises:
            IOError: If there's an error opening or processing the image.
            ValueError: If the input image_content is invalid or corrupted.

        Note:
            The LANCZOS filter is used for high-quality downsampling, which may be slower
            but produces better results, especially for significant size reductions.
        """
        try:
            with Image.open(BytesIO(image_content)) as image:
                return image.resize(target_size, Image.LANCZOS)
        except IOError as e:
            raise IOError(f"Error opening or processing the image: {e}")
        except ValueError as e:
            raise ValueError(f"Invalid or corrupted image data: {e}")

    def delete_from_s3(self, bucket: str, image_url: str) -> None:
        """
        Delete an image from S3.

        This method parses the provided S3 URL to extract the bucket name and image key,
        then attempts to delete the corresponding object from the S3 bucket.

        Args:
            image_url (str): URL of the image to delete from S3.

        Raises:
            ValueError: If the provided URL is not a valid S3 URL format.
            BotoCoreError: If there's a low-level error interacting with S3.
            ClientError: If there's a client-side error interacting with S3.
            Exception: For any other unexpected errors during the deletion process.

        Note:
            This method doesn't return any value. It either succeeds silently or raises an exception.
        """
        try:
            # Extract the bucket name and image key from the URL
            bucket_name = bucket
            image_key = str(image_url).split('/')[-1]

            if not bucket_name or not image_key:
                raise ValueError("Invalid S3 URL format")

            # Delete the object
            self.s3_client.delete_object(Bucket=bucket_name, Key=image_key)

        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == 'AccessDenied':
                raise PermissionError(f"Access denied when deleting from S3: {str(e)}")
            else:
                raise IOError(f"S3 client error: {str(e)}")
        except Exception as e:
            raise Exception(f"Unexpected error deleting from S3: {str(e)}")

    def upload_to_s3(self, image: Image.Image, bucket_name: str, image_filename: str) -> str:
        """
        Upload an image to S3.

        This method converts the given image to JPEG format, optimizes it, and uploads it to the specified S3 bucket.

        Args:
            image (Image.Image): The PIL Image object to upload.
            bucket_name (str): Name of the S3 bucket where the image will be stored.
            image_filename (str): Desired filename for the image in S3, including extension.

        Returns:
            str: URL of the uploaded image in S3.

        Raises:
            BotoCoreError: If there's a low-level error interacting with S3.
            ClientError: If there's a client-side error interacting with S3.
            Exception: For any other unexpected errors during the upload process.

        Note:
            The image is saved as JPEG with 85% quality and optimization enabled.
            The content type of the uploaded file is set to 'image/jpeg'.
        """
        try:
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
        except Exception as e:
            raise Exception(f"Unexpected error uploading to S3: {e}")
    
    def upload_svg_to_s3(self, svg_file, bucket_name: str, svg_filename: str) -> Optional[str]:
        print(self,bucket_name, svg_file,svg_filename)
        """
        Upload an SVG file to S3.
        Args:
            svg_file (Union[bytes, IO[bytes]]): The SVG file to upload.
            bucket_name (str): Name of the S3 bucket.
            svg_filename (str): Desired filename for the SVG in S3.
        Returns:
            Optional[str]: URL of the uploaded SVG in S3, or None if upload failed.
        """
        if svg_file and svg_filename.lower().endswith('.svg'):
            try:
                if hasattr(svg_file, 'read'):
                    # svg_file is a file-like object
                    self.s3_client.upload_fileobj(
                        svg_file,
                        bucket_name,
                        svg_filename,
                        ExtraArgs={'ContentType': 'image/svg+xml'}
                    )
                else:
                    # svg_file is bytes
                    self.s3_client.upload_bytes(
                        svg_file,
                        bucket_name,
                        svg_filename,
                        ExtraArgs={'ContentType': 'image/svg+xml'}
                    )
                return f"https://{bucket_name}.s3.{self.aws_region}.amazonaws.com/{svg_filename}"
            except (BotoCoreError, ClientError) as e:
                return None
        return None

    def process_and_upload_image(self, 
                                 image_url: str, 
                                 bucket_name: str, 
                                 image_filename: str, 
                                 target_size: Tuple[int, int] = (1024, 1024)) -> Optional[str]:
        """
        Fetch, resize, and upload an image to S3.
        """
        max_retries = 3
        retry_count = 0
        
        while retry_count < max_retries:
            try:
                # Intenta obtener la imagen
                image_content = self.fetch_image(image_url)
                
                # Procesa y redimensiona la imagen
                resized_image = self.resize_image(image_content, target_size)
                
                # Sube la imagen a S3
                return self.upload_to_s3(resized_image, bucket_name, image_filename)
                
            except RequestException as e:
                retry_count += 1
                if retry_count == max_retries:
                    raise Exception(f"Failed to fetch image after {max_retries} attempts: {e}")
                continue
                
            except Exception as e:
                raise Exception(f"Unexpected error processing and uploading image: {e}")
    

# Usage Example:
# if __name__ == "__main__":
#     image_processor = ImageProcessor()
#     image_url = "https://cdn.pixabay.com/photo/2024/05/26/10/15/bird-8788491_1280.jpg"
#     bucket_name = "aialphaicons"
#     image_filename = "test_image.jpg"
#     target_size = (256, 256)

#     uploaded_url = image_processor.process_and_upload_image(image_url, bucket_name, image_filename, target_size)
#     print(f"Uploaded image URL: {uploaded_url}")


# image_processor = ImageProcessor()
# image_processor.delete_from_s3("https://aialphaicons.s3.us-east-2.amazonaws.com/algorand-api-convincing-enough?.jpg")