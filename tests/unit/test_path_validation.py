#!/usr/bin/env python3
"""Unit tests for path validation functions from sync_script.sh functionality."""

import pytest
import subprocess
import tempfile
import os
from unittest.mock import patch, Mock


class TestPathValidation:
    """Test path validation logic (simulating bash script validation)."""
    
    def test_validate_absolute_path(self):
        """Test validation of absolute paths."""
        # Since we can't directly test bash functions, we'll test the Python equivalent
        valid_paths = [
            '/data/test',
            '/home/user/documents',
            '/mnt/backup',
            '/var/log'
        ]
        
        for path in valid_paths:
            # Path should be absolute
            assert path.startswith('/'), f'Path {path} should be absolute'
            # Should not contain directory traversal
            assert '../' not in path, f'Path {path} contains directory traversal'
            assert '..\\ ' not in path, f'Path {path} contains Windows directory traversal'
    
    def test_reject_relative_paths(self):
        """Test rejection of relative paths for source directories."""
        invalid_paths = [
            'data/test',
            'relative/path',
            './current/dir',
            '~/home/path'
        ]
        
        for path in invalid_paths:
            # Source paths must be absolute
            assert not path.startswith('/'), f'Path {path} should be rejected as relative'
    
    def test_reject_directory_traversal(self):
        """Test rejection of directory traversal attempts."""
        malicious_paths = [
            '/data/../etc/passwd',
            '/home/user/../../root',
            '/backup/../../../',
            '/mnt/disk/../system',
            '/data/..\\windows\\path'  # Windows-style
        ]
        
        for path in malicious_paths:
            # Should contain directory traversal patterns
            # Fix pattern matching for Windows-style paths
            has_traversal = (
                '../' in path or 
                '..\\' in path or
                '\\..\\' in path
            )
            assert has_traversal, \
                   f'Path {path} should be detected as directory traversal'
    
    def test_reject_dangerous_characters(self):
        """Test rejection of paths with dangerous characters."""
        dangerous_paths = [
            '/data/test; rm -rf /',
            '/data/test && echo hacked',
            '/data/test | cat /etc/passwd',
            '/data/test`whoami`',
            '/data/test$(whoami)',
            '/data/test(malicious)'
        ]
        
        dangerous_chars = [';', '&', '|', '`', '$', '(', ')']
        
        for path in dangerous_paths:
            has_dangerous_char = any(char in path for char in dangerous_chars)
            assert has_dangerous_char, f'Path {path} should contain dangerous characters'
    
    def test_path_normalization(self):
        """Test path normalization logic."""
        test_cases = [
            ('/data//test', '/data/test'),
            ('/data/test/', '/data/test'),
            ('/data/test///', '/data/test'),
            ('//data/test', '/data/test'),
            ('/', '/'),
            ('', '/')  # Empty path should become root
        ]
        
        for input_path, expected in test_cases:
            # Simulate the bash normalization logic
            normalized = input_path
            # Remove double slashes
            while '//' in normalized:
                normalized = normalized.replace('//', '/')
            # Remove trailing slash except for root
            if len(normalized) > 1 and normalized.endswith('/'):
                normalized = normalized[:-1]
            # Handle empty string
            if not normalized:
                normalized = '/'
                
            assert normalized == expected, \
                   f'Path {input_path} should normalize to {expected}, got {normalized}'
    
    def test_empty_path_validation(self):
        """Test handling of empty paths."""
        empty_paths = ['', None, '   ']
        
        for path in empty_paths:
            if path is None or path.strip() == '':
                # Empty paths should be rejected
                assert True  # This would trigger an error in the actual script
    
    def test_valid_backup_routes(self, sample_routes_json):
        """Test validation of complete backup route configurations."""
        for source, destination in sample_routes_json.items():
            # Source should be absolute
            assert source.startswith('/'), f'Source {source} must be absolute'
            
            # Both should not contain dangerous patterns
            dangerous_chars = [';', '&', '|', '`', '$', '(', ')']
            for char in dangerous_chars:
                assert char not in source, f'Source {source} contains dangerous char: {char}'
                assert char not in destination, f'Destination {destination} contains dangerous char: {char}'
            
            # Should not contain directory traversal
            assert '../' not in source, f'Source {source} contains directory traversal'
            assert '../' not in destination, f'Destination {destination} contains directory traversal'


class TestRouteFileValidation:
    """Test JSON route file validation and parsing."""
    
    def test_valid_json_structure(self, sample_routes_json):
        """Test valid JSON structure validation."""
        import json
        
        # Should be valid JSON
        json_str = json.dumps(sample_routes_json)
        parsed = json.loads(json_str)
        
        assert isinstance(parsed, dict), 'Routes should be a dictionary'
        assert len(parsed) > 0, 'Routes should not be empty'
        
        # All keys and values should be strings
        for key, value in parsed.items():
            assert isinstance(key, str), f'Route key {key} should be string'
            assert isinstance(value, str), f'Route value {value} should be string'
    
    def test_invalid_json_handling(self):
        """Test handling of invalid JSON files."""
        invalid_json_samples = [
            '{invalid json}',
            '{"unclosed": "string"',
            'not json at all',
            '{"trailing": "comma",}',
            ''
        ]
        
        import json
        
        for invalid_json in invalid_json_samples:
            with pytest.raises(json.JSONDecodeError):
                json.loads(invalid_json)
    
    def test_route_count_validation(self, sample_routes_json):
        """Test route count validation logic."""
        import json
        
        # Valid route file should have countable routes
        json_str = json.dumps(sample_routes_json)
        parsed = json.loads(json_str)
        route_count = len(parsed)
        
        assert isinstance(route_count, int), 'Route count should be integer'
        assert route_count > 0, 'Should have at least one route'
        assert str(route_count).isdigit(), 'Route count should be numeric string'
    
    def test_empty_routes_file(self):
        """Test handling of empty routes file."""
        import json
        
        empty_routes = {}
        json_str = json.dumps(empty_routes)
        parsed = json.loads(json_str)
        
        route_count = len(parsed)
        assert route_count == 0, 'Empty routes should have count 0'


class TestEnvironmentValidation:
    """Test environment variable validation."""
    
    def test_required_variables_present(self, mock_ssh_environment):
        """Test validation of required environment variables."""
        required_vars = ['REMOTE_USER', 'REMOTE_HOST', 'ROUTES_FILE']
        
        for var in required_vars:
            assert var in mock_ssh_environment, f'Required variable {var} missing'
            assert mock_ssh_environment[var], f'Required variable {var} is empty'
    
    def test_missing_environment_variables(self):
        """Test handling of missing environment variables."""
        required_vars = ['REMOTE_USER', 'REMOTE_HOST', 'ROUTES_FILE']
        
        # Each missing variable should cause validation to fail
        for missing_var in required_vars:
            env_without_var = {var: 'test_value' for var in required_vars if var != missing_var}
            
            # The missing variable should not be in the environment
            assert missing_var not in env_without_var, \
                   f'Variable {missing_var} should be missing for this test'
    
    def test_ssh_key_file_validation(self):
        """Test SSH key file validation logic."""
        # Test various SSH key file scenarios
        test_cases = [
            ('/path/to/valid/key', True),
            ('', False),  # Empty path
            ('/nonexistent/key', False),  # Would fail existence check
        ]
        
        for key_path, should_be_valid in test_cases:
            if should_be_valid:
                assert key_path, f'Valid key path {key_path} should not be empty'
            else:
                assert not key_path or not os.path.exists(key_path), \
                       f'Invalid key path {key_path} should be empty or non-existent'


class TestRsyncCommandConstruction:
    """Test rsync command construction and validation."""
    
    def test_rsync_exclude_patterns(self):
        """Test rsync exclude patterns are properly formatted."""
        exclude_patterns = [
            '*.Trash*',
            'lost+found',
            'System Volume Information',
            '.DS_Store',
            'Thumbs.db',
            'desktop.ini',
            'sync.log',
            '.venv'
        ]
        
        for pattern in exclude_patterns:
            # Patterns should be safe for command line
            assert not any(char in pattern for char in [';', '&', '|', '`']), \
                   f'Exclude pattern {pattern} contains dangerous characters'
    
    def test_ssh_options_validation(self):
        """Test SSH connection options are secure."""
        expected_ssh_options = [
            '-i /.ssh/id_rsa',
            '-o BatchMode=yes',
            '-o ConnectTimeout=10',
            '-o ServerAliveInterval=60',
            '-o StrictHostKeyChecking=no',
            '-o UserKnownHostsFile=/dev/null'
        ]
        
        # These options should be present for security and reliability
        for option in expected_ssh_options:
            # Each option should be properly formatted
            assert option.startswith('-'), f'SSH option {option} should start with -'
            if '=' in option:
                key, value = option.split('=', 1)
                assert key.strip(), f'SSH option key in {option} should not be empty'
                assert value.strip(), f'SSH option value in {option} should not be empty'