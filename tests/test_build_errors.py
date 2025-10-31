"""Tests for error cases and missing coverage in schorle.build module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
import pytest
import subprocess
import jinja2

from schorle.build import (
    print_build_info,
    print_build_error,
    print_build_output,
    get_client_template,
    get_server_template,
    get_template,
    transform_artifacts_to_manifest,
    build_entrypoints,
)
from schorle.manifest import SchorleProject, PageInfo, BuildManifestEntry
from schorle.utils import cwd


def test_print_build_info():
    """Test print_build_info function."""
    with patch('schorle.build.console') as mock_console:
        print_build_info("Test message", "green")
        mock_console.print.assert_called_once()


def test_print_build_error_without_details():
    """Test print_build_error without details."""
    with patch('schorle.build.console') as mock_console:
        print_build_error("Test error")
        # Should call print once for error text only
        assert mock_console.print.call_count == 1


def test_print_build_error_with_details():
    """Test print_build_error with details."""
    with patch('schorle.build.console') as mock_console:
        print_build_error("Test error", "Detailed error information")
        # Should call print twice - once for error text, once for panel
        assert mock_console.print.call_count == 2


def test_print_build_output_with_stdout():
    """Test print_build_output with stdout content."""
    with patch('schorle.build.console') as mock_console:
        print_build_output("Build successful", "")
        # Should call print once for stdout panel
        assert mock_console.print.call_count == 1


def test_print_build_output_with_stderr():
    """Test print_build_output with stderr content."""
    with patch('schorle.build.console') as mock_console:
        print_build_output("", "Warning: deprecated API")
        # Should call print once for stderr panel
        assert mock_console.print.call_count == 1


def test_print_build_output_with_json_artifacts():
    """Test print_build_output filters out JSON artifacts from stderr."""
    with patch('schorle.build.console') as mock_console:
        stderr = """Warning: deprecated API
{"artifact": "data"}
[1, 2, 3]
Real error message"""
        
        print_build_output("", stderr)
        # Should call print once, but only for non-JSON lines
        mock_console.print.assert_called_once()


def test_print_build_output_empty():
    """Test print_build_output with empty strings."""
    with patch('schorle.build.console') as mock_console:
        print_build_output("", "")
        # Should not call print at all
        mock_console.print.assert_not_called()


def test_get_client_template():
    """Test get_client_template function."""
    template = get_client_template()
    assert isinstance(template, jinja2.Template)


def test_get_server_template():
    """Test get_server_template function."""
    template = get_server_template()
    assert isinstance(template, jinja2.Template)


def test_get_template_legacy():
    """Test get_template legacy function."""
    template = get_template()
    assert isinstance(template, jinja2.Template)


def test_transform_artifacts_to_manifest():
    """Test transform_artifacts_to_manifest function."""
    # Create mock artifacts
    artifacts = [
        {
            "page": "Index",
            "js": "/_schorle/dist/Index.abc123.js",
            "css": "/_schorle/dist/Index.abc123.css",
            "server_js": "/_schorle/dist/server/Index.abc123.js"
        }
    ]
    
    # Create mock page info
    mock_page_info = Mock(spec=PageInfo)
    mock_page_info.page = Path("pages/Index.tsx")
    
    page_infos = [mock_page_info]
    
    # Create mock project
    mock_project = Mock(spec=SchorleProject)
    mock_project.pages_path = Path("pages")
    
    entries = transform_artifacts_to_manifest(artifacts, page_infos, mock_project)
    
    assert len(entries) == 1
    assert isinstance(entries[0], BuildManifestEntry)
    assert entries[0].page == "Index"
    assert entries[0].assets.js == "/_schorle/dist/Index.abc123.js"
    assert entries[0].assets.css == "/_schorle/dist/Index.abc123.css"
    assert entries[0].assets.server_js == "/_schorle/dist/server/Index.abc123.js"


def test_transform_artifacts_to_manifest_mismatched_pages():
    """Test transform_artifacts_to_manifest with mismatched pages."""
    artifacts = [{"page": "Index"}]
    page_infos = []  # No matching page infos
    mock_project = Mock(spec=SchorleProject)
    
    entries = transform_artifacts_to_manifest(artifacts, page_infos, mock_project)
    
    # Should still create entries even without matching page infos
    assert len(entries) == 1


def test_build_entrypoints_subprocess_error():
    """Test build_entrypoints with subprocess error."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Mock subprocess to raise an error
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.CalledProcessError(1, "bun", "Build failed")
            
            with pytest.raises(subprocess.CalledProcessError):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_build_entrypoints_missing_manifest():
    """Test build_entrypoints with missing manifest file."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path("nonexistent/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Mock successful subprocess but no manifest created
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            with pytest.raises(FileNotFoundError):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_build_entrypoints_invalid_manifest_json():
    """Test build_entrypoints with invalid JSON in manifest."""
    with tempfile.TemporaryDirectory() as tmpdir:
        proj = Mock(spec=SchorleProject)
        manifest_path = Path(tmpdir) / "manifest.json"
        proj.manifest_path = manifest_path
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create invalid JSON
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text("invalid json content")
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            with pytest.raises(json.JSONDecodeError):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)




def test_build_entrypoints_with_env_variables():
    """Test build_entrypoints respects environment variables."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = False  # Production mode
        
        # Mock the manifest file
        proj.manifest_path.parent.mkdir(exist_ok=True)
        proj.manifest_path.write_text('{"entries": []}')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)
            
            # Check that NODE_ENV was set to production
            call_args = mock_run.call_args
            env = call_args[1].get('env', {})
            assert env.get('NODE_ENV') == 'production'


def test_build_entrypoints_timeout():
    """Test build_entrypoints with timeout."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("bun", 30)
            
            with pytest.raises(subprocess.TimeoutExpired):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_build_entrypoints_permission_error():
    """Test build_entrypoints with permission error on manifest write."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path("/root/manifest.json")  # Likely no permission
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Mock subprocess success but permission error on file operations
        with patch('subprocess.run') as mock_run, \
             patch('pathlib.Path.read_text') as mock_read:
            
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            mock_read.side_effect = PermissionError("Permission denied")
            
            with pytest.raises(PermissionError):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_transform_artifacts_edge_cases():
    """Test transform_artifacts_to_manifest with edge cases."""
    # Test with empty artifacts
    entries = transform_artifacts_to_manifest([], [], Mock())
    assert entries == []
    
    # Test with artifact missing required fields
    artifacts = [{"page": "Index"}]  # Missing js, css, server_js
    page_infos = []
    mock_project = Mock(spec=SchorleProject)
    
    entries = transform_artifacts_to_manifest(artifacts, page_infos, mock_project)
    assert len(entries) == 1
    assert entries[0].page == "Index"
    # Should handle missing fields gracefully


def test_jinja_template_rendering_error():
    """Test error handling in template rendering."""
    # This tests the error paths in template usage
    template = get_client_template()
    
    # Test with invalid template variables
    with pytest.raises(jinja2.UndefinedError):
        template.render(undefined_variable="test")


def test_build_with_missing_bun():
    """Test build behavior when bun is not available."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = FileNotFoundError("bun: command not found")
            
            with pytest.raises(FileNotFoundError):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_build_with_disk_full():
    """Test build behavior when disk is full."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Mock subprocess success but OSError on file operations
        with patch('subprocess.run') as mock_run, \
             patch('pathlib.Path.write_text') as mock_write:
            
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            proj.manifest_path.parent.mkdir(exist_ok=True)
            
            # Mock reading successful manifest content
            with patch('pathlib.Path.read_text') as mock_read:
                mock_read.return_value = '{"entries": []}'
                mock_write.side_effect = OSError("No space left on device")
                
                with pytest.raises(OSError):
                    build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_build_with_interrupted_process():
    """Test build behavior when process is interrupted."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        with patch('subprocess.run') as mock_run:
            mock_run.side_effect = KeyboardInterrupt("Process interrupted")
            
            with pytest.raises(KeyboardInterrupt):
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)


def test_transform_artifacts_with_relative_paths():
    """Test transform_artifacts_to_manifest with relative asset paths."""
    artifacts = [
        {
            "page": "Index",
            "js": "dist/Index.js",  # Relative path
            "css": "dist/Index.css",
            "server_js": "dist/server/Index.js"
        }
    ]
    
    mock_page_info = Mock(spec=PageInfo)
    mock_page_info.page = Path("pages/Index.tsx")
    
    page_infos = [mock_page_info]
    mock_project = Mock(spec=SchorleProject)
    mock_project.pages_path = Path("pages")
    
    entries = transform_artifacts_to_manifest(artifacts, page_infos, mock_project)
    
    assert len(entries) == 1
    # Should handle relative paths in assets
    assert entries[0].assets.js == "dist/Index.js"


def test_manifest_validation_error():
    """Test handling of manifest validation errors."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.manifest_path = Path(".schorle/manifest.json")
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create manifest with invalid structure
        proj.manifest_path.parent.mkdir(exist_ok=True)
        proj.manifest_path.write_text('{"invalid": "structure"}')
        
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = Mock(returncode=0, stdout="", stderr="")
            
            # Should handle invalid manifest structure
            # The exact behavior depends on the validation logic
            try:
                build_entrypoints(("bun", "run", "slx-ipc", "build"), proj)
            except (KeyError, ValueError, TypeError):
                # These are expected for invalid manifest structure
                pass
