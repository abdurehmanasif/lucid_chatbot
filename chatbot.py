import os
import logging
from typing import Optional

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from twilio.rest import Client

from appointment_service import AppointmentBookingService
from context_manager import ContextManager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LucidChatbot:
    """Main chatbot service for Lucid Motors appointment booking."""

    def __init__(self):
        self._setup_clients()
        self._setup_services()

    def _setup_clients(self):
        """Initialize external service clients."""
        # Google AI client
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise EnvironmentError("GOOGLE_API_KEY environment variable is not set")

        self.llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=google_api_key,
        )

        # Twilio client
        account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        auth_token = os.getenv("TWILIO_AUTH_TOKEN")

        if not account_sid or not auth_token:
            logger.warning(
                "Twilio credentials not found. SMS functionality will be disabled."
            )
            self.twilio_client = None
        else:
            self.twilio_client = Client(account_sid, auth_token)

    def _setup_services(self):
        """Initialize internal services."""
        self.appointment_service = AppointmentBookingService(self.llm)
        self.context_manager = ContextManager()

    def process_message(self, user_message: str, user_id: str) -> str:
        """
        Process incoming user message and return bot response.

        Args:
            user_message: The message from the user
            user_id: Unique identifier for the user (e.g., WhatsApp number)

        Returns:
            Bot response string
        """
        try:
            logger.info(f"Processing message from {user_id}: {user_message}")

            # Get conversation context
            context = self.context_manager.get_context(user_id)

            # Analyze user intent
            intent = self.appointment_service.analyze_intent(user_message, context)
            logger.info(f"Detected intent: {intent.intent}, city: {intent.city}")

            # Update context first so that response generation has latest info
            self.appointment_service.update_context_state(context, intent)

            # Generate response based on updated context
            response = self.appointment_service.generate_response(
                user_message, context, intent
            )

            # Save conversation to history
            self.context_manager.save_conversation(user_id, user_message, response)

            logger.info(f"Generated response: {response}")
            return response

        except Exception as e:
            logger.error(f"Error processing message from {user_id}: {e}")
            return "I'm sorry, I encountered an error. Please try again or contact our support team."

    def send_whatsapp_message(self, to_number: str, message: str) -> bool:
        """
        Send WhatsApp message via Twilio.

        Args:
            to_number: Recipient phone number (should include whatsapp: prefix)
            message: Message to send

        Returns:
            True if message sent successfully, False otherwise
        """
        if not self.twilio_client:
            logger.error("Twilio client not configured")
            return False

        try:
            # Ensure proper WhatsApp format
            if not to_number.startswith("whatsapp:"):
                to_number = f"whatsapp:{to_number}"

            message_obj = self.twilio_client.messages.create(
                from_="whatsapp:+14155238886",  # Twilio WhatsApp sandbox number
                body=message,
                to=to_number,
            )

            logger.info(f"Message sent to {to_number}: {message_obj.sid}")
            return True

        except Exception as e:
            logger.error(f"Error sending WhatsApp message to {to_number}: {e}")
            return False

    def reset_conversation(self, user_id: str) -> str:
        """
        Reset conversation context for a user.

        Args:
            user_id: User identifier

        Returns:
            Confirmation message
        """
        self.context_manager.reset_context(user_id)
        return "Your conversation has been reset. How can I help you today?"

    def get_user_context_summary(self, user_id: str) -> str:
        """
        Get a summary of the user's current conversation context.

        Args:
            user_id: User identifier

        Returns:
            Context summary string
        """
        context = self.context_manager.get_context(user_id)

        summary_parts = [f"State: {context.state.value}"]

        if context.city:
            summary_parts.append(f"City: {context.city}")

        if context.selected_center:
            summary_parts.append(f"Center: {context.selected_center.name}")

        if context.selected_time_slot:
            summary_parts.append(f"Time: {context.selected_time_slot}")

        return " | ".join(summary_parts)

    def cleanup_old_data(self, days: int = 7) -> None:
        """Clean up old conversation contexts and histories."""
        self.context_manager.cleanup_old_contexts(days)
        logger.info(f"Cleaned up contexts older than {days} days")


# Global chatbot instance
chatbot: Optional[LucidChatbot] = None


def get_chatbot() -> LucidChatbot:
    """Get or create global chatbot instance."""
    global chatbot
    if chatbot is None:
        chatbot = LucidChatbot()
    return chatbot


def initialize_chatbot() -> LucidChatbot:
    """Initialize and return chatbot instance."""
    return LucidChatbot()
