from langgraph.graph import StateGraph, END
from langgraph.prebuilt import create_react_agent
from langchain_google_genai import ChatGoogleGenerativeAI  # FIXED IMPORT
from langchain.schema import SystemMessage, HumanMessage
from typing import Dict, Any, Literal
import logging
from agents.state import TripPlannerState
from tools.travel_tools import travel_tools
from chains.itinerary_chain import itinerary_chain
from config.settings import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TripPlannerAgent:
    def __init__(self):
        self.llm = ChatGoogleGenerativeAI(
            model=settings.LLM_MODEL,
            google_api_key=settings.GEMINI_API_KEY,
            temperature=settings.LLM_TEMPERATURE
        )
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build the enhanced LangGraph state machine"""
        workflow = StateGraph(TripPlannerState)
        
        # Add all nodes
        workflow.add_node("collect_user_input", self.collect_user_input)
        workflow.add_node("gather_travel_data", self.gather_travel_data)
        workflow.add_node("analyze_weather", self.analyze_weather)
        workflow.add_node("search_accommodations", self.search_accommodations)
        workflow.add_node("search_flights", self.search_flights)
        workflow.add_node("generate_itinerary", self.generate_itinerary)
        workflow.add_node("provide_alternatives", self.provide_alternatives)
        workflow.add_node("finalize_recommendation", self.finalize_recommendation)
        workflow.add_node("handle_feedback", self.handle_feedback)
        
        # Set entry point
        workflow.set_entry_point("collect_user_input")
        
        # Define complex conditional edges
        workflow.add_conditional_edges(
            "collect_user_input",
            self.decide_after_input_collection,
            {
                "complete": "gather_travel_data",
                "incomplete": "collect_user_input",
                "error": "provide_alternatives"
            }
        )
        
        workflow.add_conditional_edges(
            "gather_travel_data",
            self.decide_after_data_collection,
            {
                "weather_check": "analyze_weather",
                "direct_planning": "search_flights",
                "error": "provide_alternatives"
            }
        )
        
        workflow.add_conditional_edges(
            "analyze_weather",
            self.decide_after_weather_analysis,
            {
                "favorable": "search_accommodations",
                "unfavorable": "provide_alternatives",
                "conditional": "search_flights"
            }
        )
        
        workflow.add_edge("search_accommodations", "search_flights")
        workflow.add_edge("search_flights", "generate_itinerary")
        
        workflow.add_conditional_edges(
            "generate_itinerary",
            self.decide_after_itinerary,
            {
                "success": "finalize_recommendation",
                "needs_improvement": "provide_alternatives",
                "error": "provide_alternatives"
            }
        )
        
        workflow.add_conditional_edges(
            "finalize_recommendation",
            self.decide_after_finalization,
            {
                "accepted": END,
                "needs_revision": "handle_feedback",
                "rejected": "provide_alternatives"
            }
        )
        
        workflow.add_conditional_edges(
            "handle_feedback",
            self.decide_after_feedback,
            {
                "regenerate": "generate_itinerary",
                "new_search": "gather_travel_data",
                "weather_recheck": "analyze_weather"
            }
        )
        
        workflow.add_edge("provide_alternatives", "finalize_recommendation")
        
        return workflow.compile()
    
    def collect_user_input(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced user input collection with conversation"""
        logger.info("Collecting user input")
        
        current_messages = state.get("messages", [])
        missing_info = state.get("missing_information", [])
        
        # Check if we have all required information
        required_fields = ["destination", "travel_dates", "duration", "budget"]
        current_state = {field: state.get(field) for field in required_fields}
        
        # Identify missing information
        new_missing = [field for field, value in current_state.items() if not value]
        
        if not new_missing and not missing_info:
            return {
                "current_step": "data_collection",
                "requires_input": False,
                "missing_information": []
            }
        
        # Update missing information
        if new_missing:
            return {
                "current_step": "input_collection",
                "requires_input": True,
                "missing_information": new_missing,
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": f"Need information: {', '.join(new_missing)}"}]
            }
        
        return {
            "current_step": "data_collection",
            "requires_input": False
        }
    
    def gather_travel_data(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced data gathering with comprehensive metrics"""
        logger.info(f"Gathering comprehensive travel data for {state.get('destination')}")
        
        try:
            travel_data = travel_tools.get_comprehensive_travel_data(
                destination=state.get('destination', ''),
                dates=state.get('travel_dates', ''),
                budget=state.get('budget', settings.DEFAULT_BUDGET),
                preferences=state.get('preferences', []),
                origin_city=state.get('origin_city', 'New York')
            )
            
            if travel_data.get('status') == 'success':
                # Get weather viability from the basic weather data
                weather_viability = travel_tools.check_weather_viability(travel_data.get('weather_data', {}))
                
                return {
                    "weather_data": travel_data['weather_data'],
                    "weather_analysis": travel_data['weather_analysis'],
                    "weather_viability": weather_viability,
                    "hotel_options": travel_data['hotel_options'],
                    "attraction_options": travel_data['attraction_options'],
                    "flight_options": travel_data['flight_options'],
                    "search_results": travel_data['search_results'],
                    "current_step": "weather_analysis",
                    "conversation_history": state.get("conversation_history", []) + 
                                           [{"role": "system", "content": "Travel data collected successfully"}]
                }
            else:
                return {
                    "error_message": travel_data.get('error', 'Unknown error in data collection'),
                    "current_step": "error_handling",
                    "conversation_history": state.get("conversation_history", []) + 
                                           [{"role": "system", "content": f"Data collection error: {travel_data.get('error')}"}]
                }
                
        except Exception as e:
            logger.error(f"Data collection failed: {str(e)}")
            return {
                "error_message": f"Data collection failed: {str(e)}",
                "current_step": "error_handling",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": f"Data collection exception: {str(e)}"}]
            }
    
    def analyze_weather(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced weather analysis with scoring"""
        logger.info("Analyzing weather conditions with scoring")
        
        try:
            viability = state.get('weather_viability', {})
            weather_score = state.get('weather_score', 0)
            
            analysis_update = state.get('weather_analysis', '') + f"\nWeather Viability Score: {weather_score}/100"
            
            if viability.get('viable', False):
                return {
                    "current_step": "accommodation_search",
                    "weather_analysis": analysis_update,
                    "conversation_history": state.get("conversation_history", []) + 
                                           [{"role": "system", "content": "Weather conditions favorable"}]
                }
            else:
                alternatives = ["Consider alternative dates", "Look for nearby destinations", "Plan indoor activities"]
                return {
                    "current_step": "alternative_planning",
                    "weather_analysis": analysis_update,
                    "alternative_suggestions": alternatives,
                    "conversation_history": state.get("conversation_history", []) + 
                                           [{"role": "system", "content": "Weather conditions unfavorable, generating alternatives"}]
                }
                
        except Exception as e:
            return {
                "current_step": "alternative_planning",
                "error_message": f"Weather analysis error: {str(e)}",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": f"Weather analysis error: {str(e)}"}]
            }
    
    def search_accommodations(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced accommodation search with preference matching"""
        logger.info("Searching for accommodations with preference matching")
        
        hotels = state.get('hotel_options', [])
        budget = state.get('budget', settings.DEFAULT_BUDGET)
        
        # Filter and rank hotels
        filtered_hotels = [
            hotel for hotel in hotels 
            if not hotel.get('error') and self._is_within_budget(hotel, budget)
        ][:3]
        
        return {
            "hotel_options": filtered_hotels,
            "current_step": "flight_search",
            "conversation_history": state.get("conversation_history", []) + 
                                   [{"role": "system", "content": f"Found {len(filtered_hotels)} accommodation options"}]
        }
    
    def search_flights(self, state: TripPlannerState) -> Dict[str, Any]:
        """Flight search integration"""
        logger.info("Searching for flight options")
        
        flights = state.get('flight_options', [])
        
        return {
            "flight_options": flights,
            "current_step": "itinerary_generation",
            "conversation_history": state.get("conversation_history", []) + 
                                   [{"role": "system", "content": f"Found {len(flights)} flight options"}]
        }
    
    def generate_itinerary(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced itinerary generation with quality scoring"""
        logger.info("Generating comprehensive travel itinerary")
        
        try:
            itinerary = itinerary_chain.generate_itinerary(
                travel_data={
                    'destination': state.get('destination'),
                    'weather_analysis': state.get('weather_analysis', ''),
                    'hotels': state.get('hotel_options', []),
                    'attractions': state.get('attraction_options', []),
                    'flights': state.get('flight_options', [])
                },
                duration=state.get('duration', 3),
                preferences=state.get('preferences', []),
                travel_type=state.get('travel_type', 'leisure')
            )
            
            # Calculate itinerary quality score
            quality_score = self._calculate_itinerary_quality(itinerary, state)
            
            return {
                "itinerary": itinerary,
                "itinerary_quality_score": quality_score,
                "current_step": "finalization",
                "final_recommendation": f"Trip plan generated with quality score: {quality_score}/100",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": "Itinerary generated successfully"}]
            }
            
        except Exception as e:
            logger.error(f"Itinerary generation failed: {str(e)}")
            return {
                "error_message": f"Itinerary generation failed: {str(e)}",
                "current_step": "alternative_planning",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": f"Itinerary generation error: {str(e)}"}]
            }
    
    def provide_alternatives(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced alternative suggestions"""
        logger.info("Generating comprehensive alternative suggestions")
        
        try:
            alternatives = itinerary_chain.generate_alternative_suggestions(
                destination=state.get('destination', ''),
                issue=state.get('error_message', 'Planning constraints encountered'),
                preferences=state.get('preferences', [])
            )
            
            return {
                "alternative_suggestions": alternatives,
                "current_step": "finalization",
                "final_recommendation": "Alternative travel suggestions provided",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": "Generated alternative suggestions"}]
            }
            
        except Exception as e:
            return {
                "alternative_suggestions": ["Please adjust your travel parameters and try again"],
                "current_step": "finalization",
                "final_recommendation": "Unable to create optimal plan. Please try different parameters.",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": f"Alternative generation error: {str(e)}"}]
            }
    
    def finalize_recommendation(self, state: TripPlannerState) -> Dict[str, Any]:
        """Enhanced finalization with comprehensive output"""
        logger.info("Finalizing travel recommendation")
        
        recommendation = {
            "status": "completed",
            "itinerary": state.get('itinerary'),
            "alternative_suggestions": state.get('alternative_suggestions', []),
            "quality_score": state.get('itinerary_quality_score', 0),
            "weather_analysis": state.get('weather_analysis'),
            "hotel_options": state.get('hotel_options', []),
            "flight_options": state.get('flight_options', [])
        }
        
        return {
            "current_step": "completed",
            "requires_input": False,
            "should_continue": False,
            "final_recommendation": recommendation,
            "conversation_history": state.get("conversation_history", []) + 
                                   [{"role": "system", "content": "Recommendation finalized"}]
        }
    
    def handle_feedback(self, state: TripPlannerState) -> Dict[str, Any]:
        """Handle user feedback and decide next steps"""
        logger.info("Processing user feedback")
        
        feedback = state.get('user_feedback', '').lower()
        current_step = state.get('current_step', '')
        
        # Analyze feedback to decide next action
        if any(word in feedback for word in ['weather', 'rain', 'storm']):
            next_action = "weather_recheck"
        elif any(word in feedback for word in ['hotel', 'accommodation', 'stay']):
            next_action = "new_search"
        elif any(word in feedback for word in ['itinerary', 'schedule', 'plan']):
            next_action = "regenerate"
        else:
            next_action = "regenerate"  # Default action
        
        return {
            "current_step": next_action,
            "conversation_history": state.get("conversation_history", []) + 
                                   [{"role": "system", "content": f"Processing feedback, next action: {next_action}"}]
        }
    
    # Decision methods
    def decide_after_input_collection(self, state: TripPlannerState) -> Literal["complete", "incomplete", "error"]:
        if state.get('error_message'):
            return "error"
        elif not state.get('requires_input', True):
            return "complete"
        else:
            return "incomplete"
    
    def decide_after_data_collection(self, state: TripPlannerState) -> Literal["weather_check", "direct_planning", "error"]:
        if state.get('error_message'):
            return "error"
        elif state.get('weather_data') and 'error' not in state.get('weather_data', {}):
            return "weather_check"
        else:
            return "direct_planning"
    
    def decide_after_weather_analysis(self, state: TripPlannerState) -> Literal["favorable", "unfavorable", "conditional"]:
        viability = state.get('weather_viability', {})
        if viability.get('viable', False):
            return "favorable"
        elif viability.get('score', 0) < 30:
            return "unfavorable"
        else:
            return "conditional"
    
    def decide_after_itinerary(self, state: TripPlannerState) -> Literal["success", "needs_improvement", "error"]:
        if state.get('error_message'):
            return "error"
        elif state.get('itinerary_quality_score', 0) >= 70:
            return "success"
        else:
            return "needs_improvement"
    
    def decide_after_finalization(self, state: TripPlannerState) -> Literal["accepted", "needs_revision", "rejected"]:
        # This would typically come from user feedback
        # For demo purposes, we assume acceptance
        return "accepted"
    
    def decide_after_feedback(self, state: TripPlannerState) -> Literal["regenerate", "new_search", "weather_recheck"]:
        feedback = state.get('user_feedback', '').lower()
        
        if any(word in feedback for word in ['weather', 'rain']):
            return "weather_recheck"
        elif any(word in feedback for word in ['hotel', 'flight']):
            return "new_search"
        else:
            return "regenerate"
    
    # Helper methods
    def _is_within_budget(self, hotel: Dict[str, Any], budget: float) -> bool:
        """Simple budget check"""
        return True  # Accept all for demo
    
    def _calculate_itinerary_quality(self, itinerary: str, state: TripPlannerState) -> float:
        """Calculate itinerary quality score"""
        if not itinerary:
            return 0
        
        score = 50  # Base score
        
        # Add points for length
        if len(itinerary) > 500:
            score += 20
        
        # Add points for structure
        if any(marker in itinerary for marker in ['Day 1', 'Day 2', 'Morning', 'Afternoon']):
            score += 20
        
        # Add points for comprehensiveness
        if all(keyword in itinerary for keyword in ['hotel', 'activities', 'restaurant']):
            score += 10
        
        return min(100, score)
    
    def plan_trip(self, initial_state: Dict[str, Any]) -> Dict[str, Any]:
        """Main method to execute trip planning with enhanced monitoring"""
        try:
            # Initialize state with defaults
            state = {
                "max_iterations": settings.MAX_ITERATIONS,
                "current_iteration": 0,
                "should_continue": True,
                "conversation_history": [],
                "missing_information": [],
                "retry_count": 0,
                **initial_state
            }
            
            logger.info("Starting trip planning process")
            
            # Execute the graph
            final_state = self.graph.invoke(state)
            
            logger.info("Trip planning completed successfully")
            return final_state
            
        except Exception as e:
            logger.error(f"Trip planning failed: {str(e)}")
            return {
                "error_message": f"Trip planning failed: {str(e)}",
                "itinerary": None,
                "final_recommendation": "Unable to generate travel plan. Please try again.",
                "conversation_history": state.get("conversation_history", []) + 
                                       [{"role": "system", "content": f"Planning process error: {str(e)}"}]
            }