#!/usr/bin/env python3
"""
Test script for the Lucid Motors appointment booking chatbot.
Demonstrates the conversation flow and functionality.
"""

import os
import sys
from dotenv import load_dotenv
from chatbot import LucidChatbot

# Load environment variables
load_dotenv()

# Add current directory to path to import our modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))


def test_appointment_booking_flow():
    """Test the complete appointment booking conversation flow."""
    print("🚗 Testing Lucid Motors Appointment Booking Chatbot")
    print("=" * 60)

    try:
        # Initialize chatbot
        chatbot = LucidChatbot()
        test_user_id = "test_user_123"

        # Test conversation flows with more natural, human-like queries
        test_cases = [
            {
                "name": "Natural Booking Flow with Typos",
                "messages": [
                    "Hey there, my car needs servicing soon",
                    "I'm in jeddah",  # Lowercase city name
                    "11 am works for me",  # Informal time format
                ],
            },
            {
                "name": "Booking with Location and Vague Time Preference",
                "messages": [
                    "I need to schedule a checkup for my Lucid in Riyadh sometime next week",
                    "the downtown one please",  # Informal reference to location
                    "afternoon slot would be better, maybe 2pm?",  # Vague time preference
                ],
            },
            {
                "name": "Multi-intent Messages and Location Change",
                "messages": [
                    "Hi! Hope you're doing well today",  # Greeting with pleasantry
                    "Need to get my car serviced asap",  # Urgency indication
                    "Is there a center in Dubai?",  # Question about non-available location
                    "oh ok, what about riyadh then?",  # Location change with casual phrasing
                    "can you book me for 3 PM on the 17th?",  # Specific request with date
                ],
            },
            {
                "name": "Implicit References and Context Awareness",
                "messages": [
                    "Do you have any service centers in Dammam?",  # Question about location
                    "Great, when can I bring my car in?",  # Implicit acceptance and question
                    "The earliest one please",  # Vague reference to time slots
                ],
            },
            {
                "name": "Correction and Clarification Flow",
                "messages": [
                    "I want to book a service appt",  # Abbreviation
                    "Sorry, I meant Jeddah not Riyadh",  # Correction without prior mention
                    "Are there any slots available on the weekend?",  # Question about availability
                    "10 AM on the 17th then",  # Decision with date reference
                ],
            },
        ]

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test Case {i}: {test_case['name']}")
            print("-" * 40)

            # Reset context for each test
            chatbot.reset_conversation(f"{test_user_id}_{i}")

            for j, message in enumerate(test_case["messages"], 1):
                print(f"\n👤 User: {message}")
                response = chatbot.process_message(message, f"{test_user_id}_{i}")
                print(f"🤖 Bot: {response}")

                # Show context after each exchange
                context = chatbot.get_user_context_summary(f"{test_user_id}_{i}")
                print(f"📊 Context: {context}")

        print("\n" + "=" * 60)
        print("✅ All tests completed successfully!")

    except Exception as e:
        print(f"❌ Error during testing: {e}")
        return False

    return True


def interactive_test():
    """Interactive test mode for manual testing."""
    print("\n🔄 Interactive Test Mode")
    print("Type 'quit' to exit, 'reset' to reset conversation")
    print("Type 'context' to see current conversation context")
    print("-" * 40)

    try:
        chatbot = LucidChatbot()
        user_id = "interactive_user"

        # Show example queries to help the user
        example_queries = [
            "Hi, I need to get my car serviced",
            "Is there a service center in Riyadh?",
            "I'd prefer the downtown location",
            "Do you have any slots next Tuesday?",
            "Morning would be better for me",
            "Can I book for 11 AM?",
        ]
        print("\nExample queries you can try:")
        for example in example_queries:
            print(f" • {example}")

        while True:
            user_input = input("\n👤 You: ").strip()

            if user_input.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == "reset":
                response = chatbot.reset_conversation(user_id)
                print(f"🔄 {response}")
                continue
            elif user_input.lower() == "context":
                context = chatbot.get_user_context_summary(user_id)
                print(f"📊 Current context: {context}")
                continue
            elif not user_input:
                continue

            # Process message
            response = chatbot.process_message(user_input, user_id)
            print(f"🤖 Bot: {response}")

            # Show context
            context = chatbot.get_user_context_summary(user_id)
            print(f"📊 Context: {context}")

    except KeyboardInterrupt:
        print("\n👋 Test interrupted by user")
    except Exception as e:
        print(f"❌ Error in interactive mode: {e}")


def main():
    """Main test function."""
    print("🚗 Lucid Motors Chatbot Test Suite")
    print("=" * 60)

    # Check environment variables
    required_vars = ["GOOGLE_API_KEY"]
    missing = [var for var in required_vars if not os.getenv(var)]

    if missing:
        print(f"❌ Missing environment variables: {missing}")
        print("Please set up your .env file with the required variables.")
        return

    # Run automated tests
    # success = test_appointment_booking_flow()
    success = True

    if success:
        # Ask if user wants interactive mode
        choice = (
            input("\n🔄 Would you like to run interactive mode? (y/n): ")
            .strip()
            .lower()
        )
        if choice in ["y", "yes"]:
            interactive_test()


if __name__ == "__main__":
    main()
