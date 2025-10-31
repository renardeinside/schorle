"""Tests for error cases and missing coverage in schorle.render module."""

from pathlib import Path
from unittest.mock import Mock, patch
import pytest
from pydantic import BaseModel
from fastapi.datastructures import Headers

from schorle.render import (
    _compute_import_uris,
    _resolve_page_info,
    render,
)
from schorle.manifest import SchorleProject, PageInfo, BuildManifestEntry, BuildManifestAssets
from schorle.utils import cwd


class HeadersModel(BaseModel):
    authorization: str
    user_agent: str


class CookiesModel(BaseModel):
    session_id: str
    theme: str


def test_compute_import_uris_missing_pages_directory():
    """Test _compute_import_uris with missing pages directory."""
    mock_project = Mock(spec=SchorleProject)
    mock_project.pages_path = Path("/nonexistent/pages")
    mock_project.pages_path.exists.return_value = False
    
    mock_page_info = Mock(spec=PageInfo)
    
    with pytest.raises(FileNotFoundError, match="Missing pages directory"):
        _compute_import_uris(mock_project, mock_page_info)


def test_resolve_page_info_absolute_path():
    """Test _resolve_page_info with absolute path."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.project_root = Path.cwd()
        proj.pages_path = Path.cwd() / "pages"
        
        # Mock page infos
        mock_page_info = Mock(spec=PageInfo)
        mock_page_info.page = proj.pages_path / "Index.tsx"
        proj.collect_page_infos.return_value = [mock_page_info]
        
        # Test with absolute path
        absolute_path = proj.pages_path / "Index.tsx"
        result = _resolve_page_info(proj, absolute_path)
        
        assert result == mock_page_info


def test_resolve_page_info_absolute_path_value_error():
    """Test _resolve_page_info with absolute path that can't be made relative."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.project_root = Path.cwd()
        proj.pages_path = Path.cwd() / "pages"
        
        # Mock page infos
        mock_page_info = Mock(spec=PageInfo)
        mock_page_info.page = proj.pages_path / "Index.tsx"
        proj.collect_page_infos.return_value = [mock_page_info]
        
        # Test with absolute path outside project root
        absolute_path = Path("/completely/different/path/Index.tsx")
        
        with pytest.raises(FileNotFoundError):
            _resolve_page_info(proj, absolute_path)


def test_resolve_page_info_with_pages_prefix():
    """Test _resolve_page_info with path prefixed with 'pages/'."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.project_root = Path.cwd()
        proj.pages_path = Path.cwd() / "pages"
        
        # Mock page infos
        mock_page_info = Mock(spec=PageInfo)
        mock_page_info.page = proj.pages_path / "Index.tsx"
        proj.collect_page_infos.return_value = [mock_page_info]
        
        # Test with pages/ prefix
        path_with_prefix = Path("pages/Index.tsx")
        result = _resolve_page_info(proj, path_with_prefix)
        
        assert result == mock_page_info


def test_resolve_page_info_not_found():
    """Test _resolve_page_info when page is not found."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.project_root = Path.cwd()
        proj.pages_path = Path.cwd() / "pages"
        
        # Empty page infos - nothing found
        proj.collect_page_infos.return_value = []
        
        with pytest.raises(FileNotFoundError, match="Page not found"):
            _resolve_page_info(proj, Path("NonExistent.tsx"))


def test_render_missing_manifest_entry():
    """Test render with string page name not found in manifest."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.get_manifest_entry.return_value = None
        
        with pytest.raises(FileNotFoundError, match="Page not found in manifest"):
            list(render(proj, "NonExistentPage"))


def test_render_missing_page_file():
    """Test render when page file is not found."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        
        # Mock manifest entry but no page file
        mock_entry = Mock(spec=BuildManifestEntry)
        mock_entry.assets = Mock(spec=BuildManifestAssets)
        mock_entry.assets.js = "index.js"
        mock_entry.assets.css = "index.css"
        mock_entry.assets.server_js = "server.js"
        
        proj.get_manifest_entry.return_value = mock_entry
        proj.find_page_file.return_value = None
        
        with pytest.raises(FileNotFoundError, match="Page file not found"):
            list(render(proj, "Index"))


def test_render_no_server_js():
    """Test render when no server JS is available."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        
        # Create PageInfo without server_js
        page_info = PageInfo(
            page=Path("Index.tsx"),
            layouts=[],
            js="index.js",
            css="index.css",
            server_js=""  # No server JS
        )
        
        with pytest.raises(RuntimeError, match="No server-side build available"):
            list(render(proj, page_info))


def test_render_missing_server_js_file():
    """Test render when server JS file doesn't exist on disk."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        
        # Create PageInfo with server_js but file doesn't exist
        page_info = PageInfo(
            page=Path("Index.tsx"),
            layouts=[],
            js="index.js",
            css="index.css",
            server_js="/.schorle/dist/server/nonexistent.js"
        )
        
        with pytest.raises(FileNotFoundError, match="Server JS file not found"):
            list(render(proj, page_info))


def test_render_subprocess_failure():
    """Test render when subprocess fails."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen to fail
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.stdout = None
                mock_popen.return_value = mock_process
                
                with pytest.raises(RuntimeError, match="Failed to render: stdout is None"):
                    list(render(proj, page_info))
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_subprocess_stdin_none():
    """Test render when subprocess stdin is None."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen with stdin=None
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_process.stdout = Mock()
                mock_process.stdin = None
                mock_popen.return_value = mock_process
                
                with pytest.raises(RuntimeError, match="Failed to render: stdin is None"):
                    list(render(proj, page_info))
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_with_props():
    """Test render with props injection."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                # Test with props
                props = b"test props data"
                result = list(render(proj, page_info, props=props))
                
                # Check that props were written to stdin
                mock_stdin.write.assert_called_once_with(props)
                mock_stdin.flush.assert_called_once()
                mock_stdin.close.assert_called()
                
                assert len(result) > 0
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_headers_basemodel():
    """Test render with headers as BaseModel."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                # Test with BaseModel headers
                headers = HeadersModel(authorization="Bearer token", user_agent="test")
                result = list(render(proj, page_info, headers=headers))
                
                assert len(result) > 0
                # Should contain headers injection
                html_content = b"".join(result).decode()
                assert "__SCHORLE_HEADERS__" in html_content
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_cookies_basemodel():
    """Test render with cookies as BaseModel."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                # Test with BaseModel cookies
                cookies = CookiesModel(session_id="abc123", theme="dark")
                result = list(render(proj, page_info, cookies=cookies))
                
                assert len(result) > 0
                # Should contain cookies injection
                html_content = b"".join(result).decode()
                assert "__SCHORLE_COOKIES__" in html_content
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_with_empty_css():
    """Test render when CSS is empty/None."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo without CSS
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="",  # Empty CSS
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                result = list(render(proj, page_info))
                
                assert len(result) > 0
                # Should not inject CSS link since it's empty
                html_content = b"".join(result).decode()
                assert "stylesheet" not in html_content
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_process_error():
    """Test render when subprocess process fails to start."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen to raise an exception
            with patch('subprocess.Popen') as mock_popen:
                mock_popen.side_effect = OSError("Failed to start process")
                
                with pytest.raises(OSError, match="Failed to start process"):
                    list(render(proj, page_info))
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_production_mode():
    """Test render in production mode sets correct NODE_ENV."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = False  # Production mode
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                list(render(proj, page_info))
                
                # Check that NODE_ENV was set to production
                call_args = mock_popen.call_args
                env = call_args[1]['env']
                assert env['NODE_ENV'] == 'production'
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_with_unicode_content():
    """Test render with unicode content in HTML output."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen with unicode content
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                unicode_content = "<html><head></head><body>Hello 世界 🌍</body></html>".encode('utf-8')
                mock_stdout.__iter__ = Mock(return_value=iter([unicode_content]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                result = list(render(proj, page_info))
                
                assert len(result) > 0
                html_content = b"".join(result).decode('utf-8')
                assert "世界" in html_content
                assert "🌍" in html_content
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_large_props():
    """Test render with large props data."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                # Test with large props (1MB of data)
                large_props = b"x" * (1024 * 1024)
                result = list(render(proj, page_info, props=large_props))
                
                # Should handle large props without issues
                mock_stdin.write.assert_called_once_with(large_props)
                assert len(result) > 0
        finally:
            server_js_file.unlink(missing_ok=True)


def test_render_empty_headers_cookies():
    """Test render with empty headers and cookies."""
    with cwd("packages/aurora"):
        proj = Mock(spec=SchorleProject)
        proj.root_path = Path.cwd()
        proj.dev = True
        
        # Create valid PageInfo
        server_js_file = Path("test_server.js")
        server_js_file.write_text("// test")
        
        try:
            page_info = PageInfo(
                page=Path("Index.tsx"),
                layouts=[],
                js="index.js",
                css="index.css",
                server_js=str(server_js_file)
            )
            
            # Mock subprocess.Popen
            with patch('subprocess.Popen') as mock_popen:
                mock_process = Mock()
                mock_stdin = Mock()
                mock_stdout = Mock()
                mock_stdout.__iter__ = Mock(return_value=iter([b"<html><head></head><body></body></html>"]))
                
                mock_process.stdout = mock_stdout
                mock_process.stdin = mock_stdin
                mock_popen.return_value = mock_process
                
                # Test with empty headers and cookies
                result = list(render(proj, page_info, headers=Headers(), cookies={}))
                
                assert len(result) > 0
                html_content = b"".join(result).decode()
                # Should not inject empty headers/cookies scripts
                assert "__SCHORLE_HEADERS__" not in html_content
                assert "__SCHORLE_COOKIES__" not in html_content
        finally:
            server_js_file.unlink(missing_ok=True)
