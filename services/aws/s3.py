import os
import boto3
import requests
from PIL import Image
from io import BytesIO
from dotenv import load_dotenv
from typing import Tuple, Optional
from urllib.parse import urlparse, unquote
from botocore.exceptions import ClientError
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

        This method sends a GET request to the specified URL to retrieve the image content.
        It uses a timeout of 10 seconds to prevent hanging on slow connections.

        Args:
            image_url (str): URL of the image to fetch.

        Returns:
            bytes: The raw image content.

        Raises:
            RequestException: If there's an error fetching the image, such as network issues,
                              invalid URLs, or server errors.

        Note:
            This method does not validate the content type of the response. It's the caller's
            responsibility to ensure that the URL points to a valid image resource.
        """
        try:
            response = requests.get(image_url, timeout=10)
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

    def delete_from_s3(self, image_url: str) -> None:
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
            parsed_url = urlparse(image_url)
            bucket_name = parsed_url.netloc.split('.')[0]
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

    def process_and_upload_image(self, 
                                 image_url: str, 
                                 bucket_name: str, 
                                 image_filename: str, 
                                 target_size: Tuple[int, int] = (1024, 1024)) -> Optional[str]:
        """
        Fetch, resize, and upload an image to S3.

        This method performs the following steps:
        1. Fetches the image from the provided URL.
        2. Resizes the image to the specified target size.
        3. Uploads the resized image to the specified S3 bucket.

        Args:
            image_url (str): URL of the image to be processed and uploaded.
            bucket_name (str): Name of the S3 bucket where the image will be uploaded.
            image_filename (str): Desired filename for the image in S3.
            target_size (Tuple[int, int], optional): Desired size for the resized image. 
                                                     Default is (1024, 1024).

        Returns:
            Optional[str]: URL of the uploaded image in S3 if successful, None otherwise.

        Raises:
            RequestException: If there's an error fetching the image from the URL.
            IOError: If there's an error processing (resizing) the image.
            BotoCoreError: If there's an error interacting with AWS S3.
            Exception: For any other unexpected errors.
        """
        try:
            image_content = self.fetch_image(image_url)
            resized_image = self.resize_image(image_content, target_size)
            return self.upload_to_s3(resized_image, bucket_name, image_filename)
        except Exception as e:
            raise Exception(str(e))



# Usage Example:
# if __name__ == "__main__":
#     image_processor = ImageProcessor()
#     image_url = "https://cdn.pixabay.com/photo/2024/05/26/10/15/bird-8788491_1280.jpg"
#     bucket_name = "aialphaicons"
#     image_filename = "test_image.jpg"
#     target_size = (256, 256)

#     uploaded_url = image_processor.process_and_upload_image(image_url, bucket_name, image_filename, target_size)
#     print(f"Uploaded image URL: {uploaded_url}")


image_processor = ImageProcessor()
image_processor.delete_from_s3("https://aialphaicons.s3.us-east-2.amazonaws.com/algorand-api-convincing-enough?.jpg")