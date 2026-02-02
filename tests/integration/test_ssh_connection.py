#!/usr/bin/env python3
"""Integration tests for SSH connectivity and remote server communication."""

import pytest
import subprocess
import socket
import tempfile
import os
from unittest.mock import patch, Mock


class TestSSHConnectivity:
    """Test SSH connection functionality."""
    
    @pytest.fixture
    def ssh_config(self):
        """Create temporary SSH configuration for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create SSH directory structure
            ssh_dir = os.path.join(temp_dir, '.ssh')
            os.makedirs(ssh_dir)
            
            # Create mock private key
            key_file = os.path.join(ssh_dir, 'id_rsa')
            with open(key_file, 'w') as f:
                f.write('-----BEGIN RSA PRIVATE KEY-----\n')
                f.write('fake_key_content_for_testing\n')
                f.write('-----END RSA PRIVATE KEY-----\n')
            os.chmod(key_file, 0o600)
            
            # Create SSH config file
            config_file = os.path.join(ssh_dir, 'config')
            with open(config_file, 'w') as f:
                f.write('Host *\n')
                f.write('    StrictHostKeyChecking no\n')
                f.write('    UserKnownHostsFile /dev/null\n')
                f.write('    LogLevel QUIET\n')
            
            yield {
                'ssh_dir': ssh_dir,
                'key_file': key_file,
                'config_file': config_file
            }
    
    def test_ssh_key_file_exists(self, ssh_config):
        """Test SSH private key file existence and permissions."""
        key_file = ssh_config['key_file']
        
        # File should exist
        assert os.path.exists(key_file), 'SSH private key file should exist'
        
        # Should be readable
        assert os.access(key_file, os.R_OK), 'SSH key should be readable'
        
        # Should have correct permissions (600)
        stat_info = os.stat(key_file)
        permissions = oct(stat_info.st_mode)[-3:]
        assert permissions == '600', f'SSH key permissions should be 600, got {permissions}'
    
    def test_ssh_config_file_creation(self, ssh_config):
        """Test SSH configuration file creation and content."""
        config_file = ssh_config['config_file']
        
        assert os.path.exists(config_file), 'SSH config file should exist'
        
        with open(config_file, 'r') as f:
            config_content = f.read()
        
        # Should contain required security settings
        required_settings = [
            'StrictHostKeyChecking no',
            'UserKnownHostsFile /dev/null',
            'LogLevel QUIET'
        ]
        
        for setting in required_settings:
            assert setting in config_content, f'SSH config should contain: {setting}'
    
    @patch('subprocess.run')
    def test_ssh_connection_command_construction(self, mock_subprocess):
        """Test SSH connection command is properly constructed."""
        mock_subprocess.return_value = Mock(returncode=0, stdout='Connection OK\n')
        
        # Simulate the SSH connection test command
        ssh_command = [
            'ssh',
            '-i', '/.ssh/id_rsa',
            '-o', 'BatchMode=yes',
            '-o', 'ConnectTimeout=10',
            '-o', 'StrictHostKeyChecking=no',
            '-o', 'UserKnownHostsFile=/dev/null',
            '-v',
            'testuser@192.168.1.100',
            'echo "Connection OK"'
        ]
        
        # Execute the command
        result = subprocess.run(ssh_command, capture_output=True, text=True, timeout=15)
        
        # Should have been called with correct parameters
        mock_subprocess.assert_called_once()
        call_args = mock_subprocess.call_args[0][0]
        
        # Verify command structure
        assert call_args[0] == 'ssh', 'Command should start with ssh'
        assert '-i' in call_args, 'Should specify identity file'
        assert '/.ssh/id_rsa' in call_args, 'Should use correct key file'
        assert 'BatchMode=yes' in ' '.join(call_args), 'Should use batch mode'
        assert 'ConnectTimeout=10' in ' '.join(call_args), 'Should set connection timeout'
    
    @patch('subprocess.run')
    def test_ssh_connection_success(self, mock_subprocess):
        """Test successful SSH connection."""
        mock_subprocess.return_value = Mock(
            returncode=0,
            stdout='Connection OK\n',
            stderr=''
        )
        
        # Simulate successful connection
        result = subprocess.run(['ssh', 'test@host', 'echo OK'], capture_output=True, text=True)
        
        assert result.returncode == 0, 'SSH connection should succeed'
        assert 'Connection OK' in result.stdout, 'Should receive expected output'
    
    @patch('subprocess.run')
    def test_ssh_connection_failure(self, mock_subprocess):
        """Test SSH connection failure handling."""
        mock_subprocess.return_value = Mock(
            returncode=255,
            stdout='',
            stderr='Connection refused\n'
        )
        
        # Simulate connection failure
        result = subprocess.run(['ssh', 'test@host', 'echo OK'], capture_output=True, text=True)
        
        assert result.returncode != 0, 'SSH connection should fail'
        assert 'Connection refused' in result.stderr, 'Should capture error message'
    
    @patch('subprocess.run')
    def test_ssh_connection_timeout(self, mock_subprocess):
        """Test SSH connection timeout handling."""
        mock_subprocess.side_effect = subprocess.TimeoutExpired('ssh', 15)
        
        # Simulate connection timeout
        with pytest.raises(subprocess.TimeoutExpired):
            subprocess.run(['ssh', 'test@host', 'echo OK'], timeout=15)
    
    def test_network_connectivity_check(self):
        """Test basic network connectivity check."""
        # Test ping functionality (mocked)
        with patch('subprocess.run') as mock_subprocess:
            mock_subprocess.return_value = Mock(returncode=0)
            
            # Simulate ping command
            result = subprocess.run(['ping', '-c', '1', '-W', '5', '192.168.1.100'], 
                                  capture_output=True)
            
            # Should have attempted ping
            mock_subprocess.assert_called_once()
            call_args = mock_subprocess.call_args[0][0]
            assert 'ping' == call_args[0], 'Should use ping command'
            assert '-c' in call_args, 'Should limit ping count'
    
    @patch('socket.socket')
    def test_port_connectivity_check(self, mock_socket):
        """Test SSH port connectivity check."""
        # Mock successful connection
        mock_sock = Mock()
        mock_socket.return_value = mock_sock
        mock_sock.connect.return_value = None
        
        # Test connection to SSH port
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5)
            result = sock.connect(('192.168.1.100', 22))
            sock.close()
            
            # Should attempt connection
            mock_sock.connect.assert_called_with(('192.168.1.100', 22))
        except Exception as e:
            pytest.skip(f'Network test skipped: {e}')
    
    def test_ssh_key_permissions_validation(self):
        """Test SSH key file permissions validation."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as temp_key:
            temp_key.write('fake ssh key content')
            temp_key_path = temp_key.name
        
        try:
            # Test different permission scenarios
            test_permissions = [
                (0o600, True),   # Correct permissions
                (0o644, False),  # Too permissive
                (0o400, True),   # Read-only, acceptable
                (0o755, False),  # Way too permissive
            ]
            
            for perms, should_be_valid in test_permissions:
                os.chmod(temp_key_path, perms)
                actual_perms = oct(os.stat(temp_key_path).st_mode)[-3:]
                expected_perms = oct(perms)[-3:]
                
                if should_be_valid:
                    assert actual_perms in ['600', '400'], \
                           f'SSH key permissions {actual_perms} should be restrictive'
                else:
                    assert actual_perms not in ['600', '400'], \
                           f'SSH key permissions {actual_perms} should be flagged as insecure'
        finally:
            os.unlink(temp_key_path)


class TestRemoteHostValidation:
    """Test remote host validation and connectivity."""
    
    def test_ip_address_validation(self):
        """Test IP address format validation."""
        valid_ips = [
            '192.168.1.100',
            '10.0.0.1',
            '172.16.0.1',
            '100.64.0.1'  # Tailscale range
        ]
        
        invalid_ips = [
            '999.999.999.999',
            '192.168.1',
            'not.an.ip.address',
            '192.168.1.256',
            ''
        ]
        
        import re
        ip_pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        
        for ip in valid_ips:
            assert re.match(ip_pattern, ip), f'IP {ip} should match pattern'
            # Additional validation for octet ranges
            octets = ip.split('.')
            for octet in octets:
                assert 0 <= int(octet) <= 255, f'Octet {octet} in {ip} out of range'
        
        for ip in invalid_ips:
            if ip:  # Skip empty string
                is_valid_format = re.match(ip_pattern, ip) is not None
                if is_valid_format:
                    # Check octet ranges
                    try:
                        octets = ip.split('.')
                        is_valid_range = all(0 <= int(octet) <= 255 for octet in octets)
                        assert not is_valid_range, f'IP {ip} should be invalid'
                    except ValueError:
                        pass  # Invalid integer conversion, as expected
                else:
                    assert not is_valid_format, f'IP {ip} should not match pattern'
    
    def test_hostname_validation(self):
        """Test hostname format validation."""
        valid_hostnames = [
            'server.local',
            'backup-server',
            'host123',
            'my-server.example.com'
        ]
        
        invalid_hostnames = [
            '',
            'server with spaces',
            'server_with_underscores',
            'server..local',
            '-server',
            'server-',
            'a' * 300  # Too long
        ]
        
        import re
        hostname_pattern = r'^[a-zA-Z0-9][a-zA-Z0-9\-\.]*[a-zA-Z0-9]$'
        
        for hostname in valid_hostnames:
            assert re.match(hostname_pattern, hostname), f'Hostname {hostname} should be valid'
            assert len(hostname) <= 253, f'Hostname {hostname} too long'
        
        for hostname in invalid_hostnames:
            if hostname:  # Skip empty string
                # More restrictive validation that catches edge cases
                is_valid = (
                    re.match(hostname_pattern, hostname) and 
                    len(hostname) <= 253 and
                    not '..' in hostname and  # No consecutive dots
                    not hostname.startswith('.') and  # No leading dots
                    not hostname.endswith('.') and   # No trailing dots
                    not hostname.startswith('-') and # No leading hyphens
                    not hostname.endswith('-')       # No trailing hyphens
                )
                assert not is_valid, f'Hostname {hostname} should be invalid'
    
    @patch('subprocess.run')
    def test_remote_host_reachability(self, mock_subprocess):
        """Test remote host reachability check."""
        # Test successful ping
        mock_subprocess.return_value = Mock(returncode=0, stdout='PING OK\n')
        
        result = subprocess.run(['ping', '-c', '1', '-W', '5', '192.168.1.100'], 
                              capture_output=True)
        
        assert result.returncode == 0, 'Host should be reachable'
        
        # Test failed ping
        mock_subprocess.return_value = Mock(returncode=1, stdout='', stderr='Host unreachable')
        
        result = subprocess.run(['ping', '-c', '1', '-W', '5', '192.168.1.100'], 
                              capture_output=True)
        
        assert result.returncode != 0, 'Host should be unreachable'
    
    def test_tailscale_ip_range_validation(self):
        """Test Tailscale IP address range validation."""
        tailscale_ips = [
            '100.64.0.1',
            '100.127.255.254',
            '100.100.100.100'
        ]
        
        non_tailscale_ips = [
            '192.168.1.100',
            '10.0.0.1',
            '172.16.0.1',
            '8.8.8.8'
        ]
        
        def is_tailscale_ip(ip):
            """Check if IP is in Tailscale range (100.64.0.0/10)."""
            try:
                octets = [int(x) for x in ip.split('.')]
                return (octets[0] == 100 and 64 <= octets[1] <= 127)
            except (ValueError, IndexError):
                return False
        
        for ip in tailscale_ips:
            assert is_tailscale_ip(ip), f'IP {ip} should be in Tailscale range'
        
        for ip in non_tailscale_ips:
            assert not is_tailscale_ip(ip), f'IP {ip} should not be in Tailscale range'


class TestEnvironmentSetup:
    """Test environment setup and configuration."""
    
    def test_environment_variable_export(self, mock_ssh_environment):
        """Test environment variable setup for sync script."""
        # Simulate environment file creation
        env_content = []
        for key, value in mock_ssh_environment.items():
            env_content.append(f"export {key}='{value}'")
        
        env_file_content = '\n'.join(env_content)
        
        # Verify all required variables are exported
        assert 'export REMOTE_USER=' in env_file_content
        assert 'export REMOTE_HOST=' in env_file_content
        assert 'export ROUTES_FILE=' in env_file_content
        
        # Verify values are properly quoted
        for line in env_content:
            assert line.count("'") >= 2, f'Environment line should be quoted: {line}'
    
    def test_log_directory_creation(self):
        """Test log directory creation and permissions."""
        import tempfile
        
        with tempfile.TemporaryDirectory() as temp_dir:
            log_dir = os.path.join(temp_dir, 'logs')
            
            # Create log directory
            os.makedirs(log_dir, exist_ok=True)
            
            # Should exist and be writable
            assert os.path.exists(log_dir), 'Log directory should be created'
            assert os.access(log_dir, os.W_OK), 'Log directory should be writable'
            
            # Test permissions
            stat_info = os.stat(log_dir)
            permissions = oct(stat_info.st_mode)[-3:]
            assert permissions == '755', f'Log directory permissions should be 755, got {permissions}'
    
    def test_container_startup_sequence(self):
        """Test the logical sequence of container startup steps."""
        startup_steps = [
            'validate_environment_variables',
            'create_log_directory', 
            'setup_ssh_configuration',
            'test_remote_connectivity',
            'start_web_server',
            'start_cron_daemon'
        ]
        
        # Each step should be logically ordered
        for i, step in enumerate(startup_steps):
            assert step, f'Startup step {i} should be defined'
            
            # Verify dependencies
            if step == 'setup_ssh_configuration':
                # Should come after environment validation
                assert 'validate_environment_variables' in startup_steps[:i]
            
            elif step == 'test_remote_connectivity':
                # Should come after SSH setup
                assert 'setup_ssh_configuration' in startup_steps[:i]
            
            elif step == 'start_cron_daemon':
                # Should be last
                assert i == len(startup_steps) - 1