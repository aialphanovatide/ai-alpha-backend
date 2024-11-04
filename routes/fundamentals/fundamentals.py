

from config import Session
from flask import Blueprint, jsonify, request
from config import DApps, Hacks, Revenue_model, Upgrades
from services.fundamentals_populator.populator import process_query


fundamentals_bp = Blueprint('fundamentals_bp', __name__)


@fundamentals_bp.route('/api/save_fundamental_data', methods=['POST'])
def save_fundamental_data():
    """
    Endpoint for saving fundamental data to the appropriate table based on the section.

    Request JSON format:
    {
        "section_name": str,  # The type of data to save (e.g., "revenue", "upgrade", "hacks", "dapps")
        "coin_bot_id": int,   # The ID of the associated CoinBot
        "content": Any        # The content to be saved (format depends on the section)
    }

    Returns:
        A JSON response with the operation result.
    """
    with Session() as session:
        try:
            data = request.json
            section_name = data.get('section_name')
            coin_bot_id = data.get('coin_bot_id')
            content = data.get('content')

            if not all([section_name, coin_bot_id, content]):
                return jsonify({
                    'success': False,
                    'message': 'Missing required fields',
                    'code': 'MISSING_PARAMETERS'
                }), 400

            # Determine which table to save to based on section_name
            if section_name.lower() == 'revenue':
                new_entry = Revenue_model(
                    coin_bot_id=coin_bot_id,
                    analized_revenue=str(content),  # Assuming content is the revenue value
                    fees_1ys=None,  # You might want to add this to your query if needed
                    dynamic=True
                )
            elif section_name.lower() == 'upgrade':
                for upgrade in content:
                    new_entry = Upgrades(
                        coin_bot_id=coin_bot_id,
                        event=upgrade.get('Event'),
                        date=upgrade.get('Date'),
                        event_overview=upgrade.get('Event Overview'),
                        impact=upgrade.get('Impact'),
                        dynamic=True
                    )
                    session.add(new_entry)
            elif section_name.lower() == 'hacks':
                for hack in content:
                    new_entry = Hacks(
                        coin_bot_id=coin_bot_id,
                        hack_name=hack.get('Hack Name'),
                        date=hack.get('Date'),
                        incident_description=hack.get('Incident Description'),
                        consequences=hack.get('Consequences'),
                        mitigation_measure=hack.get('Risk Mitigation Measures'),
                        dynamic=True
                    )
                    session.add(new_entry)
            elif section_name.lower() == 'dapps':
                for dapp in content:
                    new_entry = DApps(
                        coin_bot_id=coin_bot_id,
                        dapps=dapp.get('DApp'),
                        description=dapp.get('Description'),
                        tvl=str(dapp.get('TVL')),  # Convert to string as per your schema
                        dynamic=True
                    )
                    session.add(new_entry)
            else:
                return jsonify({
                    'success': False,
                    'message': f'Invalid section name: {section_name}',
                    'code': 'INVALID_SECTION'
                }), 400

            # Commit the session to save all entries
            session.commit()

            return jsonify({
                'success': True,
                'message': f'Data for {section_name} saved successfully',
                'code': 'SUCCESS'
            }), 201

        except Exception as e:
            session.rollback()
            return jsonify({
                'success': False,
                'message': f'Error saving data: {str(e)}',
                'code': 'SERVER_ERROR'
            }), 500
            
            
            

@fundamentals_bp.route('/analysis/fundamental_ai_search', methods=['POST'])
async def fundamental_ai_search():
    """
    Endpoint for performing a fundamental AI search on cryptocurrency data.

    This function processes a POST request containing a section name and a coin name.
    It uses these parameters to query and retrieve specific cryptocurrency data using
    an AI-powered search function.

    Request JSON format:
    {
        "section_name": str,  # The type of data to retrieve (e.g., "revenue", "hacks", "dapps")
        "coin_name": str      # The name or symbol of the cryptocurrency (e.g., "BTC", "ETH")
    }

    Returns:
        A JSON response with the following structure:
        {
            "success": bool,  # Indicates if the operation was successful
            "message": str,   # A descriptive message about the result
            "code": str,      # A code indicating the status of the operation
            "data": Any       # The retrieved data, or None if an error occurred
        }

    HTTP Status Codes:
        200: Successful operation
        400: Bad request (missing parameters or query error)
        500: Server error
    """
    with Session() as session:  
        try:
            # Extract data from the request
            data = request.json
            section_name = data.get('section_name')
            coin_name = data.get('coin_name')

            # Validate input parameters
            if not section_name or not coin_name:
                return jsonify({
                    'success': False,
                    'message': 'Section name and coin name are required',
                    'code': 'MISSING_PARAMETERS',
                    'data': None
                }), 400

            # Process the query
            result, error = await process_query(section_name, coin_name)

            # Handle query errors
            if error:
                return jsonify({
                    'success': False,
                    'message': error,
                    'code': 'QUERY_ERROR',
                    'data': None
                }), 400

            # Return successful response
            return jsonify({
                'success': True,
                'message': 'Data retrieved successfully',
                'code': 'SUCCESS',
                'data': result
            }), 200

        except Exception as e:
            # Handle unexpected errors
            session.rollback()  # Rollback the session in case of error
            return jsonify({
                'success': False,
                'message': f'Error processing request: {str(e)}',
                'code': 'SERVER_ERROR',
                'data': None
            }), 500