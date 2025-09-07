from pathlib import Path
from schorle.registry import registry


def test_registry(tmp_path: Path):
    # create a simple pages directory
    (tmp_path / "pages").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "Index.tsx").write_text(
        "export default function Index() { return <div>Index</div> }"
    )
    (tmp_path / "pages" / "About.tsx").write_text(
        "export default function About() { return <div>About</div> }"
    )

    # add nested pages directory
    (tmp_path / "pages" / "nested").mkdir(parents=True, exist_ok=True)
    (tmp_path / "pages" / "nested" / "Index.tsx").write_text(
        "export default function NestedIndex() { return <div>NestedIndex</div> }"
    )
    (tmp_path / "pages" / "nested" / "About.tsx").write_text(
        "export default function NestedAbout() { return <div>NestedAbout</div> }"
    )

    # run the registry command
    registry(
        tmp_path / "pages",
        ts_out=tmp_path / "registry.ts",
        py_out=tmp_path / "registry.py",
    )

    # check the registry files
    assert (tmp_path / "registry.py").exists()
    assert (tmp_path / "registry.ts").exists()

    # TODO: add content-based assertions
