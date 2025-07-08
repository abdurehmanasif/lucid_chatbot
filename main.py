import os
from dotenv import load_dotenv
import logging
from flask import Flask, request, jsonify

from chatbot import get_chatbot

# Load environment variables from .env if present
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)


# Health check endpoint
@app.route("/", methods=["GET"])
def health_check():
    """Health check endpoint."""
    return (
        jsonify(
            {
                "status": "healthy",
                "service": "Lucid Motors Appointment Booking Bot",
                "version": "2.0.0",
            }
        ),
        200,
    )


@app.route("/twilio", methods=["POST"])
def handle_twilio_webhook():
    """Handle incoming WhatsApp messages from Twilio webhook."""
    try:
        # Extract message data from Twilio webhook
        user_message = request.values.get("Body", "").strip()
        sender_id = request.values.get("From", "")

        if not user_message or not sender_id:
            logger.warning("Received webhook without message body or sender ID")
            return jsonify({"error": "Missing required fields"}), 400

        logger.info(f"Received message from {sender_id}: {user_message}")

        # Get chatbot instance and process message
        chatbot = get_chatbot()
        response = chatbot.process_message(user_message, sender_id)

        # Send response back via WhatsApp
        success = chatbot.send_whatsapp_message(sender_id, response)

        if success:
            logger.info(f"Successfully sent response to {sender_id}")
            return jsonify({"status": "success", "message": "Response sent"}), 200
        else:
            logger.error(f"Failed to send response to {sender_id}")
            return (
                jsonify({"status": "error", "message": "Failed to send response"}),
                500,
            )

    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return jsonify({"status": "error", "message": "Internal server error"}), 500


@app.route("/chat", methods=["POST"])
def handle_chat_api():
    """Handle chat messages via REST API (for testing/integration)."""
    try:
        data = request.get_json()

        if not data or "message" not in data or "user_id" not in data:
            return jsonify({"error": "Missing required fields: message, user_id"}), 400

        user_message = data["message"].strip()
        user_id = data["user_id"]

        if not user_message or not user_id:
            return jsonify({"error": "Message and user_id cannot be empty"}), 400

        # Process message with chatbot
        chatbot = get_chatbot()
        response = chatbot.process_message(user_message, user_id)

        # Get context summary for debugging
        context_summary = chatbot.get_user_context_summary(user_id)

        return (
            jsonify(
                {"response": response, "context": context_summary, "user_id": user_id}
            ),
            200,
        )

    except Exception as e:
        logger.error(f"Error processing chat API request: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/reset/<user_id>", methods=["POST"])
def reset_conversation(user_id: str):
    """Reset conversation context for a specific user."""
    try:
        chatbot = get_chatbot()
        response = chatbot.reset_conversation(user_id)

        return jsonify({"message": response, "user_id": user_id}), 200

    except Exception as e:
        logger.error(f"Error resetting conversation for {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/context/<user_id>", methods=["GET"])
def get_user_context(user_id: str):
    """Get conversation context summary for a specific user."""
    try:
        chatbot = get_chatbot()
        context_summary = chatbot.get_user_context_summary(user_id)

        return jsonify({"context": context_summary, "user_id": user_id}), 200

    except Exception as e:
        logger.error(f"Error getting context for {user_id}: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.route("/cleanup", methods=["POST"])
def cleanup_old_data():
    """Clean up old conversation data (admin endpoint)."""
    try:
        days = request.json.get("days", 7) if request.json else 7

        chatbot = get_chatbot()
        chatbot.cleanup_old_data(days)

        return jsonify({"message": f"Cleaned up data older than {days} days"}), 200

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return jsonify({"error": "Internal server error"}), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({"error": "Endpoint not found"}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {error}")
    return jsonify({"error": "Internal server error"}), 500


if __name__ == "__main__":
    # Validate required environment variables
    required_env_vars = ["GOOGLE_API_KEY", "TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]

    if missing_vars:
        logger.error(f"Missing required environment variables: {missing_vars}")
        exit(1)

    # Initialize chatbot on startup
    try:
        chatbot = get_chatbot()
        logger.info("Chatbot initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize chatbot: {e}")
        exit(1)

    # Run Flask app
    app.run(
        debug=False,  # Set to False for production
        host="0.0.0.0",
        port=int(os.getenv("PORT", 5000)),
    )
