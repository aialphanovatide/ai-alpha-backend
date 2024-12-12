from typing import Optional
import requests
import io
from PIL import Image
import svgwrite
import base64

def convert_png_to_svg(png_url: str) -> Optional[str]:
    """
    Convert a PNG image to an SVG representation.

    Args:
        png_url (str): URL of the PNG image

    Returns:
        Optional[str]: Base64 encoded SVG string or None if conversion fails
    """
    try:
        # Download the PNG image
        response = requests.get(png_url, timeout=10)
        response.raise_for_status()
        
        # Open the image
        img = Image.open(io.BytesIO(response.content))
        width, height = img.size
        
        # Create an SVG drawing
        dwg = svgwrite.Drawing('temp.svg', size=(width, height))
        
        # Convert image to base64
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        # Create an image element in the SVG
        img_element = dwg.image(
            f'data:image/png;base64,{img_str}', 
            insert=(0, 0), 
            size=(width, height)
        )
        dwg.add(img_element)
        
        # Convert to string
        svg_string = dwg.tostring()
        
        return svg_string

    except Exception as e:
        print(f"Error converting PNG to SVG: {e}")
        return None

def get_icon_as_svg(coin_id: str, icon_urls: dict) -> Optional[str]:
    """
    Attempt to get an SVG representation of a coin icon.

    Args:
        coin_id (str): The CoinGecko coin ID
        icon_urls (dict): Dictionary of icon URLs

    Returns:
        Optional[str]: SVG representation of the icon
    """
    # Priority: large > small > thumb
    icon_priority = ['large', 'small', 'thumb']
    
    for size in icon_priority:
        if icon_urls.get(size):
            svg = convert_png_to_svg(icon_urls[size])
            if svg:
                return svg
    
    return None