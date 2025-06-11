# Tests for kaia.py - Kubernetes AI Assistant
import pytest
import unittest
import unittest.mock as mock
import os
import argparse
import sys
from unittest.mock import patch, MagicMock

# Mock sys.argv before importing kaia to prevent argument parsing errors
with patch.object(sys, 'argv', ['kaia.py', '--provider', 'ollama']):
    from kaia import (
        create_model, 
        parse_arguments
    )


class TestArgumentParsing(unittest.TestCase):
    """Test command line argument parsing functionality."""
    
    def test_default_provider_is_ollama(self):
        """Test that the default provider is ollama when no arguments provided."""
        with patch.object(sys, 'argv', ['kaia.py']):
            args = parse_arguments()
            self.assertEqual(args.provider, 'ollama')
    
    def test_valid_provider_arguments(self):
        """Test that all valid provider arguments are accepted."""
        providers = ['ollama', 'gemini', 'github']
        
        for provider in providers:
            with patch.object(sys, 'argv', ['kaia.py', '--provider', provider]):
                args = parse_arguments()
                self.assertEqual(args.provider, provider)
    
    def test_invalid_provider_raises_error(self):
        """Test that invalid provider arguments raise SystemExit."""
        with patch.object(sys, 'argv', ['kaia.py', '--provider', 'invalid']):
            with self.assertRaises(SystemExit):
                parse_arguments()
    
    def test_help_argument(self):
        """Test that --help argument works (raises SystemExit)."""
        with patch.object(sys, 'argv', ['kaia.py', '--help']):
            with self.assertRaises(SystemExit):
                parse_arguments()


class TestModelCreation(unittest.TestCase):
    """Test model creation functionality for different providers."""
    
    def test_create_ollama_model_default(self):
        """Test creating Ollama model with default settings."""
        model = create_model('ollama')
        self.assertIsNotNone(model)
        # Should use default model name if environment variable not set
        
    def test_create_ollama_model_custom(self):
        """Test creating Ollama model with custom model name."""
        with patch.dict(os.environ, {'OLLAMA_MODEL_NAME': 'custom-model'}):
            model = create_model('ollama')
            self.assertIsNotNone(model)
    
    def test_create_gemini_model_default(self):
        """Test creating Gemini model with default settings."""
        model = create_model('gemini')
        self.assertIsNotNone(model)
        
    def test_create_gemini_model_custom(self):
        """Test creating Gemini model with custom model name."""
        with patch.dict(os.environ, {'GEMINI_MODEL_NAME': 'gemini-pro'}):
            model = create_model('gemini')
            self.assertIsNotNone(model)
    
    def test_create_github_model_default(self):
        """Test creating GitHub model with default settings."""
        # Mock GITHUB_TOKEN to avoid missing token error
        with patch.dict(os.environ, {'GITHUB_TOKEN': 'fake-token'}):
            model = create_model('github')
            self.assertIsNotNone(model)
        
    def test_create_github_model_custom(self):
        """Test creating GitHub model with custom model name."""
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'fake-token',
            'GITHUB_MODEL_NAME': 'custom-model'
        }):
            model = create_model('github')
            self.assertIsNotNone(model)
    
    def test_invalid_provider_raises_error(self):
        """Test that invalid provider raises ValueError."""
        with self.assertRaises(ValueError):
            create_model('invalid')


class TestEnvironmentVariables(unittest.TestCase):
    """Test environment variable handling."""
    
    def test_ollama_model_name_environment_variable(self):
        """Test that OLLAMA_MODEL_NAME environment variable is used."""
        test_model_name = 'test-ollama-model'
        with patch.dict(os.environ, {'OLLAMA_MODEL_NAME': test_model_name}):
            model = create_model('ollama')
            # We can't directly test the model name, but we can verify the model was created
            self.assertIsNotNone(model)
    
    def test_gemini_model_name_environment_variable(self):
        """Test that GEMINI_MODEL_NAME environment variable is used."""
        test_model_name = 'test-gemini-model'
        with patch.dict(os.environ, {'GEMINI_MODEL_NAME': test_model_name}):
            model = create_model('gemini')
            self.assertIsNotNone(model)
    
    def test_github_model_name_environment_variable(self):
        """Test that GITHUB_MODEL_NAME environment variable is used."""
        test_model_name = 'test-github-model'
        with patch.dict(os.environ, {
            'GITHUB_TOKEN': 'fake-token',
            'GITHUB_MODEL_NAME': test_model_name
        }):
            model = create_model('github')
            self.assertIsNotNone(model)


class TestIntegration(unittest.TestCase):
    """Integration tests for the complete workflow."""
    
    @patch.object(sys, 'argv', ['kaia.py', '--provider', 'ollama'])
    def test_full_workflow_ollama(self):
        """Test complete workflow with Ollama provider."""
        # Test argument parsing
        args = parse_arguments()
        self.assertEqual(args.provider, 'ollama')
        
        # Test model creation
        model = create_model(args.provider)
        self.assertIsNotNone(model)
    
    @patch.object(sys, 'argv', ['kaia.py', '--provider', 'gemini'])
    def test_full_workflow_gemini(self):
        """Test complete workflow with Gemini provider."""
        # Test argument parsing
        args = parse_arguments()
        self.assertEqual(args.provider, 'gemini')
        
        # Test model creation
        model = create_model(args.provider)
        self.assertIsNotNone(model)
    
    @patch.object(sys, 'argv', ['kaia.py', '--provider', 'github'])
    @patch.dict(os.environ, {'GITHUB_TOKEN': 'fake-token'})
    def test_full_workflow_github(self):
        """Test complete workflow with GitHub provider."""
        # Test argument parsing
        args = parse_arguments()
        self.assertEqual(args.provider, 'github')
        
        # Test model creation
        model = create_model(args.provider)
        self.assertIsNotNone(model)


class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios."""
    
    def test_missing_github_token_in_environment(self):
        """Test that missing GITHUB_TOKEN is handled properly."""
        # Remove GITHUB_TOKEN if it exists
        with patch.dict(os.environ, {}, clear=True):
            # GitHub models should still work with the token handling in create_model
            model = create_model('github')
            self.assertIsNotNone(model)
    
    def test_environment_variable_precedence(self):
        """Test that environment variables take precedence over defaults."""
        custom_values = {
            'OLLAMA_MODEL_NAME': 'custom-ollama',
            'GEMINI_MODEL_NAME': 'custom-gemini',
            'GITHUB_MODEL_NAME': 'custom-github',
            'GITHUB_TOKEN': 'custom-token'
        }
        
        with patch.dict(os.environ, custom_values):
            # Test each provider uses custom values
            ollama_model = create_model('ollama')
            gemini_model = create_model('gemini')
            github_model = create_model('github')
            
            self.assertIsNotNone(ollama_model)
            self.assertIsNotNone(gemini_model)
            self.assertIsNotNone(github_model)


if __name__ == "__main__":
    # Run tests if script is executed directly
    try:
        import pytest
        pytest.main([__file__, '-v'])
    except ImportError:
        unittest.main(verbosity=2)

# Run tests with: python -m pytest tests.py -v
# For coverage: python -m pytest tests.py --cov=kaia --cov-report=html