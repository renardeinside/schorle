"""Tests for schorle.bun module."""

import os
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import requests

from schorle.bun import (
    BUN_VERSION,
    bun_installed,
    install_bun,
    check_and_prepare_bun,
)


def test_bun_version_constant():
    """Test that BUN_VERSION is defined."""
    assert BUN_VERSION == "1.2.21"


def test_bun_installed_true():
    """Test bun_installed when bun is available."""
    with patch('shutil.which') as mock_which:
        mock_which.return_value = "/usr/local/bin/bun"
        assert bun_installed() is True
        mock_which.assert_called_once_with("bun")


def test_bun_installed_false():
    """Test bun_installed when bun is not available."""
    with patch('shutil.which') as mock_which:
        mock_which.return_value = None
        assert bun_installed() is False
        mock_which.assert_called_once_with("bun")


def test_install_bun_x64_linux():
    """Test install_bun for Linux x64."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        # Mock platform detection
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Create fake extracted directory structure
            with tempfile.TemporaryDirectory() as fake_extract_dir:
                fake_bun_dir = Path(fake_extract_dir) / "bun-linux-x64"
                fake_bun_dir.mkdir()
                fake_bun_binary = fake_bun_dir / "bun"
                fake_bun_binary.write_text("fake bun binary")
                
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    # Mock the temporary directory iteration
                    mock_iterdir.side_effect = [
                        [fake_bun_dir],  # First call: list extracted dirs
                        [fake_bun_binary],  # Second call: list contents of bun dir
                    ]
                    
                    install_bun(install_path)
            
            # Verify the correct URL was used
            expected_url = f"https://github.com/oven-sh/bun/releases/download/bun-v{BUN_VERSION}/bun-linux-x64.zip"
            mock_get.assert_called_once_with(expected_url, stream=True)


def test_install_bun_aarch64_darwin():
    """Test install_bun for macOS ARM64."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        # Mock platform detection
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Darwin"
            mock_machine.return_value = "arm64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Create fake extracted directory structure
            with tempfile.TemporaryDirectory() as fake_extract_dir:
                fake_bun_dir = Path(fake_extract_dir) / "bun-darwin-aarch64"
                fake_bun_dir.mkdir()
                fake_bun_binary = fake_bun_dir / "bun"
                fake_bun_binary.write_text("fake bun binary")
                
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    # Mock the temporary directory iteration
                    mock_iterdir.side_effect = [
                        [fake_bun_dir],  # First call: list extracted dirs
                        [fake_bun_binary],  # Second call: list contents of bun dir
                    ]
                    
                    install_bun(install_path)
            
            # Verify the correct URL was used
            expected_url = f"https://github.com/oven-sh/bun/releases/download/bun-v{BUN_VERSION}/bun-darwin-aarch64.zip"
            mock_get.assert_called_once_with(expected_url, stream=True)


def test_install_bun_amd64_windows():
    """Test install_bun for Windows x64."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        # Mock platform detection
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Windows"
            mock_machine.return_value = "amd64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Create fake extracted directory structure
            with tempfile.TemporaryDirectory() as fake_extract_dir:
                fake_bun_dir = Path(fake_extract_dir) / "bun-windows-x64"
                fake_bun_dir.mkdir()
                fake_bun_binary = fake_bun_dir / "bun.exe"
                fake_bun_binary.write_text("fake bun binary")
                
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    # Mock the temporary directory iteration
                    mock_iterdir.side_effect = [
                        [fake_bun_dir],  # First call: list extracted dirs
                        [fake_bun_binary],  # Second call: list contents of bun dir
                    ]
                    
                    install_bun(install_path)
            
            # Verify the correct URL was used
            expected_url = f"https://github.com/oven-sh/bun/releases/download/bun-v{BUN_VERSION}/bun-windows-x64.zip"
            mock_get.assert_called_once_with(expected_url, stream=True)


def test_install_bun_custom_version():
    """Test install_bun with custom version."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        custom_version = "1.0.0"
        
        # Mock platform detection
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Create fake extracted directory structure
            with tempfile.TemporaryDirectory() as fake_extract_dir:
                fake_bun_dir = Path(fake_extract_dir) / "bun-linux-x64"
                fake_bun_dir.mkdir()
                fake_bun_binary = fake_bun_dir / "bun"
                fake_bun_binary.write_text("fake bun binary")
                
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    # Mock the temporary directory iteration
                    mock_iterdir.side_effect = [
                        [fake_bun_dir],  # First call: list extracted dirs
                        [fake_bun_binary],  # Second call: list contents of bun dir
                    ]
                    
                    install_bun(install_path, version=custom_version)
            
            # Verify the correct URL was used with custom version
            expected_url = f"https://github.com/oven-sh/bun/releases/download/bun-v{custom_version}/bun-linux-x64.zip"
            mock_get.assert_called_once_with(expected_url, stream=True)


def test_install_bun_download_error():
    """Test install_bun when download fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock HTTP error
            mock_response = Mock()
            mock_response.raise_for_status.side_effect = requests.HTTPError("404 Not Found")
            mock_get.return_value = mock_response
            
            with pytest.raises(requests.HTTPError):
                install_bun(install_path)


def test_install_bun_zip_error():
    """Test install_bun when zip extraction fails."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile error
            mock_zipfile.side_effect = zipfile.BadZipFile("Invalid zip file")
            
            with pytest.raises(zipfile.BadZipFile):
                install_bun(install_path)


def test_install_bun_permission_error():
    """Test install_bun when there's a permission error."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Mock permission error during file move
            with patch('shutil.move') as mock_move:
                mock_move.side_effect = PermissionError("Permission denied")
                
                with pytest.raises(PermissionError):
                    install_bun(install_path)


def test_install_bun_existing_files():
    """Test install_bun overwrites existing files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        install_path.mkdir()
        
        # Create existing file and directory
        existing_file = install_path / "bun"
        existing_file.write_text("old bun")
        existing_dir = install_path / "lib"
        existing_dir.mkdir()
        (existing_dir / "old_lib.so").write_text("old lib")
        
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Create fake extracted directory structure
            with tempfile.TemporaryDirectory() as fake_extract_dir:
                fake_bun_dir = Path(fake_extract_dir) / "bun-linux-x64"
                fake_bun_dir.mkdir()
                new_bun_binary = fake_bun_dir / "bun"
                new_bun_binary.write_text("new bun binary")
                new_lib_dir = fake_bun_dir / "lib"
                new_lib_dir.mkdir()
                (new_lib_dir / "new_lib.so").write_text("new lib")
                
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    # Mock the temporary directory iteration
                    mock_iterdir.side_effect = [
                        [fake_bun_dir],  # First call: list extracted dirs
                        [new_bun_binary, new_lib_dir],  # Second call: list contents of bun dir
                    ]
                    
                    # Mock the file operations
                    with patch('shutil.rmtree') as mock_rmtree, \
                         patch('pathlib.Path.unlink') as mock_unlink, \
                         patch('shutil.move') as mock_move:
                        
                        install_bun(install_path)
                        
                        # Verify existing files were removed
                        mock_unlink.assert_called()  # existing file removed
                        mock_rmtree.assert_called()  # existing dir removed


def test_check_and_prepare_bun_already_installed():
    """Test check_and_prepare_bun when bun is already installed."""
    with patch('schorle.bun.bun_installed') as mock_installed, \
         patch('shutil.which') as mock_which:
        
        mock_installed.return_value = True
        mock_which.return_value = "/usr/local/bin/bun"
        
        result = check_and_prepare_bun()
        
        assert result == Path("/usr/local/bin/bun")
        mock_installed.assert_called_once()


def test_check_and_prepare_bun_install_success():
    """Test check_and_prepare_bun when bun needs to be installed."""
    with patch('schorle.bun.bun_installed') as mock_installed, \
         patch('schorle.bun.install_bun') as mock_install, \
         patch('shutil.which') as mock_which, \
         patch('pathlib.Path.home') as mock_home, \
         patch.dict(os.environ, {'PATH': '/usr/bin'}, clear=False):
        
        # First call: bun not installed, second call: after installation
        mock_installed.return_value = False
        mock_home.return_value = Path("/home/user")
        
        # Mock which calls - first None, then success after install
        mock_which.side_effect = [None, "/home/user/.schorle/bun"]
        
        result = check_and_prepare_bun()
        
        assert result == Path("/home/user/.schorle/bun")
        mock_install.assert_called_once_with(Path("/home/user/.schorle"))
        assert "/home/user/.schorle/bun" in os.environ["PATH"]


def test_check_and_prepare_bun_install_fails():
    """Test check_and_prepare_bun when installation fails."""
    with patch('schorle.bun.bun_installed') as mock_installed, \
         patch('schorle.bun.install_bun') as mock_install, \
         patch('shutil.which') as mock_which, \
         patch('pathlib.Path.home') as mock_home:
        
        mock_installed.return_value = False
        mock_home.return_value = Path("/home/user")
        
        # Mock which always returns None (bun still not found after install)
        mock_which.return_value = None
        
        with pytest.raises(RuntimeError, match="Bun not found even after installation"):
            check_and_prepare_bun()
        
        mock_install.assert_called_once()


def test_install_bun_network_timeout():
    """Test install_bun when network request times out."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "x86_64"
            
            # Mock network timeout
            mock_get.side_effect = requests.Timeout("Request timed out")
            
            with pytest.raises(requests.Timeout):
                install_bun(install_path)


def test_install_bun_unknown_architecture():
    """Test install_bun with unknown architecture."""
    with tempfile.TemporaryDirectory() as tmpdir:
        install_path = Path(tmpdir) / "bun"
        
        with patch('platform.system') as mock_system, \
             patch('platform.machine') as mock_machine, \
             patch('requests.get') as mock_get, \
             patch('zipfile.ZipFile') as mock_zipfile:
            
            mock_system.return_value = "Linux"
            mock_machine.return_value = "unknown_arch"  # Unknown architecture
            
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.iter_content.return_value = [b"fake zip data"]
            mock_get.return_value = mock_response
            
            # Mock zipfile extraction
            mock_zip_instance = Mock()
            mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
            
            # Create fake extracted directory structure
            with tempfile.TemporaryDirectory() as fake_extract_dir:
                fake_bun_dir = Path(fake_extract_dir) / "bun-linux-unknown_arch"
                fake_bun_dir.mkdir()
                fake_bun_binary = fake_bun_dir / "bun"
                fake_bun_binary.write_text("fake bun binary")
                
                with patch('pathlib.Path.iterdir') as mock_iterdir:
                    # Mock the temporary directory iteration
                    mock_iterdir.side_effect = [
                        [fake_bun_dir],  # First call: list extracted dirs
                        [fake_bun_binary],  # Second call: list contents of bun dir
                    ]
                    
                    install_bun(install_path)
            
            # Should attempt download with unknown architecture
            expected_url = f"https://github.com/oven-sh/bun/releases/download/bun-v{BUN_VERSION}/bun-linux-unknown_arch.zip"
            mock_get.assert_called_once_with(expected_url, stream=True)


def test_install_bun_expanduser():
    """Test install_bun properly expands user home directory."""
    with patch('platform.system') as mock_system, \
         patch('platform.machine') as mock_machine, \
         patch('requests.get') as mock_get, \
         patch('zipfile.ZipFile') as mock_zipfile, \
         patch('pathlib.Path.mkdir') as mock_mkdir:
        
        mock_system.return_value = "Linux"
        mock_machine.return_value = "x86_64"
        
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.iter_content.return_value = [b"fake zip data"]
        mock_get.return_value = mock_response
        
        # Mock zipfile extraction
        mock_zip_instance = Mock()
        mock_zipfile.return_value.__enter__.return_value = mock_zip_instance
        
        # Create fake extracted directory structure
        with tempfile.TemporaryDirectory() as fake_extract_dir:
            fake_bun_dir = Path(fake_extract_dir) / "bun-linux-x64"
            fake_bun_dir.mkdir()
            fake_bun_binary = fake_bun_dir / "bun"
            fake_bun_binary.write_text("fake bun binary")
            
            with patch('pathlib.Path.iterdir') as mock_iterdir:
                # Mock the temporary directory iteration
                mock_iterdir.side_effect = [
                    [fake_bun_dir],  # First call: list extracted dirs
                    [fake_bun_binary],  # Second call: list contents of bun dir
                ]
                
                # Test with tilde path
                install_bun("~/custom_bun")
        
        # Verify mkdir was called with expanded path
        mock_mkdir.assert_called_with(parents=True, exist_ok=True)
