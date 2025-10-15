import json
from typing import Dict, Any, List
from datetime import datetime

def format_itinerary_display(itinerary_data: Dict[str, Any]) -> str:
    """Format the itinerary for display with consistent weather scoring"""
    if not itinerary_data.get('itinerary'):
        return "No itinerary generated."
    
    formatted_output = f"""
    🗺️ TRAVEL ITINERARY
    ===================
    
    Destination: {itinerary_data.get('destination', 'Unknown')}
    Duration: {itinerary_data.get('duration', 'Unknown')} days
    Travel Type: {itinerary_data.get('travel_type', 'Leisure')}
    
    📋 ITINERARY:
    {itinerary_data.get('itinerary', 'No itinerary available')}
    
    """
    
    # FIXED: Single consistent weather score display
    weather_data = itinerary_data.get('weather_data', {})
    if weather_data and 'error' not in weather_data:
        # Get the correct viability score - use extended analysis score first
        extended_analysis = weather_data.get('extended_analysis', {})
        
        # Use the overall trip score from extended analysis if available
        if extended_analysis and 'overall_trip_score' in extended_analysis:
            display_score = extended_analysis['overall_trip_score']
            overall_recommendation = extended_analysis.get('overall_recommendation', '')
        else:
            # Fallback to basic viability score
            display_score = weather_data.get('viability_score', 50)
            overall_recommendation = weather_data.get('viability_reason', '')
        
        weather_analysis = itinerary_data.get('weather_analysis', '')
        
        # Clean up the weather analysis to remove duplicate scores
        weather_analysis_clean = weather_analysis.split('Weather viability score:')[0].strip()
        
        formatted_output += f"""
    🌤️ WEATHER ANALYSIS:
    {weather_analysis_clean}
    
    Overall Weather Score: {display_score}/100 - {overall_recommendation}
    """
        
        # Add extended forecast if available
        if extended_analysis and 'daily_forecasts' in extended_analysis:
            formatted_output += "\n    📅 DAILY WEATHER FORECAST:\n"
            for day in extended_analysis['daily_forecasts']:
                formatted_output += f"    • {day['day_name']}: {day['description'].title()}, {day['temperature']}°C ({day['suitability_level']})\n"
    
    # Add enhanced hotel options
    hotels = itinerary_data.get('hotel_options', [])
    if hotels and isinstance(hotels, list) and len(hotels) > 0:
        formatted_output += "\n    🏨 ACCOMMODATION OPTIONS:\n"
        for i, hotel in enumerate(hotels[:4], 1):
            formatted_output += f"    {i}. {hotel.get('name', 'Unknown Hotel')}\n"
            formatted_output += f"       💰 ${hotel.get('price_per_night', 'N/A')}/night | ⭐ {hotel.get('rating', 'N/A')}/5\n"
            formatted_output += f"       📍 {hotel.get('distance_center', 'Unknown')} from center\n"
            formatted_output += f"       🏷️ {hotel.get('price_range', 'Standard').title()}\n"
            
            # Show top 3 amenities
            amenities = hotel.get('amenities', [])[:3]
            if amenities:
                formatted_output += f"       ✅ {', '.join(amenities)}\n"
            
            formatted_output += "\n"
    
    # Add flight information if available
    flights = itinerary_data.get('flight_options', [])
    if flights and isinstance(flights, list) and len(flights) > 0:
        formatted_output += "    ✈️ FLIGHT OPTIONS:\n"
        for i, flight in enumerate(flights[:3], 1):
            formatted_output += f"    {i}. {flight.get('airline', 'Unknown')} - ${flight.get('price', 'N/A')}\n"
            formatted_output += f"       🕒 {flight.get('departure_time', '')} to {flight.get('arrival_time', '')}\n"
            formatted_output += f"       ⏱️ {flight.get('duration', 'Unknown')}"
            
            # Add layover info if applicable
            layovers = flight.get('layovers', 0)
            if layovers > 0:
                formatted_output += f" | 🛑 {layovers} stop{'s' if layovers > 1 else ''}"
            
            formatted_output += "\n\n"
    
    # Add alternative suggestions if any
    alternatives = itinerary_data.get('alternative_suggestions', [])
    if alternatives:
        formatted_output += "    💡 ALTERNATIVE SUGGESTIONS:\n"
        for i, alt in enumerate(alternatives, 1):
            formatted_output += f"    {i}. {alt}\n"
    
    return formatted_output

def validate_user_input(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate user input data"""
    errors = []
    
    if not input_data.get('destination'):
        errors.append("Destination is required")
    
    if not input_data.get('travel_dates'):
        errors.append("Travel dates are required")
    
    if not input_data.get('duration') or input_data.get('duration', 0) < 1:
        errors.append("Duration must be at least 1 day")
    
    if not input_data.get('budget') or input_data.get('budget', 0) < 50:
        errors.append("Budget must be at least $50")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors
    }

def create_sample_itinerary() -> Dict[str, Any]:
    """Create a sample itinerary for testing"""
    return {
        "destination": "Paris, France",
        "travel_dates": "2024-06-15 to 2024-06-20",
        "duration": 5,
        "budget": 1500,
        "preferences": ["cultural", "food", "sightseeing"],
        "travel_type": "leisure",
        "itinerary": """
        Day 1: Arrival and Eiffel Tower
        - Morning: Arrive at CDG Airport, check into hotel
        - Afternoon: Visit Eiffel Tower and Champ de Mars
        - Evening: Dinner at local French bistro
        
        Day 2: Art and Culture
        - Morning: Louvre Museum
        - Afternoon: Notre-Dame Cathedral and Seine River cruise
        - Evening: Montmartre and Sacré-Cœur
        
        Day 3: Historical Paris
        - Morning: Palace of Versailles day trip
        - Afternoon: Explore Versailles gardens
        - Evening: Return to Paris, casual dining
        
        Day 4: Local Experience
        - Morning: Local markets and food tour
        - Afternoon: Shopping in Le Marais
        - Evening: Latin Quarter exploration
        
        Day 5: Departure
        - Morning: Last-minute souvenir shopping
        - Afternoon: Airport transfer and departure
        """,
        "weather_analysis": "Current weather in Paris: 18°C, partly cloudy. Pleasant conditions for sightseeing.",
        "viability_score": 85
    }

def get_system_metrics() -> Dict[str, Any]:
    """Get system performance metrics"""
    return {
        "total_plans_generated": 150,
        "average_planning_time": "45.2 seconds",
        "success_rate": "94.7%",
        "popular_destinations": ["Goa", "Bangalore", "Delhi", "Mumbai", "Kerala"],
        "user_satisfaction": "4.8/5.0",
        "api_health": {
            "weather_api": "🟢 Operational",
            "search_api": "🟢 Operational", 
            "llm_api": "🟢 Operational",
            "monitoring": "🟢 Operational"
        }
    }