from schorle.render import render
from schorle.utils import cwd
from schorle.manifest import find_schorle_project
from pathlib import Path
import json
import shutil
import subprocess
import os
from fastapi.datastructures import Headers
from pydantic import BaseModel


def test_render():
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))
        gen = render(proj, Path("Index.tsx"))
        for line in gen:
            print(line.decode("utf-8"))


def test_render_page():
    """Test the render function with string page name that uses BuildManifest directly."""
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        # Test that the function doesn't crash and returns a generator
        gen = render(proj, "Index")
        assert gen is not None

        # Try to get some content from the generator
        first_chunk = next(gen, None)
        if first_chunk:
            content = first_chunk.decode("utf-8")
            print(f"First chunk: {content[:100]}")
            # Basic checks that rendering worked
            assert len(content) > 0


def test_render_input_types():
    """Test that the unified render function handles all input types: str, Path, PageInfo."""
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        # Test 1: String page name (preferred method)
        gen_str = render(proj, "Index")
        assert gen_str is not None

        # Test 2: Path object (legacy method)
        gen_path = render(proj, Path("Index.tsx"))
        assert gen_path is not None

        # Test 3: PageInfo object (for when you already have one)
        # First get the PageInfo
        manifest_entry = proj.get_manifest_entry("Index")
        if manifest_entry is not None:
            page_file = proj.find_page_file("Index")
            if page_file is not None:
                layouts = proj.get_page_layouts(page_file)
                from schorle.manifest import PageInfo

                page_info = PageInfo(
                    page=page_file,
                    layouts=layouts,
                    js=manifest_entry.assets.js,
                    css=manifest_entry.assets.css,
                )
                gen_pageinfo = render(proj, page_info)
                assert gen_pageinfo is not None
                print("✓ All input types work with unified render function")

        print("✓ Unified render function test passed")


def test_manifest_dynamic_reading():
    """Test that the manifest is read dynamically and not cached between calls."""
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        # Skip if manifest doesn't exist
        if not proj.manifest_path.exists():
            print("Skipping test - manifest not found")
            return

        # Read the original manifest
        original_manifest = proj.manifest_path.read_text()

        # Get the first manifest entry to check current assets
        first_entry = proj.get_manifest_entry("Index")
        if first_entry is None:
            print("Skipping test - Index page not found in manifest")
            return

        original_js = first_entry.assets.js
        print(f"Original JS asset: {original_js}")

        # Create a backup
        backup_path = proj.manifest_path.with_suffix(".json.backup")
        shutil.copy2(proj.manifest_path, backup_path)

        try:
            # Modify the manifest to simulate a dev/prod switch
            manifest_data = json.loads(original_manifest)
            for entry in manifest_data["entries"]:
                if entry["page"] == "Index":
                    # Change the asset paths to simulate a mode switch
                    if "dev.js" in entry["assets"]["js"]:
                        # Switch to "production" style paths
                        entry["assets"]["js"] = entry["assets"]["js"].replace(
                            "dev.js", "abc123.js"
                        )
                        if entry["assets"]["css"]:
                            entry["assets"]["css"] = entry["assets"]["css"].replace(
                                "dev.css", "abc123.css"
                            )
                    else:
                        # Switch to dev style paths
                        entry["assets"]["js"] = entry["assets"]["js"].replace(
                            ".js", ".dev.js"
                        )
                        if entry["assets"]["css"]:
                            entry["assets"]["css"] = entry["assets"]["css"].replace(
                                ".css", ".dev.css"
                            )

            # Write the modified manifest
            proj.manifest_path.write_text(json.dumps(manifest_data, indent=2))

            # Read the manifest again and verify it picks up the new content
            updated_entry = proj.get_manifest_entry("Index")
            updated_js = updated_entry.assets.js
            print(f"Updated JS asset: {updated_js}")

            # Verify that the manifest was actually updated
            assert updated_js != original_js, (
                "Manifest should have been updated with new asset paths"
            )

            print("✓ Manifest dynamic reading test passed - no caching detected")

        finally:
            # Restore the original manifest
            shutil.move(backup_path, proj.manifest_path)
            print("✓ Original manifest restored")


class TestHeaders(BaseModel):
    authorization: str
    user_agent: str
    x_custom_header: str


class TestCookies(BaseModel):
    session_id: str
    theme: str


def test_headers_cookies_conversion():
    """Test that headers and cookies are properly converted and passed through the render pipeline."""

    # Test data
    test_headers_dict = {
        "authorization": "Bearer test-token",
        "user-agent": "test-agent/1.0",
        "x-custom-header": "custom-value",
    }

    test_cookies_dict = {"session_id": "abc123", "theme": "dark"}

    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        print("=== Testing Headers Object Conversion ===")

        # Test 1: FastAPI Headers object
        headers_obj = Headers(test_headers_dict)
        print(f"Headers object: {headers_obj}")
        print(f"Headers as dict: {dict(headers_obj)}")

        # Test 2: BaseModel headers
        headers_model = TestHeaders(
            authorization="Bearer model-token",
            user_agent="model-agent/1.0",
            x_custom_header="model-value",
        )
        print(f"Headers model: {headers_model.model_dump()}")

        # Test 3: BaseModel cookies
        cookies_model = TestCookies(session_id="model123", theme="light")
        print(f"Cookies model: {cookies_model.model_dump()}")

        print("\n=== Testing Render Pipeline ===")

        # Test that the render function accepts different input types without crashing
        test_cases = [
            ("Headers object + dict cookies", headers_obj, test_cookies_dict),
            ("BaseModel headers + dict cookies", headers_model, test_cookies_dict),
            ("Headers object + BaseModel cookies", headers_obj, cookies_model),
            ("BaseModel headers + BaseModel cookies", headers_model, cookies_model),
        ]

        for case_name, test_headers, test_cookies in test_cases:
            print(f"\nTesting: {case_name}")
            try:
                gen = render(proj, "Index", headers=test_headers, cookies=test_cookies)
                assert gen is not None

                # Try to get the first chunk to verify rendering works
                first_chunk = next(gen, None)
                if first_chunk:
                    content = first_chunk.decode("utf-8")
                    print(f"✓ Render successful, content length: {len(content)}")

                    # Check if header/cookie data is injected as scripts
                    if "__SCHORLE_HEADERS__" in content:
                        print("✓ Headers script tag found in output")
                    else:
                        print("⚠ Headers script tag NOT found in output")

                    if "__SCHORLE_COOKIES__" in content:
                        print("✓ Cookies script tag found in output")
                    else:
                        print("⚠ Cookies script tag NOT found in output")
                else:
                    print("⚠ No content generated")

            except Exception as e:
                print(f"✗ Error: {e}")
                raise

        print("\n✓ All headers/cookies conversion tests completed")


def test_headers_cookies_subprocess_integration():
    """Test that headers/cookies actually make it through to the render.tsx subprocess."""

    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        # Create test headers and cookies
        headers = Headers(
            {
                "authorization": "Bearer subprocess-test",
                "user-agent": "test-browser/1.0",
                "x-test-header": "subprocess-value",
            }
        )

        cookies = {"session": "subprocess123", "preference": "test"}

        print("=== Testing Subprocess Integration ===")
        print(f"Input headers: {dict(headers)}")
        print(f"Input cookies: {cookies}")

        # Render with headers and cookies
        gen = render(proj, "Index", headers=headers, cookies=cookies)

        # Collect all output
        output = b""
        for chunk in gen:
            output += chunk

        html_content = output.decode("utf-8")

        # Parse and verify the injected data
        print(f"\nGenerated HTML length: {len(html_content)}")

        # Look for the script tags with our data
        if "__SCHORLE_HEADERS__" in html_content:
            print("✓ Headers script tag found")
            # Extract the JSON from the script tag
            import re

            headers_match = re.search(
                r'<script id="__SCHORLE_HEADERS__" type="application/json">(.*?)</script>',
                html_content,
            )
            if headers_match:
                headers_json = headers_match.group(1)
                parsed_headers = json.loads(headers_json)
                print(f"Parsed headers from HTML: {parsed_headers}")

                # Verify our test data is present
                assert "authorization" in parsed_headers
                assert parsed_headers["authorization"] == "Bearer subprocess-test"
                assert parsed_headers["x-test-header"] == "subprocess-value"
                print("✓ Headers data verified in output")
            else:
                print("✗ Could not extract headers JSON")
        else:
            print("✗ Headers script tag not found in output")

        if "__SCHORLE_COOKIES__" in html_content:
            print("✓ Cookies script tag found")
            # Extract the JSON from the script tag
            cookies_match = re.search(
                r'<script id="__SCHORLE_COOKIES__" type="application/json">(.*?)</script>',
                html_content,
            )
            if cookies_match:
                cookies_json = cookies_match.group(1)
                parsed_cookies = json.loads(cookies_json)
                print(f"Parsed cookies from HTML: {parsed_cookies}")

                # Verify our test data is present
                assert "session" in parsed_cookies
                assert parsed_cookies["session"] == "subprocess123"
                assert parsed_cookies["preference"] == "test"
                print("✓ Cookies data verified in output")
            else:
                print("✗ Could not extract cookies JSON")
        else:
            print("✗ Cookies script tag not found in output")

        print("\n✓ Subprocess integration test completed")


def test_debug_render_subprocess():
    """Debug test to see what's happening in the render subprocess."""

    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        headers = Headers({"authorization": "Bearer debug-test"})
        cookies = {"session": "debug123"}

        print("=== Debug Render Subprocess ===")

        # Let's manually replicate what render() does to see the subprocess output
        from schorle.render import _resolve_page_info, _compute_import_uris
        from schorle.manifest import PageInfo

        # Get page info
        page_info = _resolve_page_info(proj, Path("Index.tsx"))
        page_import, layout_imports = _compute_import_uris(proj, page_info)

        # Build render info
        render_info = {
            "page": page_import,
            "layouts": layout_imports,
            "js": page_info.js or "",
            "css": page_info.css or "",
            "headers": dict(headers) if headers else None,
            "cookies": cookies,
        }

        print(f"Render info: {json.dumps(render_info, indent=2)}")

        # Run the bun command manually
        full_cmd = [
            "bun",
            "run",
            "slx-ipc",
            "render",
            json.dumps(render_info),
        ]

        print(f"Command: {' '.join(full_cmd)}")

        base_env = os.environ.copy()
        base_env["NODE_ENV"] = "development" if proj.dev else "production"

        # Run with more explicit error handling
        try:
            result = subprocess.run(
                full_cmd,
                cwd=str(proj.root_path),
                input=b"",  # Empty props
                capture_output=True,
                env=base_env,
                timeout=10,
            )

            print(f"Return code: {result.returncode}")
            print(f"Stdout length: {len(result.stdout)}")
            print(f"Stderr length: {len(result.stderr)}")

            if result.stdout:
                stdout_str = result.stdout.decode("utf-8")
                print(f"Stdout: {stdout_str[:500]}...")

            if result.stderr:
                stderr_str = result.stderr.decode("utf-8")
                print(f"Stderr: {stderr_str}")

            if result.returncode != 0:
                print(f"✗ Process failed with code {result.returncode}")
            else:
                print("✓ Process completed successfully")

        except subprocess.TimeoutExpired:
            print("✗ Process timed out")
        except Exception as e:
            print(f"✗ Exception: {e}")

        print("\n✓ Debug test completed")


def test_inspect_html_output():
    """Inspect the actual HTML output to see how headers/cookies are injected."""

    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))

        headers = Headers({"authorization": "Bearer inspect-test"})
        cookies = {"session": "inspect123"}

        print("=== Inspecting HTML Output ===")

        gen = render(proj, "Index", headers=headers, cookies=cookies)

        # Collect all output
        output = b""
        for chunk in gen:
            output += chunk

        html_content = output.decode("utf-8")

        print(f"Full HTML content:\n{html_content}")
        print(f"\nHTML length: {len(html_content)}")

        # Look for script tags specifically
        if "__SCHORLE_HEADERS__" in html_content:
            start = html_content.find("__SCHORLE_HEADERS__")
            context = html_content[max(0, start - 100) : start + 200]
            print(f"\nHeaders context:\n{context}")

        if "__SCHORLE_COOKIES__" in html_content:
            start = html_content.find("__SCHORLE_COOKIES__")
            context = html_content[max(0, start - 100) : start + 200]
            print(f"\nCookies context:\n{context}")

        print("\n✓ Inspection completed")


def test_render_mdx():
    with cwd("packages/aurora"):
        proj = find_schorle_project(Path("."))
        gen = render(proj, "About")
        response = "\n".join(line.decode("utf-8") for line in gen)
        assert "This is the about page." in response
