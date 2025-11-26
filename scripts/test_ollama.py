#!/usr/bin/env python3
"""
Test script for Ollama executor integration with LLMVM.

This script tests both conversation mode and tool calling with <helpers> blocks.

Prerequisites:
1. Ollama must be installed and running:
   - Install: https://ollama.ai/download
   - Run: `ollama serve`

2. A model must be pulled:
   - For tool calling: `ollama pull llama3.1` (or qwen2.5, mistral)
   - Check available models: `ollama list`

Usage:
    # Test conversation mode only
    python scripts/test_ollama.py --conversation

    # Test tool calling only
    python scripts/test_ollama.py --tools

    # Test both (default)
    python scripts/test_ollama.py

    # Use a specific model
    python scripts/test_ollama.py --model qwen2.5

    # Use a specific Ollama endpoint
    python scripts/test_ollama.py --endpoint http://192.168.1.100:11434/v1
"""

import argparse
import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from llmvm.common.ollama_executor import OllamaExecutor
from llmvm.common.objects import User, Assistant, System


def check_ollama_available(endpoint: str) -> bool:
    """Check if Ollama server is running and accessible."""
    import requests

    # Remove /v1 suffix for health check
    base_url = endpoint.replace('/v1', '')

    try:
        response = requests.get(f"{base_url}/api/tags", timeout=5)
        if response.status_code == 200:
            models = response.json().get('models', [])
            print(f"✓ Ollama is running at {base_url}")
            print(f"✓ Available models: {', '.join([m['name'] for m in models])}")
            return True
        else:
            print(f"✗ Ollama returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"✗ Cannot connect to Ollama at {base_url}: {e}")
        print("\nPlease ensure Ollama is running:")
        print("  1. Install Ollama: https://ollama.ai/download")
        print("  2. Run: ollama serve")
        print("  3. Pull a model: ollama pull llama3.1")
        return False


async def test_conversation_mode(executor: OllamaExecutor):
    """Test basic conversation mode without tool calling."""
    print("\n" + "="*60)
    print("Testing Conversation Mode")
    print("="*60)

    test_cases = [
        "Hello! What is your name?",
        "What is 2 + 2?",
        "Write a haiku about coding.",
    ]

    for i, query in enumerate(test_cases, 1):
        print(f"\n[Test {i}] Query: {query}")

        messages = [User(query)]

        try:
            response = await executor.aexecute(
                messages=messages,
                max_output_tokens=512,
                temperature=0.7,
            )

            print(f"Response: {response.get_str()}")
            print(f"✓ Test {i} passed")

        except Exception as e:
            print(f"✗ Test {i} failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    return True


async def test_tool_calling(executor: OllamaExecutor):
    """
    Test tool calling with <helpers> blocks.

    This tests LLMVM's unique approach where the model emits Python code
    in <helpers> blocks that gets executed by the server.
    """
    print("\n" + "="*60)
    print("Testing Tool Calling with <helpers> Blocks")
    print("="*60)

    # The system prompt that instructs the model to use <helpers> blocks
    # This is typically loaded from tool_call.prompt
    system_prompt = """You are a helpful assistant that can write Python code to solve problems.

When you need to use tools or perform calculations, write Python code inside <helpers> tags.
The code will be executed and the results will be provided back to you in <helpers_result> tags.

Available functions (simulated for this test):
- get_stock_price(ticker: str) -> float: Get current stock price
- get_gold_price_per_gram() -> float: Get current gold price per gram

Example:
User: What is the price of MSFT stock?
Assistant: Let me check the price of Microsoft stock.
<helpers>
price = get_stock_price("MSFT")
result(f"Microsoft stock price: ${price}")
</helpers>

Important: Always use <helpers> tags for function calls, not regular text.
"""

    # Test query from the README
    query = "I have 5 MSFT stocks and 10 NVDA stocks, what is my net worth in grams of gold?"

    print(f"\nQuery: {query}")
    print("\nNote: This test checks if the model can generate <helpers> blocks.")
    print("Full tool execution requires the LLMVM server to be running.\n")

    messages = [
        System(system_prompt),
        User(query)
    ]

    try:
        # Stream the response to see the <helpers> blocks as they're generated
        print("Response:")
        print("-" * 60)

        full_response = ""

        async def stream_handler(node):
            nonlocal full_response
            from llmvm.common.objects import TokenNode
            if isinstance(node, TokenNode):
                print(node.token, end='', flush=True)
                full_response += node.token

        response = await executor.aexecute(
            messages=messages,
            max_output_tokens=2048,
            temperature=0.3,  # Lower temperature for more deterministic code generation
            stream_handler=stream_handler,
        )

        print("\n" + "-" * 60)

        # Check if the response contains <helpers> blocks
        if '<helpers>' in full_response or '<code>' in full_response:
            print("\n✓ Model generated code blocks!")

            # Extract and display the code blocks
            if '<helpers>' in full_response:
                import re
                helpers_blocks = re.findall(r'<helpers>(.*?)</helpers>', full_response, re.DOTALL)
                print(f"\nFound {len(helpers_blocks)} <helpers> block(s):")
                for i, block in enumerate(helpers_blocks, 1):
                    print(f"\n--- Block {i} ---")
                    print(block.strip())
                    print("--- End Block ---")

            return True
        else:
            print("\n⚠ Model did not generate <helpers> blocks.")
            print("This may indicate:")
            print("  1. The model needs more specific prompting")
            print("  2. The model doesn't follow the instruction format well")
            print("  3. You may need to use a different model (try llama3.1 or qwen2.5)")
            return False

    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    parser = argparse.ArgumentParser(description='Test Ollama executor for LLMVM')
    parser.add_argument('--model', default='llama3.1',
                       help='Ollama model to use (default: llama3.1)')
    parser.add_argument('--endpoint', default='http://localhost:11434/v1',
                       help='Ollama API endpoint (default: http://localhost:11434/v1)')
    parser.add_argument('--conversation', action='store_true',
                       help='Test conversation mode only')
    parser.add_argument('--tools', action='store_true',
                       help='Test tool calling only')

    args = parser.parse_args()

    # If neither flag is specified, test both
    test_conversation = args.conversation or not args.tools
    test_tools = args.tools or not args.conversation

    print("LLMVM Ollama Executor Test Suite")
    print("=" * 60)
    print(f"Model: {args.model}")
    print(f"Endpoint: {args.endpoint}")

    # Check if Ollama is available
    if not check_ollama_available(args.endpoint):
        return 1

    # Create executor
    executor = OllamaExecutor(
        default_model=args.model,
        api_endpoint=args.endpoint,
    )

    results = []

    # Run tests
    if test_conversation:
        result = await test_conversation_mode(executor)
        results.append(("Conversation Mode", result))

    if test_tools:
        result = await test_tool_calling(executor)
        results.append(("Tool Calling", result))

    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)

    for name, result in results:
        status = "✓ PASSED" if result else "✗ FAILED"
        print(f"{name}: {status}")

    all_passed = all(r for _, r in results)

    if all_passed:
        print("\n✓ All tests passed!")
        return 0
    else:
        print("\n✗ Some tests failed. See details above.")
        return 1


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
