from langchain.schema import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from config.settings import settings
from typing import Dict, Any, List
import json

class ItineraryChain:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.LLM_TEMPERATURE
        )
    
    def generate_itinerary(self, travel_data: Dict[str, Any], duration: int, 
                          preferences: List[str], travel_type: str) -> str:
        """
        Generate a detailed travel itinerary using LLM with enhanced weather analysis
        """
        try:
            # Prepare context from travel data
            weather_info = travel_data.get('weather_analysis', 'Weather information not available')
            weather_data = travel_data.get('weather_data', {})
            extended_analysis = weather_data.get('extended_analysis', {})
            daily_forecasts = extended_analysis.get('daily_forecasts', [])
            
            hotels = travel_data.get('hotel_options', [])
            attractions = travel_data.get('attraction_options', [])
            flights = travel_data.get('flight_options', [])
            
            # Format hotels and attractions
            hotel_list = "\n".join([
                f"- {hotel.get('name', 'Unknown')}: {hotel.get('description', 'No description')[:100]}..."
                for hotel in (hotels if isinstance(hotels, list) else [])[:3]
            ]) if hotels else "No hotel information available"
            
            attraction_list = "\n".join([
                f"- {attr.get('name', 'Unknown')} ({attr.get('category', 'General')}): {attr.get('description', 'No description')[:100]}..."
                for attr in attractions[:5]
            ]) if attractions else "No attraction information available"
            
            flight_info = "\n".join([
                f"- {flight.get('airline', 'Unknown')}: ${flight.get('price', 'N/A')} - {flight.get('departure_time', '')} to {flight.get('arrival_time', '')}"
                for flight in (flights if isinstance(flights, list) else [])[:2]
            ]) if flights else "No flight information available"
            
            # Enhanced weather information
            daily_weather_info = ""
            if daily_forecasts:
                daily_weather_info = "\n\nDAILY WEATHER FORECAST:\n"
                for day in daily_forecasts:
                    daily_weather_info += f"- {day['day_name']} ({day['date']}): {day['description']}, {day['temperature']}°C - {day['suitability_level']}\n"
            
            user_prompt = f"""
            Create a {duration}-day travel itinerary with the following details:
            
            DESTINATION: {travel_data.get('destination', 'Unknown')}
            TRAVEL TYPE: {travel_type}
            PREFERENCES: {', '.join(preferences)}
            DURATION: {duration} days
            
            OVERALL WEATHER ANALYSIS:
            {weather_info}
            {daily_weather_info}
            
            FLIGHT OPTIONS:
            {flight_info}
            
            AVAILABLE HOTELS:
            {hotel_list}
            
            AVAILABLE ATTRACTIONS:
            {attraction_list}
            
            Please create a detailed day-by-day itinerary that:
            1. Considers the daily weather conditions for appropriate activities
            2. Includes morning, afternoon, and evening activities
            3. Provides meal suggestions based on local cuisine
            4. Includes transportation tips between locations
            5. Suggests weather-appropriate clothing
            6. Considers budget for each day
            7. Matches the user's preferences: {', '.join(preferences)}
            
            Make the itinerary practical and enjoyable, adjusting activities based on daily weather conditions.
            If certain days have poor weather, suggest indoor alternatives.
            """
            
            try:
                system_prompt = """You are an expert travel planner. Create detailed, practical itineraries 
                that consider weather conditions, user preferences, and available attractions.
                Pay special attention to daily weather forecasts and adjust activities accordingly."""
                
                messages = [
                    SystemMessage(content=system_prompt),
                    HumanMessage(content=user_prompt)
                ]
                
                response = self.llm.invoke(messages)
                return response.content
                
            except Exception as llm_error:
                # Fallback itinerary generation without LLM
                return self._generate_fallback_itinerary(
                    travel_data.get('destination', 'Unknown'),
                    duration,
                    preferences,
                    travel_type,
                    weather_info,
                    daily_forecasts,
                    hotels,
                    attractions
                )
            
        except Exception as e:
            return f"Error generating itinerary: {str(e)}"
    
    def _generate_fallback_itinerary(self, destination: str, duration: int, 
                                   preferences: List[str], travel_type: str,
                                   weather_info: str, daily_forecasts: List[Dict],
                                   hotels: List[Dict], attractions: List[Dict]) -> str:
        """Generate a basic itinerary without LLM as fallback"""
        
        hotel_names = [hotel.get('name', 'Hotel') for hotel in (hotels if isinstance(hotels, list) else [])[:2]]
        attraction_names = [attr.get('name', 'Attraction') for attr in attractions[:5]]
        
        itinerary = f"""
        {destination.upper()} TRAVEL ITINERARY ({duration} Days)
        ===========================================
        
        Destination: {destination}
        Duration: {duration} days
        Travel Type: {travel_type}
        Preferences: {', '.join(preferences)}
        
        WEATHER ANALYSIS:
        {weather_info}
        
        """
        
        # Add daily weather if available
        if daily_forecasts:
            itinerary += "DAILY WEATHER FORECAST:\n"
            for day in daily_forecasts:
                itinerary += f"- {day['day_name']}: {day['description']}, {day['temperature']}°C ({day['suitability_level']})\n"
            itinerary += "\n"
        
        itinerary += f"""
        RECOMMENDED ACCOMMODATIONS:
        {chr(10).join(f"- {hotel}" for hotel in hotel_names) if hotel_names else "No hotel information available"}
        
        """
        
        # Generate day-by-day itinerary considering weather
        for day in range(1, duration + 1):
            day_weather = daily_forecasts[day-1] if day <= len(daily_forecasts) else None
            weather_desc = day_weather['description'] if day_weather else "Unknown"
            
            itinerary += f"""
        DAY {day}:
        ---------
        Weather: {weather_desc}
        
        Morning: Explore local attractions and get familiar with the area
        Afternoon: Visit {attraction_names[day % len(attraction_names)] if attraction_names else 'local landmarks'}
        Evening: Enjoy local cuisine and relax
        
        Recommendations: {', '.join(day_weather.get('recommendations', ['Plan according to weather'])) if day_weather else 'Check weather updates'}
        
        """
        
        itinerary += """
        GENERAL TRAVEL TIPS:
        - Check weather forecast daily and dress appropriately
        - Keep local emergency numbers handy
        - Stay hydrated and take breaks
        - Try local specialties and cuisine
        - Respect local customs and culture
        
        BUDGET TIPS:
        - Consider public transportation
        - Look for free attractions and activities
        - Eat at local restaurants away from tourist areas
        - Book accommodations in advance for better rates
        """
        
        return itinerary
    
    def generate_alternative_suggestions(self, destination: str, issue: str, 
                                       preferences: List[str]) -> List[str]:
        """
        Generate alternative travel suggestions when primary plan has issues
        """
        try:
            prompt = f"""
            The travel plan for {destination} has an issue: {issue}
            
            User preferences: {', '.join(preferences)}
            
            Suggest 3 alternative solutions. These could be:
            1. Alternative dates with better weather
            2. Nearby destinations with similar appeal
            3. Modified activities that work around the issue
            4. Indoor alternatives for poor weather days
            
            Provide concise, practical alternatives.
            """
            
            try:
                response = self.llm.invoke([
                    SystemMessage(content="You provide creative travel solutions and alternatives."),
                    HumanMessage(content=prompt)
                ])
                
                # Parse the response into a list of alternatives
                alternatives = [
                    line.strip()[3:] if line.strip().startswith(f"{i+1}.") else line.strip()
                    for i, line in enumerate(response.content.split('\n'))
                    if line.strip() and not line.strip().startswith('Alternative')
                ]
                
                return [alt for alt in alternatives if alt][:3]
                
            except Exception as llm_error:
                # Fallback alternatives
                return [
                    f"Consider visiting {destination} during different dates with better weather",
                    f"Explore indoor activities and museums in {destination}",
                    f"Look for nearby destinations with better weather conditions"
                ]
            
        except Exception as e:
            return [f"Could not generate alternatives due to error: {str(e)}"]

itinerary_chain = ItineraryChain()