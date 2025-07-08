import json
import re
from datetime import datetime
from typing import Optional
import csv
from pathlib import Path

from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_google_genai import ChatGoogleGenerativeAI
from pydantic import BaseModel, Field, ValidationError

from models import (
    ConversationState,
    AppointmentContext,
    get_service_centers_by_city,
    find_city_from_text,
    AVAILABLE_TIME_SLOTS,
)


class IntentAnalysis(BaseModel):
    """Structured output for intent analysis."""

    intent: str = Field(
        description="The user's intent: 'booking', 'greeting', 'location', 'center_selection', 'time_selection', 'confirmation', 'other'"
    )
    city: Optional[str] = Field(
        default=None, description="Extracted city/location if mentioned"
    )
    time_preference: Optional[str] = Field(
        default=None, description="Extracted time preference if mentioned"
    )
    center_preference: Optional[str] = Field(
        default=None, description="Service center preference if mentioned"
    )
    confidence: float = Field(
        default=0.5, description="Confidence score between 0 and 1"
    )
    reasoning: Optional[str] = Field(
        default=None, description="Brief explanation of the analysis"
    )


def sanitize_llm_json_response(response: str) -> Optional[dict]:
    """
    Robust JSON sanitization for LLM responses.
    LLMs often return malformed JSON, so we need multiple fallback strategies.
    """
    if not response:
        return None

    # Strategy 1: Try direct JSON parsing
    try:
        return json.loads(response.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract JSON from markdown code blocks
    code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(code_block_pattern, response, re.DOTALL | re.IGNORECASE)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: Find JSON-like structure in text
    json_pattern = r"\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}"
    matches = re.findall(json_pattern, response, re.DOTALL)

    for match in matches:
        try:
            # Clean up common LLM JSON issues
            cleaned = match.strip()
            # Fix trailing commas
            cleaned = re.sub(r",\s*([}\]])", r"\1", cleaned)
            # Fix missing quotes around keys
            cleaned = re.sub(r"(\w+):\s*", r'"\1": ', cleaned)
            # Fix already quoted keys (avoid double quotes)
            cleaned = re.sub(r'"(\w+)"\s*:\s*', r'"\1": ', cleaned)

            return json.loads(cleaned)
        except json.JSONDecodeError:
            continue

    # Strategy 4: Extract individual fields using regex
    try:
        intent_match = re.search(
            r'"?intent"?\s*:\s*"?([^",\}]+)"?', response, re.IGNORECASE
        )
        city_match = re.search(
            r'"?city"?\s*:\s*"?([^",\}]+)"?', response, re.IGNORECASE
        )
        time_match = re.search(
            r'"?time_preference"?\s*:\s*"?([^",\}]+)"?', response, re.IGNORECASE
        )
        center_match = re.search(
            r'"?center_preference"?\s*:\s*"?([^",\}]+)"?', response, re.IGNORECASE
        )
        confidence_match = re.search(
            r'"?confidence"?\s*:\s*([0-9.]+)', response, re.IGNORECASE
        )

        extracted = {}
        if intent_match:
            extracted["intent"] = intent_match.group(1).strip().strip('"')
        if city_match and city_match.group(1).lower() not in ["null", "none", ""]:
            extracted["city"] = city_match.group(1).strip().strip('"')
        if time_match and time_match.group(1).lower() not in ["null", "none", ""]:
            extracted["time_preference"] = time_match.group(1).strip().strip('"')
        if center_match and center_match.group(1).lower() not in ["null", "none", ""]:
            extracted["center_preference"] = center_match.group(1).strip().strip('"')
        if confidence_match:
            try:
                extracted["confidence"] = float(confidence_match.group(1))
            except ValueError:
                extracted["confidence"] = 0.5

        if "intent" in extracted:
            return extracted

    except Exception:
        pass

    return None


class AppointmentBookingService:
    """Service class for handling appointment booking conversations."""

    def __init__(self, llm: ChatGoogleGenerativeAI):
        self.llm = llm
        self._setup_chains()

    def _setup_chains(self):
        """Initialize the LangChain chains for different conversation stages."""

        # Intent analysis chain - improved prompt for better JSON output
        intent_prompt = PromptTemplate(
            input_variables=[
                "message",
                "context",
                "conversation_history",
                "available_slots",
                "available_centers",
            ],
            template="""You are an expert appointment booking assistant analyzing user messages. Return ONLY valid JSON.

CONVERSATION CONTEXT:
- Current state: {context}
- Conversation history: {conversation_history}
- Available service centers: {available_centers}
- Available time slots: {available_slots}

USER MESSAGE: {message}

TASK: Analyze the user's message to understand their intent and extract relevant information.

Consider the entire conversation context when analyzing this message. Users often refer to previous information or use implicit references.

Determine the intent from these options:
- 'booking': User wants to book a service appointment
- 'greeting': User is greeting or starting conversation
- 'location': User is providing or asking about location information
- 'center_selection': User is selecting or asking about a service center
- 'time_selection': User is selecting or asking about a time slot
- 'confirmation': User is confirming or declining something
- 'other': None of the above

Extract any mentioned:
- City/location: Look for direct mentions or contextual references to cities
- Time preferences: Look for specific times, relative times (morning/afternoon/earliest), dates, or general preferences
- Service center preferences: Look for specific centers or descriptive references (downtown, north, etc.)

Return ONLY this JSON format (no other text):
{{
    "intent": "<intent>",
    "city": "<city_or_null>",
    "time_preference": "<time_or_null>",
    "center_preference": "<center_or_null>",
    "confidence": <number_between_0_and_1>,
    "reasoning": "<brief_explanation_of_your_analysis>"
}}""",
        )

        self.intent_chain = intent_prompt | self.llm | StrOutputParser()

        # Response generation chain
        response_prompt = PromptTemplate(
            input_variables=[
                "user_message",
                "intent",
                "context",
                "conversation_history",
                "available_slots",
                "available_centers",
            ],
            template="""You are a helpful appointment booking assistant for Lucid Motors.

CURRENT CONTEXT:
- Conversation state: {context}
- User's intent: {intent}
- Available service centers: {available_centers}
- Available time slots: {available_slots}
- Conversation history: {conversation_history}

USER MESSAGE: {user_message}

TASK: Generate a natural, helpful response that:
1. Directly addresses the user's intent and message
2. Maintains conversation context and flow
3. Guides the user through the appointment booking process
4. Handles ambiguity by asking clarifying questions
5. Confirms important details before finalizing

Your response should be conversational but concise. If the user's intent is unclear, ask for clarification.
If they've provided all necessary information for a step, move to the next step.
""",
        )

        self.response_chain = response_prompt | self.llm | StrOutputParser()

    def _format_conversation_history(self, context: AppointmentContext) -> str:
        """Format conversation history for LLM context."""
        # This would typically pull from context_manager, but for simplicity:
        history = f"User is in state: {context.state.value}"

        if context.city:
            history += f"\nUser has mentioned city: {context.city}"

        if context.selected_center:
            history += f"\nUser has selected center: {context.selected_center.name}"

        if context.selected_time_slot:
            history += f"\nUser has selected time: {context.selected_time_slot}"

        return history

    def _format_available_centers(self, city: Optional[str]) -> str:
        """Format available service centers for the given city."""
        if not city:
            return "No city selected yet."

        centers = get_service_centers_by_city(city)
        if not centers:
            return f"No service centers available in {city}."

        return "\n".join([f"- {center.name}: {center.address}" for center in centers])

    def analyze_intent(
        self, message: str, context: AppointmentContext
    ) -> IntentAnalysis:
        """Analyze user intent using LLM with robust JSON parsing."""
        try:
            context_str = f"State: {context.state}, City: {context.city}, Center: {context.selected_center}"
            response = self.intent_chain.invoke(
                {
                    "message": message,
                    "context": context_str,
                    "conversation_history": context_str,
                    "available_slots": self._format_time_slots(),
                    "available_centers": self._format_available_centers(context.city),
                }
            )

            # Use improved JSON sanitization
            json_data = sanitize_llm_json_response(response)

            if json_data:
                # Clean None/null values
                cleaned_data = {}
                for key, value in json_data.items():
                    if value and str(value).lower() not in ["null", "none", ""]:
                        cleaned_data[key] = value

                try:
                    return IntentAnalysis(**cleaned_data)
                except ValidationError as e:
                    print(f"Validation error creating IntentAnalysis: {e}")

        except Exception as e:
            print(f"Error analyzing intent: {e}")

        # Fallback to simple keyword matching
        return self._fallback_intent_analysis(message, context)

    def _fallback_intent_analysis(
        self, message: str, context: AppointmentContext
    ) -> IntentAnalysis:
        """Fallback intent analysis using simple keyword matching."""
        message_lower = message.lower()

        # Check for booking keywords
        booking_keywords = [
            "book",
            "schedule",
            "appointment",
            "service",
            "servicing",
            "check-up",
            "maintenance",
        ]
        if any(keyword in message_lower for keyword in booking_keywords):
            city = find_city_from_text(message)
            return IntentAnalysis(intent="booking", city=city, confidence=0.8)

        # Check for greeting
        greeting_keywords = ["hello", "hi", "hey", "good morning", "good afternoon"]
        if any(keyword in message_lower for keyword in greeting_keywords):
            return IntentAnalysis(intent="greeting", confidence=0.9)

        # Check for location
        city = find_city_from_text(message)
        if city or context.state == ConversationState.WAITING_LOCATION:
            return IntentAnalysis(intent="location", city=city, confidence=0.7)

        # Check for time selection
        time_keywords = ["am", "pm", "morning", "afternoon", "evening"]
        if (
            any(keyword in message_lower for keyword in time_keywords)
            or context.state == ConversationState.WAITING_TIME_SLOT
        ):
            return IntentAnalysis(
                intent="time_selection", time_preference=message, confidence=0.7
            )

        return IntentAnalysis(intent="other", confidence=0.5)

    def generate_response(
        self, user_message: str, context: AppointmentContext, intent: IntentAnalysis
    ) -> str:
        """Generate appropriate response based on intent and context."""

        # If booking is done, skip LLM and send final confirmation
        if (
            context.state == ConversationState.COMPLETED
            and context.selected_center
            and context.selected_time_slot
        ):
            return self._generate_confirmation(context)

        # Prepare context for the prompt
        conversation_history = self._format_conversation_history(context)
        available_slots = self._format_time_slots()
        available_centers = self._format_available_centers(context.city)

        # Invoke the LLM chain
        response = self.response_chain.invoke(
            {
                "user_message": user_message,
                "intent": intent.model_dump_json(),
                "context": context.model_dump_json(),
                "conversation_history": conversation_history,
                "available_slots": available_slots,
                "available_centers": available_centers,
            }
        )

        return response

    def _handle_greeting(self) -> str:
        return (
            "Hello! Welcome to Lucid Motors service booking. "
            "I'm here to help you schedule a service appointment for your vehicle. "
            "How can I assist you today?"
        )

    def _handle_booking_request(
        self, intent: IntentAnalysis, context: AppointmentContext
    ) -> str:
        """Handle initial booking request."""
        if intent.city:
            context.city = intent.city
            return self._handle_location(intent, context)
        else:
            context.state = ConversationState.WAITING_LOCATION
            return "I'd be happy to help you book a service appointment! Could you tell me which city you're in?"

    def _handle_location(
        self, intent: IntentAnalysis, context: AppointmentContext
    ) -> str:
        """Handle location/city selection."""
        city = intent.city or context.city
        if not city:
            return "Could you please specify which city you'd like to book the appointment in?"

        centers = get_service_centers_by_city(city)
        if not centers:
            from models import SERVICE_CENTERS

            available_cities = list(
                {
                    center.city
                    for centers in SERVICE_CENTERS.values()
                    for center in centers
                }
            )
            return f"I'm sorry, we don't have a service center in {city}. We have centers in: {', '.join(available_cities)}. Which city works for you?"

        context.city = city
        context.state = ConversationState.WAITING_CENTER_SELECTION

        if len(centers) == 1:
            context.selected_center = centers[0]
            context.state = ConversationState.WAITING_TIME_SLOT
            return f"Great! We have {centers[0]} available. Here are the available time slots: {self._format_time_slots()}. What time works best for you?"
        else:
            center_list = "\n".join([f"• {center}" for center in centers])
            return f"We have the following service centers in {city}:\n{center_list}\n\nWhich one would you prefer?"

    def _handle_center_selection(
        self, user_message: str, context: AppointmentContext
    ) -> str:
        """Handle service center selection."""
        if not context.city:
            return "Please first let me know which city you're in."

        centers = get_service_centers_by_city(context.city)
        message_lower = user_message.lower()

        # Find matching center
        selected_center = None
        for center in centers:
            if any(word in message_lower for word in center.name.lower().split()):
                selected_center = center
                break
            elif "downtown" in message_lower and "downtown" in center.name.lower():
                selected_center = center
                break
            elif "north" in message_lower and "north" in center.name.lower():
                selected_center = center
                break

        if not selected_center and centers:
            selected_center = centers[0]  # Default to first center

        if selected_center:
            context.selected_center = selected_center
            context.state = ConversationState.WAITING_TIME_SLOT
            return f"Perfect! I've selected {selected_center}. Here are the available time slots: {self._format_time_slots()}. What time works best for you?"

        return "Could you please specify which service center you'd prefer?"

    def _handle_time_selection(
        self, user_message: str, context: AppointmentContext
    ) -> str:
        """Handle time slot selection."""
        message_lower = user_message.lower()

        # Find matching time slot
        selected_slot = None
        for slot in AVAILABLE_TIME_SLOTS:
            if slot.time.lower() in message_lower:
                selected_slot = slot
                break
            elif any(word in slot.time.lower() for word in message_lower.split()):
                selected_slot = slot
                break

        if selected_slot:
            context.selected_time_slot = selected_slot
            context.state = ConversationState.COMPLETED
            return self._generate_confirmation(context)

        return f"I didn't catch that time preference. Here are the available slots: {self._format_time_slots()}. Which one would you like?"

    def _handle_confirmation(self, context: AppointmentContext) -> str:
        """Handle appointment confirmation."""
        if context.selected_center and context.selected_time_slot:
            return self._generate_confirmation(context)
        return "I need more information to confirm your appointment. Let's start over with your city preference."

    def _handle_unknown(self, context: AppointmentContext) -> str:
        """Handle unknown/unclear messages."""
        if context.state == ConversationState.INITIAL:
            return "I can help you book a service appointment for your Lucid vehicle. Would you like to schedule one?"
        elif context.state == ConversationState.WAITING_LOCATION:
            return "Could you please tell me which city you'd like to book the appointment in?"
        elif context.state == ConversationState.WAITING_CENTER_SELECTION:
            centers = get_service_centers_by_city(context.city) if context.city else []
            if centers:
                center_list = ", ".join([center.name for center in centers])
                return f"Please choose from our available centers: {center_list}"
        elif context.state == ConversationState.WAITING_TIME_SLOT:
            return (
                f"Please select from these available times: {self._format_time_slots()}"
            )

        return (
            "I'm not sure I understood. Could you please clarify what you'd like to do?"
        )

    def _format_time_slots(self) -> str:
        """Format available time slots for display."""
        slots_by_date = {}
        for slot in AVAILABLE_TIME_SLOTS[:3]:  # Show first 3 slots
            if slot.date not in slots_by_date:
                slots_by_date[slot.date] = []
            slots_by_date[slot.date].append(slot.time)

        formatted = []
        for date, times in slots_by_date.items():
            formatted.append(f"{date}: {', '.join(times)}")

        return "; ".join(formatted)

    def _generate_confirmation(self, context: AppointmentContext) -> str:
        """Generate final confirmation message."""
        if not all([context.selected_center, context.selected_time_slot]):
            return "I couldn't complete your booking. Please try again."

        return (
            f"✅ Your service appointment is confirmed at {context.selected_center} "
            f"on {context.selected_time_slot}.\n\n"
            f"We'll send you a reminder before your appointment. "
            f"If you need to reschedule, please call {context.selected_center.phone}. "
            f"Thank you for choosing Lucid Motors and have a wonderful day!"
        )

    def update_context_state(
        self, context: AppointmentContext, intent: IntentAnalysis
    ) -> None:
        """Update context state based on intent analysis."""
        if intent.city and not context.city:
            context.city = intent.city

        # Update selected center based on preference if provided
        if intent.center_preference and context.city:
            centers_in_city = get_service_centers_by_city(context.city)
            pref_lower = intent.center_preference.lower()
            for center in centers_in_city:
                if pref_lower in center.name.lower():
                    context.selected_center = center
                    break

        # Update selected time slot if a clear preference was extracted
        if intent.time_preference:
            pref_lower = intent.time_preference.lower()
            for slot in AVAILABLE_TIME_SLOTS:
                if slot.time.lower() in pref_lower or pref_lower in slot.time.lower():
                    context.selected_time_slot = slot
                    break

        # Advance conversation state machine
        if intent.intent == "greeting":
            # Stay in initial unless we already have city info
            if context.city and context.state == ConversationState.INITIAL:
                context.state = ConversationState.WAITING_CENTER_SELECTION

        elif intent.intent == "booking":
            if not context.city:
                context.state = ConversationState.WAITING_LOCATION
            elif not context.selected_center:
                context.state = ConversationState.WAITING_CENTER_SELECTION
            elif not context.selected_time_slot:
                context.state = ConversationState.WAITING_TIME_SLOT

        elif intent.intent == "location":
            # Location provided, next ask for center
            context.state = ConversationState.WAITING_CENTER_SELECTION

        elif intent.intent == "center_selection":
            context.state = ConversationState.WAITING_TIME_SLOT

        elif intent.intent == "time_selection":
            if context.selected_center:
                context.state = ConversationState.CONFIRMING_APPOINTMENT

        elif intent.intent == "confirmation":
            context.state = ConversationState.COMPLETED

        # Persist the appointment exactly once
        if (
            context.state == ConversationState.COMPLETED
            and context.selected_center
            and context.selected_time_slot
            and not context.appointment_saved
        ):
            self._record_appointment(context)
            context.appointment_saved = True

        # Ensure last_message_time is refreshed
        context.last_message_time = datetime.now()

    def _record_appointment(self, context: AppointmentContext) -> None:
        """Append a confirmed appointment to appointments.csv"""
        appointments_file = Path("appointments.csv")

        # Prepare row
        row = {
            "user_id": context.user_id,
            "city": context.city or "",
            "center": str(context.selected_center) if context.selected_center else "",
            "date": (
                context.selected_time_slot.date if context.selected_time_slot else ""
            ),
            "time": (
                context.selected_time_slot.time if context.selected_time_slot else ""
            ),
            "booking_timestamp": datetime.now().isoformat(timespec="seconds"),
        }

        write_header = not appointments_file.exists()
        try:
            with appointments_file.open("a", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=row.keys())
                if write_header:
                    writer.writeheader()
                writer.writerow(row)
        except Exception as e:
            print(f"Error saving appointment to CSV: {e}")
