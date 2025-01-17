from langchain.schema import HumanMessage, SystemMessage
from langchain_gigachat import GigaChat
from typing import Dict, List


class AIChatManager:
    def __init__(self, gigachat_credentials: str):
        self.giga = GigaChat(
            credentials=gigachat_credentials,
            model='GigaChat:latest',
            verify_ssl_certs=False
        )
        self.user_dialogs: Dict[int, List] = {}

    def start_new_dialog(self, user_id: int, system_message: str):
        self.user_dialogs[user_id] = [SystemMessage(content=system_message)]

    def get_ai_response(self, user_id: int, user_message: str) -> str:
        if user_id not in self.user_dialogs:
            raise ValueError("Диалог для данного пользователя не начат.")

        self.user_dialogs[user_id].append(HumanMessage(content=user_message))

        ai_response = self.giga.invoke(self.user_dialogs[user_id])

        self.user_dialogs[user_id].append(ai_response.content)

        return ai_response.content

    def end_dialog(self, user_id: int):
        if user_id in self.user_dialogs:
            del self.user_dialogs[user_id]