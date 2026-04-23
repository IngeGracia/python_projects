from collections import deque


class SimpleMemory:
    def __init__(self, max_messages:int=10):
        # deque es una lista FIFO con un límite de elementos
        self.history = deque(maxlen=max_messages)

    def add_message(self, role:str, content:str):
        self.history.append({"role": role, "content": content})

    def get_messages(self):
        return list(self.history)