
from collections import defaultdict
from threading import Lock
from langchain_core.messages import HumanMessage, AIMessage


class ShortTermMemory:
    def __init__(self, max_turns=10):
        self.max_turns = max_turns
        self.sessions = defaultdict(list)
        self.lock = Lock()

    def get_history(self, session_id):
        with self.lock:
            return list(self.sessions.get(session_id, []))

    def save_turn(self, session_id, user_message, ai_response):
        with self.lock:
            history = self.sessions[session_id]
            history.append(HumanMessage(content=user_message))
            history.append(AIMessage(content=ai_response))
            self.sessions[session_id] = history[-self.max_turns * 2:]

    def clear_history(self, session_id):
        with self.lock:
            self.sessions.pop(session_id, None)


short_term_memory = ShortTermMemory()
