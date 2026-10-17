import pytest
from unittest.mock import patch, MagicMock
from app.services.conversation_service import (
    create_conversation,
    get_conversation,
    get_all_conversations,
    delete_conversation
)
from app.services.message_service import create_message, get_conversation_messages
from app.services.rag_service import answer_question


def test_conversation_lifecycle(db_session, test_user, test_document):
    conv = create_conversation(
        db=db_session,
        title="Test Conversation",
        user_id=test_user.id,
        document_id=test_document.id
    )
    assert conv.id is not None
    assert conv.title == "Test Conversation"
    assert conv.user_id == test_user.id
    assert conv.document_id == test_document.id

    fetched = get_conversation(db_session, conv.id)
    assert fetched is not None
    assert fetched.id == conv.id

    # User scoping
    user_convs = get_all_conversations(db_session, user_id=test_user.id)
    assert len(user_convs) >= 1

    other_user_convs = get_all_conversations(db_session, user_id=999)
    assert len(other_user_convs) == 0


def test_message_persistence(db_session, test_conversation):
    msg1 = create_message(
        db=db_session,
        conversation_id=test_conversation.id,
        role="user",
        content="What is attention?"
    )
    msg2 = create_message(
        db=db_session,
        conversation_id=test_conversation.id,
        role="assistant",
        content="Attention connects tokens."
    )

    messages = get_conversation_messages(db_session, test_conversation.id)
    assert len(messages) == 2
    assert messages[0].role == "user"
    assert messages[0].content == "What is attention?"
    assert messages[1].role == "assistant"
    assert messages[1].content == "Attention connects tokens."


def test_missing_conversation_raises_value_error(db_session):
    with pytest.raises(ValueError, match="Conversation 99999 not found"):
        answer_question(
            db=db_session,
            question="Any question?",
            conversation_id=99999
        )


@patch("app.services.rag_service.llm")
@patch("app.services.rag_service.hybrid_search")
@patch("app.services.rag_service.rerank_candidates")
def test_answer_question_flow(mock_rerank, mock_search, mock_llm, db_session, test_conversation):
    mock_search.return_value = [
        {"id": "c1", "text": "Self-attention computes dot products.", "chunk_id": 0}
    ]
    mock_rerank.return_value = [
        {"id": "c1", "text": "Self-attention computes dot products.", "chunk_id": 0}
    ]
    mock_response = MagicMock()
    mock_response.content = "Self-attention connects all tokens via dot products."
    mock_llm.invoke.return_value = mock_response

    answer = answer_question(
        db=db_session,
        question="What does self-attention compute?",
        conversation_id=test_conversation.id,
        use_advanced_rag=True
    )

    assert "Self-attention" in answer
    # Verify messages saved to database
    msgs = get_conversation_messages(db_session, test_conversation.id)
    assert len(msgs) == 2
    assert msgs[0].role == "user"
    assert msgs[1].role == "assistant"
