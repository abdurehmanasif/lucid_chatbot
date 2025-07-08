# Lucid Motors Appointment Booking Chatbot

A sophisticated WhatsApp chatbot for booking service appointments at Lucid Motors service centers. Built with modern LangChain v0.3, Flask, and natural language understanding capabilities.

## 🚗 Features

- **Natural Language Processing**: Understands conversational booking requests without menus or buttons
- **Context-Aware Conversations**: Maintains conversation state across multiple message exchanges
- **Multi-City Support**: Service centers in Riyadh, Jeddah, and Dammam
- **WhatsApp Integration**: Seamless integration via Twilio WhatsApp API
- **Intent Recognition**: Intelligent detection of user intents (booking, location, time selection, etc.)
- **Persistent Memory**: Conversation history and context stored locally
- **REST API**: Additional endpoints for testing and integration

## 🏗️ Architecture

The codebase follows modern software engineering principles:

- **Modular Design**: Clean separation of concerns across multiple modules
- **SOLID Principles**: Single responsibility, dependency injection, and extensible design
- **Type Safety**: Full type hints with Pydantic models
- **Error Handling**: Comprehensive error handling and logging
- **Clean Code**: PEP8 compliant, well-documented, and maintainable

### Core Components

```
📦 Lucid Chatbot/
├── 🤖 chatbot.py              # Main chatbot orchestrator
├── 🧠 appointment_service.py  # LangChain conversation logic
├── 💾 context_manager.py      # Conversation memory & persistence
├── 📊 models.py               # Pydantic data models
├── 🌐 main.py                 # Flask web server
├── 🧪 test_chatbot.py         # Test suite and interactive demo
├── 📋 requirements.txt        # Python dependencies
└── 📁 History/                # Conversation storage (auto-created)
```

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Gemini API key
- Twilio account with WhatsApp API access

### Installation

1. **Clone and setup**:
   ```bash
   git clone <repository-url>
   cd "Lucid Chatbot"
   pip install -r requirements.txt
   ```

2. **Configure environment variables** (`.env` file):
   ```env
   GOOGLE_API_KEY=your_google_gemini_api_key
   TWILIO_ACCOUNT_SID=your_twilio_account_sid
   TWILIO_AUTH_TOKEN=your_twilio_auth_token
   PORT=5000
   ```

3. **Run the application**:
   ```bash
   python main.py
   ```

### Testing

Run the test suite to see the chatbot in action:

```bash
python test_chatbot.py
```

This includes:
- Automated conversation flow tests
- Interactive chat mode for manual testing
- Context state visualization

## 💬 Conversation Flow

### Example Conversation

```
👤 User: Hey, I need to get my car serviced next week.
🤖 Bot: Happy to help! Could you tell me which city you're in?

👤 User: Jeddah.
🤖 Bot: Great! We have a Lucid Service Center in Jeddah. For July 17th, 
       available times are 10 AM, 11 AM, and 2 PM. Which do you prefer?

👤 User: 11 sounds good.
🤖 Bot: ✅ Your service appointment is confirmed at Lucid Service Center - Jeddah 
       on July 17th at 11 AM.
```

### Supported Intents

- **Booking**: "I want to book an appointment", "Schedule service"
- **Greeting**: "Hello", "Hi there"
- **Location**: "Riyadh", "I'm in Jeddah"
- **Center Selection**: "Downtown location", "The first one"
- **Time Selection**: "11 AM", "Morning works", "2 PM is perfect"
- **Confirmation**: Natural confirmations and follow-ups

## 🛠️ API Endpoints

### WhatsApp Webhook
```
POST /twilio
```
Handles incoming WhatsApp messages from Twilio.

### Chat API (Testing)
```
POST /chat
Content-Type: application/json

{
  "message": "I need to book an appointment",
  "user_id": "test_user_123"
}
```

### Context Management
```
GET /context/<user_id>          # Get conversation context
POST /reset/<user_id>           # Reset conversation
POST /cleanup                   # Clean old data (admin)
```

### Health Check
```
GET /                           # Service health status
```

## 🏢 Service Centers

Currently supports:

- **Riyadh**: Downtown and North locations
- **Jeddah**: Main service center
- **Dammam**: Main service center

Easy to extend with additional locations in `models.py`.

## 🧪 Development & Testing

### Running Tests
```bash
# Automated tests
python test_chatbot.py

# Interactive mode only
python -c "from test_chatbot import interactive_test; interactive_test()"
```

### Local Development
```bash
# Install development dependencies
pip install -r requirements.txt

# Run with debug mode
export FLASK_DEBUG=1
python main.py
```

### Adding New Service Centers

Edit `models.py`:
```python
SERVICE_CENTERS["new_city"] = [
    ServiceCenter(
        name="Lucid Service Center - New City",
        city="New City",
        address="123 Main St, New City 12345",
        phone="+966-xx-xxx-xxxx"
    )
]
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `GOOGLE_API_KEY` | Google Gemini API key | ✅ |
| `TWILIO_ACCOUNT_SID` | Twilio account identifier | ✅ |
| `TWILIO_AUTH_TOKEN` | Twilio authentication token | ✅ |
| `PORT` | Server port (default: 5000) | ❌ |

### Conversation Settings

- **Context Timeout**: 7 days (configurable in `context_manager.py`)
- **History Limit**: 50 recent conversations per user
- **Time Slots**: Static list (easily replaceable with dynamic API)

## 📊 Monitoring & Logging

- **Structured Logging**: All interactions logged with timestamps
- **Error Tracking**: Comprehensive exception handling
- **Context Debugging**: Real-time conversation state monitoring
- **Performance Metrics**: Response time tracking

## 🔒 Security & Privacy

- **Data Encryption**: Sensitive data stored securely
- **User Privacy**: Conversation data isolated by user ID
- **Input Validation**: All user inputs validated and sanitized
- **Rate Limiting**: Protection against abuse (implement as needed)

## 🚀 Deployment

### Production Setup

1. **Environment**: Set `debug=False` in `main.py`
2. **Reverse Proxy**: Use nginx or similar
3. **Process Manager**: Use gunicorn, uwsgi, or systemd
4. **SSL**: Enable HTTPS for Twilio webhooks
5. **Monitoring**: Set up application monitoring

### Example Gunicorn Command
```bash
gunicorn -w 4 -b 0.0.0.0:5000 main:app
```

## 📈 Future Enhancements

- [ ] Real-time calendar integration
- [ ] Multi-language support (Arabic, English)
- [ ] Voice message handling
- [ ] Appointment reminders
- [ ] Service history lookup
- [ ] Payment integration
- [ ] Admin dashboard
- [ ] Analytics and reporting

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Follow the existing code style and patterns
4. Add tests for new functionality
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For support or questions:
- Create an issue in the repository
- Contact the development team
- Check the test suite for usage examples

---

**Built with ❤️ for Lucid Motors** - Revolutionizing the electric vehicle service experience. 