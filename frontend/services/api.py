import os
import requests
from typing import Optional, List, Dict, Any

# Configurable backend URL with /api/v1 prefix support
BACKEND_BASE_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
API_V1_PREFIX = "/api/v1"
API_URL = f"{BACKEND_BASE_URL}{API_V1_PREFIX}"
DEFAULT_TIMEOUT = int(os.getenv("API_TIMEOUT", "60"))


def _get_headers(token: Optional[str] = None) -> Dict[str, str]:
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def check_backend_health() -> Dict[str, Any]:
    """Check health of backend API."""
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            return {"healthy": True, "data": response.json()}
        return {"healthy": False, "error": f"Status {response.status_code}"}
    except Exception as e:
        return {"healthy": False, "error": str(e)}


def upload_document(file, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Upload a PDF or TXT file to the backend.
    """
    headers = _get_headers(token)
    files = {
        "file": (file.name, file.getvalue(), file.type or "application/octet-stream")
    }
    try:
        response = requests.post(
            f"{API_URL}/upload",
            files=files,
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            try:
                err_detail = response.json().get("detail", response.text)
            except Exception:
                err_detail = response.text
            return {"success": False, "error": f"Upload failed ({response.status_code}): {err_detail}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def create_conversation(
    title: str,
    document_id: int,
    user_id: Optional[int] = 1,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Create a new conversation associated with a document.
    """
    headers = _get_headers(token)
    payload = {
        "title": title,
        "user_id": user_id or 1,
        "document_id": document_id
    }
    try:
        response = requests.post(
            f"{API_URL}/conversations",
            json=payload,
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        else:
            try:
                err_detail = response.json().get("detail", response.text)
            except Exception:
                err_detail = response.text
            return {"success": False, "error": f"Failed ({response.status_code}): {err_detail}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def list_conversations(token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch all conversations for the user.
    """
    headers = _get_headers(token)
    try:
        response = requests.get(
            f"{API_URL}/conversations",
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Failed ({response.status_code}): {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def get_conversation(conversation_id: int, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch single conversation details.
    """
    headers = _get_headers(token)
    try:
        response = requests.get(
            f"{API_URL}/conversations/{conversation_id}",
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Failed ({response.status_code}): {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def get_conversation_messages(conversation_id: int, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Fetch messages history for a conversation.
    """
    headers = _get_headers(token)
    try:
        response = requests.get(
            f"{API_URL}/conversations/{conversation_id}/messages",
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Failed ({response.status_code}): {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def delete_conversation(conversation_id: int, token: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete a conversation and its messages.
    """
    headers = _get_headers(token)
    try:
        response = requests.delete(
            f"{API_URL}/conversations/{conversation_id}",
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": f"Failed ({response.status_code}): {response.text}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


def send_chat_message(
    conversation_id: int,
    question: str,
    token: Optional[str] = None
) -> Dict[str, Any]:
    """
    Send a question grounded in the conversation's document to the RAG chat endpoint.
    """
    headers = _get_headers(token)
    payload = {
        "conversation_id": conversation_id,
        "question": question
    }
    try:
        response = requests.post(
            f"{API_URL}/chat",
            json=payload,
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            try:
                err_detail = response.json().get("detail", response.text)
            except Exception:
                err_detail = response.text
            return {"success": False, "error": f"Chat error ({response.status_code}): {err_detail}"}
    except requests.RequestException as e:
        return {"success": False, "error": f"Connection error: {str(e)}"}


# Authentication endpoints for Phase 13 integration
def register_user(username: str, email: str, password: str) -> Dict[str, Any]:
    try:
        response = requests.post(
            f"{API_URL}/auth/register",
            json={"username": username, "email": email, "password": password},
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code in (200, 201):
            return {"success": True, "data": response.json()}
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            return {"success": False, "error": detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def login_user(email_or_username: str, password: str) -> Dict[str, Any]:
    try:
        response = requests.post(
            f"{API_URL}/auth/login",
            json={"email_or_username": email_or_username, "password": password},
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            try:
                detail = response.json().get("detail", response.text)
            except Exception:
                detail = response.text
            return {"success": False, "error": detail}
    except Exception as e:
        return {"success": False, "error": str(e)}


def get_current_user_profile(token: str) -> Dict[str, Any]:
    headers = _get_headers(token)
    try:
        response = requests.get(
            f"{API_URL}/auth/me",
            headers=headers,
            timeout=DEFAULT_TIMEOUT
        )
        if response.status_code == 200:
            return {"success": True, "data": response.json()}
        else:
            return {"success": False, "error": response.text}
    except Exception as e:
        return {"success": False, "error": str(e)}