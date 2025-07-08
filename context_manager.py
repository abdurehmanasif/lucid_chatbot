import json
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from pathlib import Path

from models import AppointmentContext, ConversationHistory, ConversationState


class ContextManager:
    """Manages conversation context and history for appointment booking."""

    def __init__(self, history_dir: str = "History"):
        self.history_dir = Path(history_dir)
        self.history_dir.mkdir(exist_ok=True)
        self._contexts: Dict[str, AppointmentContext] = {}

    def get_context(self, user_id: str) -> AppointmentContext:
        """Get or create conversation context for a user."""
        # Clean user_id (remove whatsapp: prefix if present)
        clean_user_id = user_id.split(":")[-1] if ":" in user_id else user_id

        if clean_user_id not in self._contexts:
            # Try to load from file
            context = self._load_context_from_file(clean_user_id)
            if context is None:
                # Create new context
                context = AppointmentContext(user_id=clean_user_id)
            self._contexts[clean_user_id] = context

        return self._contexts[clean_user_id]

    def update_context(self, user_id: str, **kwargs) -> None:
        """Update context fields for a user."""
        clean_user_id = user_id.split(":")[-1] if ":" in user_id else user_id
        context = self.get_context(clean_user_id)

        for key, value in kwargs.items():
            if hasattr(context, key):
                setattr(context, key, value)

        context.last_message_time = datetime.now()
        self._save_context_to_file(clean_user_id, context)

    def reset_context(self, user_id: str) -> None:
        """Reset conversation context for a user."""
        clean_user_id = user_id.split(":")[-1] if ":" in user_id else user_id
        context = AppointmentContext(user_id=clean_user_id)
        self._contexts[clean_user_id] = context
        self._save_context_to_file(clean_user_id, context)

    def save_conversation(
        self, user_id: str, user_message: str, bot_response: str
    ) -> None:
        """Save a conversation turn to history."""
        clean_user_id = user_id.split(":")[-1] if ":" in user_id else user_id

        history_entry = ConversationHistory(
            timestamp=datetime.now(),
            user_message=user_message,
            bot_response=bot_response,
            context=self._get_context_dict(clean_user_id),
        )

        self._append_to_history_file(clean_user_id, history_entry)

    def get_recent_history(
        self, user_id: str, limit: int = 3
    ) -> List[ConversationHistory]:
        """Get recent conversation history for a user."""
        clean_user_id = user_id.split(":")[-1] if ":" in user_id else user_id
        return self._load_recent_history(clean_user_id, limit)

    def cleanup_old_contexts(self, days: int = 7) -> None:
        """Remove contexts that haven't been active for specified days."""
        cutoff_date = datetime.now() - timedelta(days=days)

        to_remove = []
        for user_id, context in self._contexts.items():
            if context.last_message_time < cutoff_date:
                to_remove.append(user_id)

        for user_id in to_remove:
            del self._contexts[user_id]

    def _load_context_from_file(self, user_id: str) -> Optional[AppointmentContext]:
        """Load context from JSON file."""
        context_file = self.history_dir / f"{user_id}_context.json"

        if not context_file.exists():
            return None

        try:
            with open(context_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Convert string state back to enum
            if "state" in data:
                data["state"] = ConversationState(data["state"])

            # Convert datetime string back to datetime
            if "last_message_time" in data:
                data["last_message_time"] = datetime.fromisoformat(
                    data["last_message_time"]
                )

            return AppointmentContext(**data)

        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error loading context for {user_id}: {e}")
            return None

    def _save_context_to_file(self, user_id: str, context: AppointmentContext) -> None:
        """Save context to JSON file."""
        context_file = self.history_dir / f"{user_id}_context.json"

        try:
            # Convert context to dict for JSON serialization
            context_dict = context.dict()

            # Convert enum to string
            if "state" in context_dict:
                context_dict["state"] = context_dict["state"].value

            # Convert datetime to ISO string
            if "last_message_time" in context_dict:
                context_dict["last_message_time"] = context_dict[
                    "last_message_time"
                ].isoformat()

            # Handle nested objects
            if "selected_center" in context_dict and context_dict["selected_center"]:
                context_dict["selected_center"] = context_dict["selected_center"]

            if (
                "selected_time_slot" in context_dict
                and context_dict["selected_time_slot"]
            ):
                context_dict["selected_time_slot"] = context_dict["selected_time_slot"]

            with open(context_file, "w", encoding="utf-8") as f:
                json.dump(context_dict, f, indent=2, ensure_ascii=False)

        except Exception as e:
            print(f"Error saving context for {user_id}: {e}")

    def _get_context_dict(self, user_id: str) -> Dict:
        """Get context as dictionary for history storage."""
        context = self.get_context(user_id)
        context_dict = {
            "state": context.state.value,
            "city": context.city,
            "has_selected_center": context.selected_center is not None,
            "has_selected_time": context.selected_time_slot is not None,
        }
        return context_dict

    def _append_to_history_file(
        self, user_id: str, history_entry: ConversationHistory
    ) -> None:
        """Append conversation history entry to file."""
        history_file = self.history_dir / f"{user_id}_history.json"

        # Load existing history
        history_data = []
        if history_file.exists():
            try:
                with open(history_file, "r", encoding="utf-8") as f:
                    history_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                history_data = []

        # Convert history entry to dict
        entry_dict = {
            "timestamp": history_entry.timestamp.isoformat(),
            "user_message": history_entry.user_message,
            "bot_response": history_entry.bot_response,
            "context": history_entry.context,
        }

        # Append new entry
        history_data.append(entry_dict)

        # Keep only recent entries (last 50)
        if len(history_data) > 50:
            history_data = history_data[-50:]

        # Save back to file
        try:
            with open(history_file, "w", encoding="utf-8") as f:
                json.dump(history_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving history for {user_id}: {e}")

    def _load_recent_history(
        self, user_id: str, limit: int
    ) -> List[ConversationHistory]:
        """Load recent conversation history from file."""
        history_file = self.history_dir / f"{user_id}_history.json"

        if not history_file.exists():
            return []

        try:
            with open(history_file, "r", encoding="utf-8") as f:
                history_data = json.load(f)

            # Convert back to ConversationHistory objects
            recent_entries = []
            for entry in history_data[-limit:]:
                history_entry = ConversationHistory(
                    timestamp=datetime.fromisoformat(entry["timestamp"]),
                    user_message=entry["user_message"],
                    bot_response=entry["bot_response"],
                    context=entry.get("context"),
                )
                recent_entries.append(history_entry)

            return recent_entries

        except (json.JSONDecodeError, ValueError, KeyError) as e:
            print(f"Error loading history for {user_id}: {e}")
            return []
