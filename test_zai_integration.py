#!/usr/bin/env python3
"""
Test script for Z.AI integration
Tests the Z.AI LLM client implementation
"""

import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from common.zai_client import (
    ZAIClient,
    ZAIClientAdapter,
    create_zai_client,
    generate_with_zai
)


def test_client_creation():
    """Test that client can be created."""
    print("Testing Z.AI client creation...")
    
    # Test without API key (should raise ValueError)
    try:
        client = create_zai_client(api_key="", use_adapter=False)
        print("  ✗ Should have raised ValueError without API key")
        return False
    except ValueError:
        print("  ✓ Correctly raises ValueError without API key")
    
    # Test with dummy API key
    try:
        client = create_zai_client(api_key="test-key-12345", use_adapter=False)
        print("  ✓ Client created successfully with API key")
        print(f"    - Endpoint: {client.base_url}")
        print(f"    - Default model: {client.default_model}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create client: {e}")
        return False


def test_adapter_creation():
    """Test adapter creation."""
    print("\nTesting Z.AI adapter creation...")
    
    try:
        adapter = create_zai_client(
            api_key="test-key-12345",
            default_model="glm-4.7",
            use_adapter=True
        )
        print("  ✓ Adapter created successfully")
        print(f"    - Has generate method: {hasattr(adapter, 'generate')}")
        print(f"    - Has generate_batch method: {hasattr(adapter, 'generate_batch')}")
        return True
    except Exception as e:
        print(f"  ✗ Failed to create adapter: {e}")
        return False


def test_available_models():
    """Test getting available models."""
    print("\nTesting available models...")
    
    try:
        client = create_zai_client(api_key="test-key-12345", use_adapter=False)
        models = client.get_available_models()
        
        print(f"  ✓ Found {len(models)} available models:")
        for model in models:
            print(f"    - {model['id']}: {model['description']}")
        
        return len(models) > 0
    except Exception as e:
        print(f"  ✗ Failed to get models: {e}")
        return False


def test_model_info():
    """Test getting model info."""
    print("\nTesting model info...")
    
    try:
        client = create_zai_client(api_key="test-key-12345", use_adapter=False)
        
        # Test valid model
        info = client.get_model_info("glm-4.7")
        if info:
            print(f"  ✓ GLM-4.7 info retrieved:")
            print(f"    - Description: {info['description']}")
            print(f"    - Max tokens: {info['max_tokens']}")
            print(f"    - Cost per 1M tokens: ${info['input_cost_per_1m']}")
        
        # Test invalid model
        invalid = client.get_model_info("nonexistent-model")
        if invalid is None:
            print("  ✓ Returns None for invalid model")
        
        return True
    except Exception as e:
        print(f"  ✗ Failed to get model info: {e}")
        return False


def test_configuration_options():
    """Test different configuration options."""
    print("\nTesting configuration options...")
    
    try:
        # Test with Chinese endpoint
        client_cn = create_zai_client(
            api_key="test-key",
            base_url="https://open.bigmodel.cn/api/paas/v4/",
            default_model="glm-4.5",
            use_adapter=False
        )
        print(f"  ✓ Chinese endpoint configured: {client_cn.base_url}")
        print(f"    - Model: {client_cn.default_model}")
        
        # Test with different timeout
        client_timeout = create_zai_client(
            api_key="test-key",
            timeout=120,
            use_adapter=False
        )
        print(f"  ✓ Custom timeout: {client_timeout.timeout}s")
        
        return True
    except Exception as e:
        print(f"  ✗ Configuration test failed: {e}")
        return False


def test_integration_with_config():
    """Test integration with config system."""
    print("\nTesting integration with config system...")
    
    try:
        from config import get_settings
        
        settings = get_settings()
        
        # Check if Z.AI settings exist
        if hasattr(settings.llm, 'zai'):
            print("  ✓ Z.AI settings accessible via config")
            print(f"    - Enabled: {settings.llm.zai.enabled}")
            print(f"    - Default model: {settings.llm.zai.default_model}")
            print(f"    - Base URL: {settings.llm.zai.base_url}")
            return True
        else:
            print("  ✗ Z.AI settings not found in config")
            return False
            
    except Exception as e:
        print(f"  ✗ Config integration test failed: {e}")
        return False


def print_usage_example():
    """Print usage example."""
    print("\n" + "="*60)
    print("USAGE EXAMPLE")
    print("="*60)
    print("""
To use Z.AI in your config.yaml:

  llm:
    provider: "zai"
    
    zai:
      enabled: true
      api_key: "your-zai-api-key"  # Or set ZAI_API_KEY env var
      default_model: "glm-4.7"
    
    # Use zai/ prefix for stage models
    scene_breakdown_model: "zai/glm-4.7"
    character_extraction_model: "zai/glm-4.5"
    visual_adaptation_model: "zai/glm-4.7"
    panel_breakdown_model: "zai/glm-4.5-flash"
    storyboard_generation_model: "zai/glm-4.7"

Environment variable setup:
  export ZAI_API_KEY="your-api-key"

Get your API key from: https://docs.z.ai/guides/overview/quick-start
""")


def main():
    """Run all tests."""
    print("="*60)
    print("Z.AI INTEGRATION TEST SUITE")
    print("="*60)
    
    tests = [
        ("Client Creation", test_client_creation),
        ("Adapter Creation", test_adapter_creation),
        ("Available Models", test_available_models),
        ("Model Info", test_model_info),
        ("Configuration Options", test_configuration_options),
        ("Config Integration", test_integration_with_config),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n  ✗ Test crashed: {e}")
            results.append((test_name, False))
    
    # Print summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"  {status}: {test_name}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    # Print usage example
    print_usage_example()
    
    return passed == total


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
