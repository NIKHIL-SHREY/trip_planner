from typing import List, Dict, Any
from tools.weather_tool import weather_tool
from tools.search_tool import search_tool
from tools.flight_tools import flight_tools
import logging

logger = logging.getLogger(__name__)

class TravelTools:
    def __init__(self):
        self.weather_tool = weather_tool
        self.search_tool = search_tool
        self.flight_tools = flight_tools
    
    def get_comprehensive_travel_data(self, destination: str, dates: str, 
                                    budget: float, preferences: List[str],
                                    origin_city: str = "New York") -> Dict[str, Any]:
        """
        Get all travel-related data with proper error handling and consistent scoring
        """
        try:
            logger.info(f"Collecting comprehensive travel data for {destination}")
            
            # Parse dates for extended weather analysis
            date_parts = dates.split(' to ')
            start_date = date_parts[0]
            end_date = date_parts[1] if len(date_parts) > 1 else start_date
            
            # Get enhanced weather data with consistent scoring
            weather_data = self.weather_tool.get_extended_weather_forecast(destination, start_date, end_date)
            weather_analysis = weather_data.get('weather_analysis', 'Weather information not available')
            
            # Get hotel options with enhanced search
            hotels = self.search_tool.search_hotels(destination, budget)
            
            # Get attractions with enhanced search
            attractions = self.search_tool.search_attractions(destination, preferences)
            
            # Get flight options with real search
            flight_result = self.flight_tools.search_flights(origin_city, destination, start_date, budget)
            flight_list = flight_result.get('flights', [])
            
            # Get general travel info
            travel_info = self.search_tool.search_travel_info(destination, "general")
            
            # Calculate viability with consistent scoring
            viability = self.check_weather_viability(weather_data)
            
            return {
                "weather_data": weather_data,
                "weather_analysis": weather_analysis,
                "weather_viability": viability,
                "hotel_options": hotels,
                "attraction_options": attractions,
                "flight_options": flight_list,
                "search_results": travel_info,
                "destination": destination,
                "status": "success"
            }
            
        except Exception as e:
            logger.error(f"Comprehensive travel data collection failed: {str(e)}")
            return {
                "status": "error",
                "error": f"Travel data collection failed: {str(e)}"
            }
    
    def check_weather_viability(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhanced weather viability check with consistent scoring
        """
        if "error" in weather_data:
            return {
                "viable": False, 
                "score": 0,
                "reason": "Weather data unavailable",
                "warnings": ["Cannot verify weather conditions"],
                "recommendations": ["Check weather manually"]
            }
        
        # FIXED: Use consistent scoring from extended analysis
        extended_analysis = weather_data.get('extended_analysis', {})
        
        if extended_analysis and 'overall_trip_score' in extended_analysis:
            trip_score = extended_analysis['overall_trip_score']
            recommendation = extended_analysis.get('overall_recommendation', '')
        else:
            trip_score = weather_data.get('viability_score', 50)
            recommendation = weather_data.get('viability_reason', '')
        
        viability = {
            "viable": trip_score >= 40,  # Consider viable if score >= 40
            "score": trip_score,
            "reason": recommendation,
            "warnings": [],
            "recommendations": weather_data.get('recommendations', [])
        }
        
        # Add warnings for poor conditions
        if trip_score < 30:
            viability["warnings"].append("Poor weather conditions expected")
        elif trip_score < 50:
            viability["warnings"].append("Moderate weather conditions")
        
        return viability

travel_tools = TravelTools()