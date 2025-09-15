from schorle.render import render
from schorle.utils import cwd, find_schorle_project
from pathlib import Path
import json
import tempfile
import shutil


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
