from typing import TypedDict, List, Optional, Dict, Any, Annotated
from langgraph.graph import add_messages
import operator

class TripPlannerState(TypedDict):
    # User Input & Conversation
    messages: Annotated[List[Any], add_messages]
    destination: str
    travel_dates: str
    duration: int
    budget: float
    preferences: List[str]
    travel_type: str
    user_feedback: Optional[str]
    
    # Processing Data
    current_step: str
    requires_input: bool
    conversation_history: List[Dict[str, str]]
    missing_information: List[str]
    
    # API Results
    weather_data: Optional[Dict[str, Any]]
    weather_analysis: Optional[str]
    weather_viability: Optional[Dict[str, Any]]
    hotel_options: List[Dict[str, Any]]
    attraction_options: List[Dict[str, Any]]
    flight_options: List[Dict[str, Any]]  # NEW
    search_results: List[Dict[str, Any]]
    
    # Decision Metrics
    budget_compliance: bool
    preference_match_score: float
    weather_score: float
    
    # Generated Content
    itinerary: Optional[str]
    alternative_suggestions: List[str]
    final_recommendation: Optional[str]
    itinerary_quality_score: Optional[float]
    
    # Control Flow
    should_continue: bool
    max_iterations: int
    current_iteration: int
    error_message: Optional[str]
    retry_count: int