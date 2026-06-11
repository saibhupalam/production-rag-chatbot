import requests

BASE_URL = "http://localhost:8000"


def upload_document(file):

    files = {
        "file": (
            file.name,
            file,
            file.type
        )
    }

    response = requests.post(
        f"{BASE_URL}/upload",
        files=files
    )

    return response.json()


def create_conversation(
    title,
    user_id,
    document_id
):

    response = requests.post(
        f"{BASE_URL}/conversations",
        json={
            "title": title,
            "user_id": user_id,
            "document_id": document_id
        }
    )

    return response.json()


def send_message(
    conversation_id,
    question
):

    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "conversation_id": conversation_id,
            "question": question
        }
    )

    return response.json()