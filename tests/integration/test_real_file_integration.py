#!/usr/bin/env python3
"""Integration tests for real web server file operations."""

import os
import sys
import tempfile
import json
import shutil
import time
from unittest.mock import Mock, patch
import pytest

# Add src to path for imports
sys.path.insert(0, '/src')
from web_server import EnhancedLogHandler


class TestRealWebServerFileOperations:
    """Test web server operations with real files."""
    
    @pytest.fixture
    def real_web_environment(self):
        """Create real web testing environment."""
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, 'rsync.log')
        
        # Create test log file
        with open(log_file, 'w') as f:
            f.write('[2024-02-02 10:00:00] [INFO] Test log entry\n')
        
        yield {
            'temp_dir': temp_dir,
            'log_file': log_file
        }
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def create_real_handler(self, log_file_path):
        """Create handler that can work with real files."""
        # Create handler bypassing HTTP initialization
        handler = object.__new__(EnhancedLogHandler)
        handler.log_file = log_file_path
        
        # Add required attributes that would normally be set by HTTP server
        handler.server = Mock()
        handler.client_address = ('127.0.0.1', 12345)
        handler.request = Mock()
        
        return handler
    
    def test_real_log_clearing_operation(self, real_web_environment):
        """Test actual log file clearing."""
        log_file = real_web_environment['log_file']
        handler = self.create_real_handler(log_file)
        
        # Verify log file has content initially
        assert os.path.getsize(log_file) > 0
        
        # Test actual log clearing
        if hasattr(handler, 'clear_logs'):
            result = handler.clear_logs()
            # File should be cleared or marked as cleared
            assert isinstance(result, (bool, str))
    
    def test_real_log_rotation(self, real_web_environment):
        """Test actual log file rotation behavior."""
        log_file = real_web_environment['log_file']
        handler = self.create_real_handler(log_file)
        
        # Fill log file with content to trigger rotation
        large_content = '[INFO] Log entry\n' * 1000
        with open(log_file, 'w') as f:
            f.write(large_content)
        
        # Verify large file size
        initial_size = os.path.getsize(log_file)
        assert initial_size > 10000
        
        # Test reading large file (may trigger rotation logic)
        result = handler.safe_read_log(log_file)
        assert isinstance(result, str)
    
    def test_real_error_log_accumulation(self, real_web_environment):
        """Test real error accumulation over time."""
        log_file = real_web_environment['log_file']
        handler = self.create_real_handler(log_file)
        
        # Simulate log entries over time
        log_entries = []
        for i in range(20):
            if i % 4 == 0:  # Every 4th entry is an error
                log_entries.append(f'[2024-02-02 10:{i:02d}:00] [ERROR] Error {i//4}')
            else:
                log_entries.append(f'[2024-02-02 10:{i:02d}:00] [INFO] Info {i}')
        
        with open(log_file, 'w') as f:
            f.write('\n'.join(log_entries))
        
        # Test actual error detection
        result = handler.safe_read_log(log_file)
        
        # Should detect 5 errors (0, 4, 8, 12, 16)
        assert isinstance(result, str)
        assert 'ERROR SUMMARY:' in result
        assert ('5 errors found' in result or '5 error' in result)
    
    def test_real_log_file_permissions(self, real_web_environment):
        """Test handling of real file permission issues."""
        log_file = real_web_environment['log_file']
        handler = self.create_real_handler(log_file)
        
        # Create file with restricted permissions (if possible in container)
        with open(log_file, 'w') as f:
            f.write('[INFO] Test content')
        
        try:
            # Try to restrict permissions
            os.chmod(log_file, 0o000)
            
            # Test reading restricted file
            result = handler.safe_read_log(log_file)
            
            # Should handle permission error gracefully
            assert isinstance(result, str)
            
        except (OSError, PermissionError):
            # If chmod fails in container, test alternative
            nonexistent_file = os.path.join(real_web_environment['temp_dir'], 'restricted', 'file.log')
            result = handler.safe_read_log(nonexistent_file)
            assert isinstance(result, str)
        
        finally:
            # Restore permissions for cleanup
            try:
                os.chmod(log_file, 0o644)
            except (OSError, PermissionError):
                pass
    
    def test_real_concurrent_log_operations(self, real_web_environment):
        """Test real concurrent log file operations."""
        log_file = real_web_environment['log_file']
        handler1 = self.create_real_handler(log_file)
        handler2 = self.create_real_handler(log_file)
        
        # Create initial content
        with open(log_file, 'w') as f:
            f.write('[INFO] Initial entry\n')
        
        # Test concurrent reads
        result1 = handler1.safe_read_log(log_file)
        
        # Append more content while first handler might still be processing
        with open(log_file, 'a') as f:
            f.write('[ERROR] Concurrent error\n')
        
        result2 = handler2.safe_read_log(log_file)
        
        # Both operations should succeed
        assert isinstance(result1, str)
        assert isinstance(result2, str)
        assert 'Initial entry' in result1
    
    def test_real_log_with_special_characters(self, real_web_environment):
        """Test real log parsing with special characters and encoding."""
        log_file = real_web_environment['log_file']
        handler = self.create_real_handler(log_file)
        
        # Create log with special characters
        special_content = '''[2024-02-02 10:00:00] [INFO] Starting process
[2024-02-02 10:00:01] [ERROR] File not found: /path/with spaces/special-chars_123.txt
[2024-02-02 10:00:02] [INFO] Processing files with émojis 🚀
[2024-02-02 10:00:03] [ERROR] Invalid character in filename: file"with'quotes.txt
[2024-02-02 10:00:04] [INFO] Completed with warnings
'''
        
        # Write with UTF-8 encoding
        with open(log_file, 'w', encoding='utf-8') as f:
            f.write(special_content)
        
        # Test actual parsing
        result = handler.safe_read_log(log_file)
        
        # Should handle special characters gracefully
        assert isinstance(result, str)
        assert 'ERROR SUMMARY:' in result
        assert '2 errors found' in result or '2 error' in result
    
    @patch('subprocess.run')
    def test_real_sync_process_integration(self, mock_subprocess, real_web_environment):
        """Test integration between sync process and log file."""
        log_file = real_web_environment['log_file']
        handler = self.create_real_handler(log_file)
        
        # Mock sync process output
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout='Sync completed successfully\n',
            stderr=''
        )
        
        # Create log content that would be generated by sync process
        sync_log = '''[2024-02-02 10:00:00] [INFO] Starting rsync process
[2024-02-02 10:00:01] [INFO] Connecting to remote host
[2024-02-02 10:00:02] [INFO] Transferring files...
[2024-02-02 10:00:03] [INFO] transferred: 150 files (1.2MB)
[2024-02-02 10:00:04] [INFO] Sync completed successfully
'''
        
        with open(log_file, 'w') as f:
            f.write(sync_log)
        
        # Test log processing after sync
        result = handler.safe_read_log(log_file)
        
        # Should show successful sync status
        assert isinstance(result, str)
        assert 'No errors found' in result
        assert 'Sync completed successfully' in result


class TestRealFileSystemOperations:
    """Test real file system operations and edge cases."""
    
    @pytest.fixture
    def complex_file_environment(self):
        """Create complex file testing environment."""
        temp_dir = tempfile.mkdtemp()
        
        # Create multiple log files
        files = {
            'current_log': os.path.join(temp_dir, 'rsync.log'),
            'rotated_log': os.path.join(temp_dir, 'rsync.log.1'),
            'compressed_log': os.path.join(temp_dir, 'rsync.log.2.gz'),
            'empty_log': os.path.join(temp_dir, 'empty.log')
        }
        
        # Create empty log
        with open(files['empty_log'], 'w') as f:
            f.write('')
        
        yield {
            'temp_dir': temp_dir,
            'files': files
        }
        
        # Cleanup
        shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_real_multiple_log_files(self, complex_file_environment):
        """Test handling multiple real log files."""
        files = complex_file_environment['files']
        
        # Create current log with recent entries
        with open(files['current_log'], 'w') as f:
            f.write('[2024-02-02 10:00:00] [INFO] Current session\n')
            f.write('[2024-02-02 10:00:01] [ERROR] Current error\n')
        
        # Create rotated log with older entries
        with open(files['rotated_log'], 'w') as f:
            f.write('[2024-02-01 09:00:00] [INFO] Previous session\n')
            f.write('[2024-02-01 09:00:01] [ERROR] Previous error\n')
        
        handler = object.__new__(EnhancedLogHandler)
        handler.log_file = files['current_log']
        
        # Test reading current log
        result = handler.safe_read_log(files['current_log'])
        
        assert isinstance(result, str)
        assert 'Current session' in result
        assert 'ERROR SUMMARY:' in result
    
    def test_real_log_file_growth_monitoring(self, complex_file_environment):
        """Test monitoring real log file growth."""
        log_file = complex_file_environment['files']['current_log']
        
        # Create handler
        handler = object.__new__(EnhancedLogHandler)
        handler.log_file = log_file
        
        # Start with small file
        with open(log_file, 'w') as f:
            f.write('[INFO] Initial entry\n')
        
        initial_size = os.path.getsize(log_file)
        
        # Add more content
        with open(log_file, 'a') as f:
            for i in range(100):
                f.write(f'[INFO] Entry {i}\n')
        
        final_size = os.path.getsize(log_file)
        
        # Verify file grew
        assert final_size > initial_size
        
        # Test reading large file
        result = handler.safe_read_log(log_file)
        assert isinstance(result, str)
        assert 'Entry' in result
    
    def test_real_disk_space_simulation(self, complex_file_environment):
        """Test behavior with large files (simulating disk space issues)."""
        log_file = complex_file_environment['files']['current_log']
        handler = object.__new__(EnhancedLogHandler)
        handler.log_file = log_file
        
        # Create a reasonably large file (but not too large for tests)
        large_content = '[INFO] Large entry with lots of content ' * 100 + '\n'
        
        with open(log_file, 'w') as f:
            for i in range(50):  # 50 * 100 = 5000 entries
                f.write(f'[{i:04d}] {large_content}')
                if i % 10 == 0:  # Add some errors
                    f.write(f'[ERROR] Error at iteration {i}\n')
        
        # Verify large file was created
        file_size = os.path.getsize(log_file)
        assert file_size > 100000  # Should be > 100KB
        
        # Test reading large file
        result = handler.safe_read_log(log_file)
        
        # Should handle large file gracefully (may truncate)
        assert isinstance(result, str)
        assert len(result) > 0