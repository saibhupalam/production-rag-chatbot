import pytest
from unittest.mock import patch, MagicMock
from io import BytesIO


def test_health_check_endpoint(client):
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "database" in data
    assert "vector_store" in data


def test_auth_registration_and_login(client):
    # Register new user
    reg_res = client.post(
        "/api/v1/auth/register",
        json={"username": "bob", "email": "bob@example.com", "password": "securepassword"}
    )
    assert reg_res.status_code == 201
    assert reg_res.json()["username"] == "bob"

    # Login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "bob@example.com", "password": "securepassword"}
    )
    assert login_res.status_code == 200
    token_data = login_res.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Get Profile
    token = token_data["access_token"]
    me_res = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "bob@example.com"


def test_auth_login_invalid_credentials(client):
    res = client.post(
        "/api/v1/auth/login",
        json={"email_or_username": "nonexistent@example.com", "password": "badpassword"}
    )
    assert res.status_code == 401


def test_upload_invalid_file_extension(client):
    file_content = b"Binary content"
    files = {"file": ("malicious.exe", file_content, "application/octet-stream")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 400
    assert "Unsupported file type" in res.json()["detail"]


def test_upload_empty_file(client):
    files = {"file": ("empty.txt", b"", "text/plain")}
    res = client.post("/api/v1/upload", files=files)
    assert res.status_code == 400
    assert "empty" in res.json()["detail"].lower()


@patch("app.api.v1.endpoints.document.store_chunks")
@patch("app.api.v1.endpoints.document.generate_embeddings")
def test_upload_valid_document(mock_embed, mock_store, client, auth_headers):
    mock_embed.return_value = [[0.1] * 768]
    mock_store.return_value = 1

    content = b"Attention Is All You Need. Transformers introduce self-attention mechanisms."
    files = {"file": ("paper.txt", content, "text/plain")}
    res = client.post("/api/v1/upload", files=files, headers=auth_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["filename"] == "paper.txt"
    assert data["status"] == "processed"
    assert data["chunks"] >= 1


def test_conversations_api_lifecycle(client, auth_headers, test_document):
    # 1. Create conversation
    create_res = client.post(
        "/api/v1/conversations",
        json={"title": "Paper Chat", "document_id": test_document.id},
        headers=auth_headers
    )
    assert create_res.status_code == 201
    conv_id = create_res.json()["id"]

    # 2. List conversations
    list_res = client.get("/api/v1/conversations", headers=auth_headers)
    assert list_res.status_code == 200
    ids = [c["id"] for c in list_res.json()]
    assert conv_id in ids

    # 3. Get single conversation
    get_res = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert get_res.status_code == 200
    assert get_res.json()["title"] == "Paper Chat"

    # 4. Delete conversation
    del_res = client.delete(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # 5. Verify 404 after deletion
    not_found = client.get(f"/api/v1/conversations/{conv_id}", headers=auth_headers)
    assert not_found.status_code == 404


def test_conversation_authorization_isolation(client, auth_headers, other_user_headers, test_document):
    # test_user creates a conversation
    create_res = client.post(
        "/api/v1/conversations",
        json={"title": "Private Chat", "document_id": test_document.id},
        headers=auth_headers
    )
    conv_id = create_res.json()["id"]

    # second_user tries to access test_user's conversation -> blocked with 403 Forbidden
    forbidden_res = client.get(f"/api/v1/conversations/{conv_id}", headers=other_user_headers)
    assert forbidden_res.status_code == 403

    # second_user tries to delete test_user's conversation -> blocked with 403 Forbidden
    del_forbidden = client.delete(f"/api/v1/conversations/{conv_id}", headers=other_user_headers)
    assert del_forbidden.status_code == 403


@patch("app.api.v1.endpoints.chat.answer_question")
def test_chat_endpoint_success(mock_answer, client, auth_headers, test_conversation):
    mock_answer.return_value = "The Transformer uses self-attention."

    res = client.post(
        "/api/v1/chat",
        json={"conversation_id": test_conversation.id, "question": "What is Transformer?"},
        headers=auth_headers
    )
    assert res.status_code == 200
    assert res.json()["answer"] == "The Transformer uses self-attention."


def test_chat_missing_conversation_404(client, auth_headers):
    res = client.post(
        "/api/v1/chat",
        json={"conversation_id": 99999, "question": "What is self attention?"},
        headers=auth_headers
    )
    assert res.status_code == 404
