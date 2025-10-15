import requests
from typing import Dict, Any, Optional, List
from config.settings import settings
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class WeatherTool:
    def __init__(self):
        self.api_key = settings.OPENWEATHER_API_KEY
        self.base_url = settings.OPENWEATHER_BASE_URL
    
    def get_weather_forecast(self, city: str, date: str = None) -> Dict[str, Any]:
        """
        Get weather forecast for a city using OpenWeatherMap API
        """
        try:
            # First, get coordinates for the city
            geo_url = f"{self.base_url}/weather"
            geo_params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            geo_response = requests.get(geo_url, params=geo_params)
            if geo_response.status_code != 200:
                return {"error": f"Could not find weather data for {city}"}
            
            geo_data = geo_response.json()
            lat = geo_data['coord']['lat']
            lon = geo_data['coord']['lon']
            
            # Get current weather
            current_weather = self._get_current_weather(lat, lon)
            
            # Get 5-day forecast
            forecast = self._get_5day_forecast(lat, lon)
            
            # Analyze weather conditions
            weather_analysis = self.analyze_weather_conditions({
                "city": city,
                "current_weather": current_weather,
                "forecast": forecast
            })
            
            # Calculate viability score
            viability = self._calculate_viability_score(current_weather, forecast)
            
            return {
                "city": city,
                "current_weather": current_weather,
                "forecast": forecast,
                "weather_analysis": weather_analysis,
                "viability_score": viability["score"],
                "viability_reason": viability["reason"],
                "recommendations": viability["recommendations"],
                "coordinates": {"lat": lat, "lon": lon}
            }
            
        except Exception as e:
            logger.error(f"Weather API error: {str(e)}")
            return {"error": f"Weather API error: {str(e)}"}
    
    def get_extended_weather_forecast(self, city: str, start_date: str, end_date: str) -> Dict[str, Any]:
        """
        Get extended weather forecast for trip duration with consistent scoring
        """
        try:
            basic_forecast = self.get_weather_forecast(city)
            
            if "error" in basic_forecast:
                return basic_forecast
            
            # Parse dates
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            duration = (end_dt - start_dt).days + 1
            
            # Create daily forecasts
            daily_forecasts = []
            current_weather = basic_forecast.get('current_weather', {})
            forecast_data = basic_forecast.get('forecast', [])
            
            for day in range(duration):
                forecast_date = (start_dt + timedelta(days=day)).strftime('%Y-%m-%d')
                day_name = (start_dt + timedelta(days=day)).strftime('%A')
                
                # Use forecast data if available, otherwise use current weather
                if day < len(forecast_data) and forecast_data:
                    day_data = forecast_data[day]
                    temp = day_data.get('temperature', current_weather.get('temperature', 25))
                    description = day_data.get('description', current_weather.get('description', 'clear sky'))
                    wind_speed = day_data.get('wind_speed', current_weather.get('wind_speed', 5))
                else:
                    temp = current_weather.get('temperature', 25)
                    description = current_weather.get('description', 'clear sky')
                    wind_speed = current_weather.get('wind_speed', 5)
                
                # Calculate daily score
                daily_score = self._calculate_daily_suitability_score(temp, description, wind_speed, 0)
                
                daily_forecasts.append({
                    'date': forecast_date,
                    'day_name': day_name,
                    'temperature': temp,
                    'description': description,
                    'wind_speed': wind_speed,
                    'suitability_score': daily_score,
                    'suitability_level': self._get_suitability_level(daily_score),
                    'recommendations': self._get_daily_recommendations(temp, description, 0)
                })
            
            # Calculate overall trip score - FIXED: Use proper averaging
            daily_scores = [day['suitability_score'] for day in daily_forecasts]
            overall_score = sum(daily_scores) / len(daily_scores) if daily_scores else basic_forecast.get('viability_score', 50)
            
            # Ensure the basic forecast has the correct viability score
            basic_forecast['viability_score'] = overall_score
            
            return {
                **basic_forecast,
                "extended_analysis": {
                    "daily_forecasts": daily_forecasts,
                    "trip_duration": duration,
                    "overall_trip_score": overall_score,  # FIXED: Consistent scoring
                    "overall_recommendation": self._get_overall_recommendation(overall_score)
                }
            }
            
        except Exception as e:
            logger.error(f"Extended weather forecast error: {str(e)}")
            return {"error": f"Extended weather forecast error: {str(e)}"}
    
    def _calculate_viability_score(self, current_weather: Dict, forecast: List[Dict]) -> Dict[str, Any]:
        """Calculate weather viability score with proper logic"""
        if "error" in current_weather:
            return {"score": 0, "reason": "Weather data unavailable", "recommendations": []}
        
        score = 100
        reasons = []
        recommendations = []
        
        temp = current_weather.get('temperature', 20)
        description = current_weather.get('description', '').lower()
        wind_speed = current_weather.get('wind_speed', 0)
        
        # Temperature scoring (ideal: 15-28°C)
        if 18 <= temp <= 28:
            score += 10
            reasons.append("Perfect temperature")
        elif 15 <= temp <= 30:
            score += 5
            reasons.append("Good temperature")
        elif temp < 5 or temp > 35:
            score -= 40
            reasons.append("Extreme temperature")
            recommendations.append("Consider rescheduling due to extreme temperatures")
        elif temp < 10 or temp > 32:
            score -= 20
            reasons.append("Uncomfortable temperature")
        
        # Weather condition scoring
        if any(word in description for word in ['clear', 'sunny', 'fair']):
            score += 20
            reasons.append("Excellent weather conditions")
        elif any(word in description for word in ['cloud', 'overcast']):
            score += 5
            reasons.append("Cloudy but suitable")
        elif any(word in description for word in ['drizzle', 'light rain']):
            score -= 10
            reasons.append("Light rain expected")
            recommendations.append("Carry umbrella or raincoat")
        elif any(word in description for word in ['rain', 'shower']):
            score -= 25
            reasons.append("Rain expected")
            recommendations.append("Plan indoor activities")
        elif any(word in description for word in ['storm', 'thunder']):
            score -= 50
            reasons.append("Storm conditions")
            recommendations.append("Consider rescheduling - storm warning")
        elif any(word in description for word in ['snow', 'ice']):
            score -= 30
            reasons.append("Snow conditions")
            recommendations.append("Check travel advisories")
        
        # Wind scoring
        if wind_speed > 20:
            score -= 15
            reasons.append("High winds")
            recommendations.append("Secure outdoor items")
        elif wind_speed > 15:
            score -= 5
            reasons.append("Moderate winds")
        
        # Ensure score is within bounds
        score = max(0, min(100, score))
        
        return {
            "score": score,
            "reason": "; ".join(reasons),
            "recommendations": recommendations
        }
    
    def _get_current_weather(self, lat: float, lon: float) -> Dict[str, Any]:
        url = f"{self.base_url}/weather"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            return {
                "temperature": data['main']['temp'],
                "feels_like": data['main']['feels_like'],
                "humidity": data['main']['humidity'],
                "description": data['weather'][0]['description'],
                "wind_speed": data['wind']['speed'],
                "visibility": data.get('visibility', 'N/A')
            }
        return {"error": "Could not fetch current weather"}
    
    def _get_5day_forecast(self, lat: float, lon: float) -> List[Dict[str, Any]]:
        url = f"{self.base_url}/forecast"
        params = {
            'lat': lat,
            'lon': lon,
            'appid': self.api_key,
            'units': 'metric'
        }
        
        response = requests.get(url, params=params)
        forecasts = []
        
        if response.status_code == 200:
            data = response.json()
            # Get one forecast per day for next 5 days
            for i in range(0, min(5 * 8, len(data['list'])), 8):
                item = data['list'][i]
                forecasts.append({
                    "datetime": item['dt_txt'],
                    "temperature": item['main']['temp'],
                    "description": item['weather'][0]['description'],
                    "humidity": item['main']['humidity'],
                    "wind_speed": item['wind']['speed']
                })
        
        return forecasts
    
    def analyze_weather_conditions(self, weather_data: Dict[str, Any]) -> str:
        """
        Analyze weather conditions and provide recommendations
        """
        if "error" in weather_data:
            return f"Weather analysis unavailable: {weather_data['error']}"
        
        current = weather_data['current_weather']
        temp = current['temperature']
        description = current['description']
        viability_score = weather_data.get('viability_score', 50)
        
        analysis = f"Current weather in {weather_data['city']}: {temp}°C, {description}. "
        analysis += f"Weather viability score: {viability_score}/100. "
        
        # Add specific recommendations based on score
        if viability_score >= 80:
            analysis += "Excellent conditions for travel! "
        elif viability_score >= 60:
            analysis += "Good conditions with minor considerations. "
        elif viability_score >= 40:
            analysis += "Fair conditions - some adjustments needed. "
        else:
            analysis += "Challenging conditions - consider alternatives. "
        
        # Weather-specific recommendations
        if temp > 30:
            analysis += "Hot weather - stay hydrated and seek shade. "
        elif temp < 10:
            analysis += "Cold weather - pack warm clothing. "
        
        desc_lower = description.lower()
        if 'rain' in desc_lower:
            analysis += "Rain expected - pack rain gear. "
        if 'wind' in desc_lower or current.get('wind_speed', 0) > 15:
            analysis += "Windy conditions expected. "
        
        return analysis
    
    def _calculate_daily_suitability_score(self, temp: float, description: str, wind: float, rain_prob: float) -> float:
        """Calculate daily weather suitability score"""
        score = 100
        
        # Temperature adjustments
        if temp < 0 or temp > 40:
            score -= 40
        elif temp < 5 or temp > 35:
            score -= 25
        elif temp < 10 or temp > 30:
            score -= 15
        elif 18 <= temp <= 28:
            score += 10
        
        # Weather condition adjustments
        desc_lower = description.lower()
        if any(word in desc_lower for word in ['storm', 'hurricane', 'tornado']):
            score -= 50
        elif any(word in desc_lower for word in ['heavy rain', 'thunderstorm']):
            score -= 40
        elif any(word in desc_lower for word in ['rain', 'shower']):
            score -= 20
        elif any(word in desc_lower for word in ['snow', 'sleet']):
            score -= 30
        elif any(word in desc_lower for word in ['clear', 'sunny']):
            score += 15
        elif 'cloud' in desc_lower:
            score += 5
        
        # Wind adjustments
        if wind > 25:
            score -= 20
        elif wind > 15:
            score -= 10
        
        return max(0, min(100, score))
    
    def _get_suitability_level(self, score: float) -> str:
        """Convert score to suitability level"""
        if score >= 80:
            return "Excellent"
        elif score >= 60:
            return "Good"
        elif score >= 40:
            return "Fair"
        elif score >= 20:
            return "Poor"
        else:
            return "Very Poor"
    
    def _get_daily_recommendations(self, temp: float, description: str, rain_prob: float) -> List[str]:
        """Get daily activity recommendations"""
        recommendations = []
        desc_lower = description.lower()
        
        if temp > 30:
            recommendations.extend(["Stay hydrated", "Wear light clothing", "Seek shade during peak hours"])
        elif temp < 10:
            recommendations.extend(["Warm layers needed", "Limit outdoor exposure", "Hot beverages recommended"])
        
        if any(word in desc_lower for word in ['rain', 'drizzle']):
            recommendations.extend(["Carry umbrella", "Waterproof footwear", "Have indoor backup plans"])
        elif any(word in desc_lower for word in ['storm', 'thunder']):
            recommendations.extend(["Avoid outdoor activities", "Seek shelter if needed", "Check weather alerts"])
        elif 'clear' in desc_lower or 'sunny' in desc_lower:
            recommendations.extend(["Perfect for outdoor activities", "Sunscreen recommended", "Great for photography"])
        
        return recommendations if recommendations else ["Generally good conditions for activities"]
    
    def _get_overall_recommendation(self, score: float) -> str:
        """Get overall recommendation based on score"""
        if score >= 80:
            return "Excellent weather conditions for your trip!"
        elif score >= 60:
            return "Good weather conditions with minor considerations."
        elif score >= 40:
            return "Fair weather - some days may require alternative plans."
        else:
            return "Poor weather conditions - consider rescheduling or indoor alternatives."
    
    def get_consistent_weather_score(self, weather_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure consistent weather scoring across the application"""
        if "error" in weather_data:
            return {"score": 0, "level": "Unknown", "recommendation": "Weather data unavailable"}
        
        # Use extended analysis score if available
        extended_analysis = weather_data.get('extended_analysis', {})
        if extended_analysis and 'overall_trip_score' in extended_analysis:
            score = extended_analysis['overall_trip_score']
            recommendation = extended_analysis.get('overall_recommendation', '')
        else:
            # Fallback to basic viability score
            score = weather_data.get('viability_score', 50)
            recommendation = weather_data.get('viability_reason', '')
        
        # Convert score to level
        if score >= 80:
            level = "Excellent"
        elif score >= 60:
            level = "Good" 
        elif score >= 40:
            level = "Fair"
        elif score >= 20:
            level = "Poor"
        else:
            level = "Very Poor"
        
        return {
            "score": score,
            "level": level,
            "recommendation": recommendation,
            "display_text": f"{score}/100 - {level}"
        }

weather_tool = WeatherTool()