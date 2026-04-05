#!/usr/bin/env python3
"""
Phase 2 E2E Integration Test
Tests all Phase 2 components together:
1. Conversation compaction
2. Session persistence (SessionStore save/load only — not the CLI / AgentLoop
   wiring; that is covered by pytest tests/test_session_agent_loop.py)
3. Git tools
4. Model router
5. Token counting
"""

import asyncio
from unittest.mock import AsyncMock
from pyopencode.config import load_config
from pyopencode.llm.client import LLMClient
from pyopencode.core.compaction import compact_conversation
from pyopencode.memory.session import SessionStore
from pyopencode.tools.git_tools import git_diff, git_log
from pyopencode.core.router import ModelRouter
from pyopencode.llm.token_counter import count_messages_tokens


async def test_compaction_flow():
    """Test conversation compaction with real config"""
    print("🧪 Test 1: Compaction Flow")

    config = load_config()

    # Create a long conversation
    messages = [{"role": "system", "content": "You are an AI assistant"}]
    for i in range(30):
        messages.append({"role": "user", "content": f"Question {i}"})
        messages.append({"role": "assistant", "content": f"Answer {i}"})

    print(f"   Created {len(messages)} messages")

    # Mock LLM for compaction
    mock_llm = AsyncMock(spec=LLMClient)
    mock_llm.chat.return_value = {"content": "Summary of conversation"}

    # Compact
    compacted = await compact_conversation(
        messages, mock_llm, summary_model="qwen-turbo", keep_recent=10
    )

    print(f"   Compacted to {len(compacted)} messages")
    assert len(compacted) < len(messages)
    assert compacted[0]["role"] == "system"
    print("   ✅ System message preserved")

    # Check summary message
    assert any("Summary" in str(msg.get("content", "")) for msg in compacted)
    print("   ✅ Summary message included")

    print("✅ Compaction flow test passed\n")


def test_session_persistence():
    """Test session save/load"""
    print("🧪 Test 2: Session Persistence")

    store = SessionStore()

    # Create test session
    session_id = "phase2_e2e_test"
    project_path = "/tmp/phase2_test"
    messages = [
        {"role": "system", "content": "test"},
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi"}
    ]

    # Save
    store.save(session_id, project_path, messages, "E2E test session")
    print("   ✅ Session saved")

    # Load
    loaded = store.load_latest(project_path)
    assert loaded == messages
    print("   ✅ Session loaded correctly")

    # List
    sessions = store.list_sessions(project_path)
    assert len(sessions) >= 1
    assert any(s["id"] == session_id for s in sessions)
    print(f"   ✅ Found session in list ({len(sessions)} total)")

    print("✅ Session persistence test passed\n")


def test_git_integration():
    """Test git tools"""
    print("🧪 Test 3: Git Integration")

    # Test git_diff
    diff = git_diff()
    print(f"   ✅ git_diff returned {len(diff)} chars")

    # Test git_log
    log = git_log(count=5)
    assert "fix: Security hardening" in log or len(log) > 0
    print("   ✅ git_log returned recent commits")

    # Test git_diff with specific file
    diff_specific = git_diff(file_path="pyopencode/config.py")
    print(f"   ✅ git_diff on specific file: {len(diff_specific)} chars")

    print("✅ Git integration test passed\n")


def test_model_router():
    """Test model routing logic"""
    print("🧪 Test 4: Model Router")

    config = load_config()
    router = ModelRouter(config)

    # Test all routing scenarios
    cheap = router.select(task_hint="compaction")
    fast = router.select(task_hint="subagent")
    long_ctx = router.select(token_count=150000)
    default = router.select()

    print(f"   Compaction → {cheap}")
    print(f"   Subagent → {fast}")
    print(f"   Long context → {long_ctx}")
    print(f"   Default → {default}")

    assert cheap == config["cheap_model"]
    assert fast == config["fast_model"]
    assert long_ctx == config["long_context_model"]
    assert default == config["strong_model"]

    print("✅ Model router test passed\n")


def test_token_counting():
    """Test token counting"""
    print("🧪 Test 5: Token Counting")

    messages = [
        {"role": "system", "content": "You are a helpful assistant"},
        {"role": "user", "content": "Hello, how are you?"},
        {"role": "assistant", "content": "I'm doing well, thank you!"}
    ]

    count = count_messages_tokens(messages)
    print(f"   Estimated tokens: {count}")
    assert count > 0
    assert count < 1000  # Should be reasonable for this small conversation

    print("✅ Token counting test passed\n")


async def test_full_integration():
    """Test complete Phase 2 flow"""
    print("🧪 Test 6: Full Phase 2 Integration")

    config = load_config()
    router = ModelRouter(config)

    # 1. Create conversation
    messages = [{"role": "system", "content": "AI assistant"}]
    for i in range(25):
        messages.append({"role": "user", "content": f"msg {i}"})
        messages.append({"role": "assistant", "content": f"response {i}"})

    print(f"   Step 1: Created {len(messages)} messages")

    # 2. Count tokens
    tokens = count_messages_tokens(messages)
    print(f"   Step 2: Counted {tokens} tokens")

    # 3. Select model based on token count
    model = router.select(token_count=tokens)
    print(f"   Step 3: Selected model: {model}")

    # 4. Compact if needed
    if len(messages) > 15:
        mock_llm = AsyncMock(spec=LLMClient)
        mock_llm.chat.return_value = {"content": "Conversation summary"}

        messages = await compact_conversation(
            messages, mock_llm,
            summary_model=router.select(task_hint="compaction"),
            keep_recent=5
        )
        print(f"   Step 4: Compacted to {len(messages)} messages")

    # 5. Save session
    store = SessionStore()
    store.save("integration_test", "/tmp/integration", messages, "Full integration test")
    print("   Step 5: Session saved")

    # 6. Git operations
    diff = git_diff()
    log = git_log(count=3)
    print(f"   Step 6: Git diff ({len(diff)} chars), log ({len(log)} chars)")

    print("✅ Full integration test passed\n")


async def main():
    print("=" * 60)
    print("Phase 2 E2E Integration Test Suite")
    print("=" * 60 + "\n")

    try:
        # Run all tests
        await test_compaction_flow()
        test_session_persistence()
        test_git_integration()
        test_model_router()
        test_token_counting()
        await test_full_integration()

        print("=" * 60)
        print("✅ ALL PHASE 2 TESTS PASSED!")
        print("=" * 60)

        return 0
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
