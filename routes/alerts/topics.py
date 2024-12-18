from flask import Blueprint, request, jsonify
from config import Session, Topic

topics_bp = Blueprint('topics_bp', __name__)

@topics_bp.route('/topics', methods=['GET'])
def get_topics():
    """
    Get all topics based on optional query parameters.
    
    Query parameters:
        coin (str): Optional - Filter by coin reference
        type (str): Optional - Filter by topic type
        timeframe (str): Optional - Filter by timeframe
    
    Returns:
        JSON response with topics or error message
    
    Example:
        /topics                   # Get all topics
        /topics?coin=bitcoin     # Get bitcoin topics
        /topics?type=alerts&timeframe=1d  # Get daily alerts
    """
    try:
        # Get filter parameters from query string
        coin = request.args.get('coin')
        type = request.args.get('type')
        timeframe = request.args.get('timeframe')
        
        with Session() as session:
            query = session.query(Topic)
            
            # Apply filters if provided
            if coin:
                query = query.filter(Topic.reference.ilike(f"%{coin}%"))
            if type:
                query = query.filter(Topic.type == type)
            if timeframe:
                query = query.filter(Topic.timeframe == timeframe)
                
            topics = query.all()
            topics_list = [topic.as_dict() for topic in topics]
            
            return jsonify({
                "success": True,
                "data": topics_list,
                "count": len(topics_list)
            }), 200
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to fetch topics"
        }), 500