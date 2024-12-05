# import asyncio
# from typing import Any, Optional
# from .perplexity import search_perplexity
# from .utils import extract_revenue, extract_json, get_query

# async def process_query(section_name: str, coin_name: str) -> tuple[Any, Optional[str]]:
#     """
#     Process a query for a specific cryptocurrency and section with retry logic.

#     This function generates a query based on the provided section name and cryptocurrency,
#     performs a search using Perplexity AI, and then extracts relevant data from the search results.
#     It will retry up to 3 times if the result is not as expected.

#     Args:
#         section_name (str): The name of the section to query (e.g., "revenue", "upgrade", "hacks", "dapps").
#         coin_name (str): The name or symbol of the cryptocurrency (e.g., "BTC", "ETH").

#     Returns:
#         tuple: A tuple containing two elements:
#             - The extracted data (can be a number, list, or None depending on the section and result)
#             - An error message (str) if an error occurred, or None if successful

#     Note:
#         This function is asynchronous and should be called with await.
#     """
#     max_attempts = 3
    
#     for attempt in range(max_attempts):
#         # Get the appropriate query based on section_name and coin_name
#         query = get_query(section_name, coin_name)
        
#         if query is None:
#             return None, f"Invalid section name: {section_name}"

#         try:
#             # Perform the search using Perplexity AI
#             search_result = await search_perplexity(query)

#             # Extract data based on section_name
#             if 'revenue' in section_name.lower():
#                 extracted_data = extract_revenue(search_result)
#             else:
#                 extracted_data = extract_json(search_result)

#             # Check if data was successfully extracted
#             if extracted_data is not None:
#                 return extracted_data, None  # Success
            
#             # If we reach here, extraction failed but didn't raise an exception
#             if attempt < max_attempts - 1:
#                 print(f"Attempt {attempt + 1} failed. Retrying...")
#                 await asyncio.sleep(1)  # Wait for 1 second before retrying
#             else:
#                 return None, f"Failed to extract data for {section_name} of {coin_name} after {max_attempts} attempts"

#         except Exception as e:
#             if attempt < max_attempts - 1:
#                 print(f"Attempt {attempt + 1} failed with error: {str(e)}. Retrying...")
#                 await asyncio.sleep(1)  # Wait for 1 second before retrying
#             else:
#                 return None, f"Error after {max_attempts} attempts: {str(e)}"

#     # This line should never be reached, but it's here for completeness
#     return None, f"Unexpected error occurred after {max_attempts} attempts"


#NEW VERSION

import asyncio
from typing import Any, Optional
from .utils import extract_data_by_section, extract_raw_json, get_query
import os
from langchain_community.chat_models import ChatPerplexity


chat = ChatPerplexity(  
    model="llama-3.1-sonar-small-128k-online",
    temperature=0.7,
    pplx_api_key=os.getenv("PERPLEXITY_API")
)

async def get_perplexity_response(query):
   
    response1 = chat.invoke(query)
    content1 = response1.content

    return content1

async def process_query(section_name: str, coin_name: str) -> tuple[Any, Optional[str]]:
    """
    Process a query for a specific cryptocurrency and section with retry logic.

    This function generates a query based on the provided section name and cryptocurrency,
    performs a search using Perplexity AI, and then extracts relevant data from the search results.
    It will retry up to 3 times if the result is not as expected.

    Args:
        section_name (str): The name of the section to query (e.g., "revenue", "upgrades", "hacks", "dapps").
        coin_name (str): The name or symbol of the cryptocurrency (e.g., "BTC", "ETH").

    Returns:
        tuple: A tuple containing two elements:
            - The extracted data (can be a number, list, or None depending on the section and result)
            - An error message (str) if an error occurred, or None if successful

    Note:
        This function is asynchronous and should be called with await.
    """
    max_attempts = 3
    
    for attempt in range(max_attempts):
        # Get the appropriate query based on section_name and coin_name
        query = get_query(section_name, coin_name)
        
        if query is None:
            return None, f"Invalid section name: {section_name}"

        try:
            # Perform the search using Perplexity AI
            search_result = await get_perplexity_response(query)
            # Extract data based on section_name
            extracted_data = extract_data_by_section(section_name,search_result)
            print(extracted_data)
            # Check if data was successfully extracted
            if extracted_data is not None:
                return extracted_data, None  # Success

        except Exception as e:
            return None, f"Error: {str(e)}"




