from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ConversationState(str, Enum):
    """Enumeration of conversation states for the appointment booking flow."""

    INITIAL = "initial"
    WAITING_LOCATION = "waiting_location"
    WAITING_CENTER_SELECTION = "waiting_center_selection"
    WAITING_TIME_SLOT = "waiting_time_slot"
    CONFIRMING_APPOINTMENT = "confirming_appointment"
    COMPLETED = "completed"


class ServiceCenter(BaseModel):
    """Model representing a Lucid service center."""

    name: str
    city: str
    address: str
    phone: str

    def __str__(self) -> str:
        return f"Lucid Service Center - {self.city}"


class TimeSlot(BaseModel):
    """Model representing an available appointment time slot."""

    time: str = Field(..., description="Time in format like '10 AM', '2 PM'")
    date: str = Field(..., description="Date in format 'July 17th'")
    available: bool = True

    def __str__(self) -> str:
        return f"{self.date} at {self.time}"


class AppointmentContext(BaseModel):
    """Model for tracking appointment booking context across conversation turns."""

    user_id: str
    state: ConversationState = ConversationState.INITIAL
    city: Optional[str] = None
    selected_center: Optional[ServiceCenter] = None
    selected_time_slot: Optional[TimeSlot] = None
    appointment_saved: bool = False
    last_message_time: datetime = Field(default_factory=datetime.now)

    class Config:
        arbitrary_types_allowed = True


class ConversationHistory(BaseModel):
    """Model for storing conversation history entries."""

    timestamp: datetime
    user_message: str
    bot_response: str
    context: Optional[Dict[str, Any]] = None


# Static data for service centers
SERVICE_CENTERS: Dict[str, List[ServiceCenter]] = {
    "riyadh": [
        ServiceCenter(
            name="Lucid Service Center - Riyadh Downtown",
            city="Riyadh",
            address="King Fahd Road, Riyadh 12345",
            phone="+966-11-123-4567",
        ),
        ServiceCenter(
            name="Lucid Service Center - Riyadh North",
            city="Riyadh",
            address="Olaya Street, Riyadh 12346",
            phone="+966-11-123-4568",
        ),
        ServiceCenter(
            name="Lucid Service Center - Riyadh East",
            city="Riyadh",
            address="King Abdullah Road, Riyadh 12347",
            phone="+966-11-123-4569",
        ),
    ],
    "jeddah": [
        ServiceCenter(
            name="Lucid Service Center - Jeddah",
            city="Jeddah",
            address="Tahlia Street, Jeddah 21414",
            phone="+966-12-234-5678",
        ),
        ServiceCenter(
            name="Lucid Service Center - Jeddah North",
            city="Jeddah",
            address="King Abdulaziz Road, Jeddah 21415",
            phone="+966-12-234-5679",
        ),
    ],
    "dammam": [
        ServiceCenter(
            name="Lucid Service Center - Dammam",
            city="Dammam",
            address="King Saud Road, Dammam 31411",
            phone="+966-13-345-6789",
        ),
        ServiceCenter(
            name="Lucid Service Center - Dammam West",
            city="Dammam",
            address="King Fahd Road, Dammam 31412",
            phone="+966-13-345-6790",
        ),
    ],
    "makkah": [
        ServiceCenter(
            name="Lucid Service Center - Makkah",
            city="Makkah",
            address="King Abdulaziz Road, Makkah 21955",
            phone="+966-12-345-6789",
        ),
    ],
    "medina": [
        ServiceCenter(
            name="Lucid Service Center - Medina",
            city="Medina",
            address="King Fahd Road, Medina 42351",
            phone="+966-14-456-7890",
        ),
    ],
    "taif": [
        ServiceCenter(
            name="Lucid Service Center - Taif",
            city="Taif",
            address="King Khalid Road, Taif 21944",
            phone="+966-12-567-8901",
        ),
    ],
    "abha": [
        ServiceCenter(
            name="Lucid Service Center - Abha",
            city="Abha",
            address="King Faisal Road, Abha 61321",
            phone="+966-17-678-9012",
        ),
    ],
    "tabuk": [
        ServiceCenter(
            name="Lucid Service Center - Tabuk",
            city="Tabuk",
            address="King Abdulaziz Road, Tabuk 71491",
            phone="+966-14-789-0123",
        ),
    ],
    "jazan": [
        ServiceCenter(
            name="Lucid Service Center - Jazan",
            city="Jazan",
            address="King Fahd Road, Jazan 45142",
            phone="+966-17-890-1234",
        ),
    ],
    "hail": [
        ServiceCenter(
            name="Lucid Service Center - Hail",
            city="Hail",
            address="King Khalid Road, Hail 81451",
            phone="+966-16-901-2345",
        ),
    ],
    "al-ahsa": [
        ServiceCenter(
            name="Lucid Service Center - Al-Ahsa",
            city="Al-Ahsa",
            address="King Fahd Road, Al-Ahsa 31982",
            phone="+966-13-012-3456",
        ),
    ],
    "khamis-mushait": [
        ServiceCenter(
            name="Lucid Service Center - Khamis Mushait",
            city="Khamis Mushait",
            address="King Abdullah Road, Khamis Mushait 61961",
            phone="+966-17-123-4567",
        ),
    ],
}

# Static time slots (in a real system, this would be dynamic)
AVAILABLE_TIME_SLOTS = [
    TimeSlot(time="9 AM", date="July 17th"),
    TimeSlot(time="10 AM", date="July 17th"),
    TimeSlot(time="11 AM", date="July 17th"),
    TimeSlot(time="12 PM", date="July 17th"),
    TimeSlot(time="1 PM", date="July 17th"),
    TimeSlot(time="2 PM", date="July 17th"),
    TimeSlot(time="3 PM", date="July 17th"),
    TimeSlot(time="4 PM", date="July 17th"),
    TimeSlot(time="5 PM", date="July 17th"),
    TimeSlot(time="9 AM", date="July 18th"),
    TimeSlot(time="10 AM", date="July 18th"),
    TimeSlot(time="11 AM", date="July 18th"),
    TimeSlot(time="12 PM", date="July 18th"),
    TimeSlot(time="1 PM", date="July 18th"),
    TimeSlot(time="2 PM", date="July 18th"),
    TimeSlot(time="3 PM", date="July 18th"),
    TimeSlot(time="4 PM", date="July 18th"),
    TimeSlot(time="5 PM", date="July 18th"),
    TimeSlot(time="9 AM", date="July 19th"),
    TimeSlot(time="10 AM", date="July 19th"),
    TimeSlot(time="11 AM", date="July 19th"),
    TimeSlot(time="12 PM", date="July 19th"),
    TimeSlot(time="1 PM", date="July 19th"),
    TimeSlot(time="2 PM", date="July 19th"),
    TimeSlot(time="3 PM", date="July 19th"),
    TimeSlot(time="4 PM", date="July 19th"),
    TimeSlot(time="5 PM", date="July 19th"),
    TimeSlot(time="9 AM", date="July 20th"),
    TimeSlot(time="10 AM", date="July 20th"),
    TimeSlot(time="11 AM", date="July 20th"),
    TimeSlot(time="12 PM", date="July 20th"),
    TimeSlot(time="1 PM", date="July 20th"),
    TimeSlot(time="2 PM", date="July 20th"),
    TimeSlot(time="3 PM", date="July 20th"),
    TimeSlot(time="4 PM", date="July 20th"),
    TimeSlot(time="5 PM", date="July 20th"),
]

# Static time slots (in a real system, this would be dynamic)
AVAILABLE_TIME_SLOTS = [
    TimeSlot(time="10 AM", date="July 17th"),
    TimeSlot(time="11 AM", date="July 17th"),
    TimeSlot(time="2 PM", date="July 17th"),
    TimeSlot(time="3 PM", date="July 17th"),
    TimeSlot(time="10 AM", date="July 18th"),
    TimeSlot(time="1 PM", date="July 18th"),
    TimeSlot(time="4 PM", date="July 18th"),
]


def get_service_centers_by_city(city: str) -> List[ServiceCenter]:
    """Get service centers for a given city (case-insensitive)."""
    return SERVICE_CENTERS.get(city.lower(), [])


def find_city_from_text(text: str) -> Optional[str]:
    """Extract city name from user text using fuzzy matching."""
    text_lower = text.lower()
    for city in SERVICE_CENTERS.keys():
        if city in text_lower:
            return city.title()
