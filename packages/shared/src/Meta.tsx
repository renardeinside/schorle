export function Meta({ storageKey = "theme" }: { storageKey?: string }) {
  const code = `(function() {
      try {
        var k = ${JSON.stringify(storageKey)};
        var s = localStorage.getItem(k);
        var m = window.matchMedia("(prefers-color-scheme: dark)");
        var t = s || (m.matches ? "dark" : "light");
        if (t === "system") t = m.matches ? "dark" : "light";
        var r = document.documentElement;
        if (t === "dark") r.classList.add("dark");
        else r.classList.remove("dark");
      } catch(e) {}
    })();`;

  return <script dangerouslySetInnerHTML={{ __html: code }} />;
}
