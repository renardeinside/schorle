import Link from "next/link";
import {} from "@/components/ui/card";
import { File, Folder, Files } from "fumadocs-ui/components/files";
import { Code } from "lucide-react";
import { CodeEditor } from "@/components/ui/shadcn-io/code-editor";
import { InteractiveHoverButton } from "@/components/magicui/interactive-hover-button";
import Image from "next/image";
import { AuroraText } from "@/components/magicui/aurora-text";
import { cn } from "@/lib/utils";
import { spaceMono } from "@/components/Logo";
import { Button } from "@/components/ui/button";

export default function HomePage() {
  return (
    <main className="flex flex-1 flex-col items-center justify-center px-4">
      {/* Header Section */}
      <div className="text-center mb-16 max-w-4xl mx-auto h-screen justify-center items-center flex flex-col space-y-6">
        <div className="flex items-center gap-2 mb-6">
          <Image src="/logo.svg" alt="Logo" width={96} height={96} />
          <AuroraText className={cn(spaceMono.className, "text-6xl font-bold")}>
            Schorle
          </AuroraText>
        </div>
        <h1 className="mb-6 text-4xl font-semibold leading-tight text-balance">
          The Foundation Layer for your Data and AI Applications
        </h1>

        <p className="text-md leading-relaxed text-balance">
          A hybrid framework that bridges Python backend development with
          powerful frontend. <br />
          Open Source and Open Code, based on FastAPI, NextJS and Shadcn UI.
        </p>

        <div className="flex flex-col sm:flex-row gap-4 justify-center">
          <Link href="/docs">
            <InteractiveHoverButton className="text-xl font-bold px-10 py-4">
              Explore Docs
            </InteractiveHoverButton>
          </Link>
          <Link href="/docs/quickstart">
            <Button className="text-xl font-bold px-10 py-4 bg-primary text-primary-foreground h-full cursor-pointer rounded-full">
              Quickstart
            </Button>
          </Link>
        </div>
      </div>

      {/* Code Example & File Structure Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 max-w-7xl mx-auto mb-20">
        {/* File Structure */}
        <div className="space-y-6">
          <div className="text-center lg:text-left">
            <h2 className="text-3xl font-bold mb-3">
              Simple Project Structure
            </h2>
            <p className="text-muted-foreground text-lg">
              Organize your Python backend and NextJS frontend in a unified
              project structure.
            </p>
          </div>

          <Files>
            <Folder name="aurora (sample project name)" defaultOpen>
              <Folder name="backend" defaultOpen>
                <File name="app.py" />
                <Folder name="models">
                  <File name="user.py" />
                </Folder>
              </Folder>
              <Folder name="ui" defaultOpen>
                <Folder name="app" defaultOpen>
                  <Folder name="components">
                    <File name="button.tsx" />
                  </Folder>
                  <Folder name="pages" defaultOpen>
                    <File name="Index.tsx" />
                    <File name="Profile.tsx" />
                  </Folder>
                </Folder>
              </Folder>
            </Folder>
          </Files>
        </div>

        {/* Code Example */}
        <div className="space-y-6">
          <div className="text-center lg:text-left">
            <h2 className="text-3xl font-bold mb-3">Seamless Integration</h2>
            <p className="text-muted-foreground text-lg">
              Write Python backends and React/JSX frontends that work together
              perfectly.
            </p>
          </div>

          <div className="space-y-4">
            {/* Python Code */}
            <CodeEditor
              cursor={false}
              className="w-full min-h-[480px]"
              lang="python"
              title="app.py"
              icon={<Code />}
              writing={false}
              copyButton
            >
              {`from fastapi import FastAPI
from aurora.ui import pages, ui
from aurora import models
app = FastAPI()

ui.mount(app)
ui.add_to_model_registry(models)

@app.get("/")
def index():
    return ui.render(pages.Index)

@app.get("/stats")
def stats():
    return ui.render(
      pages.Stats, 
      props=models.Stats(total_users=100, last_updated_at=datetime.now())
    )

}`}
            </CodeEditor>

            <CodeEditor
              cursor={false}
              className="w-full min-h-[480px]"
              lang="tsx"
              title="pages/Index.tsx"
              icon={<Code />}
              writing={false}
              copyButton
            >
              {`import { getProps } from "@/lib/props";

              // types are automatically generated from the Python backend
              import { Stats } from "@/lib/types";
// shadcn/ui included by default
import {Button} from "@/components/ui/button"; 

export default function Index() {
  // server-side parameter passing
  const { totalUsers, lastUpdatedAt } = getProps<Stats>();

  return (
    <div>
      <h1>Stats</h1>
      <p>Total users: {totalUsers}</p>
      <p>Last updated at: {lastUpdatedAt}</p>
    </div>
  );
}`}
            </CodeEditor>
          </div>
        </div>
      </div>

      {/* Call to action */}
      <div className="text-center flex flex-col gap-4 justify-center items-center h-screen">
        <h3 className="text-4xl leading-tight mb-20">
          Get started with{" "}
          <AuroraText className={cn(spaceMono.className, "font-bold")}>
            Schorle
          </AuroraText>{" "}
          today
        </h3>
        <Link href="/docs/quickstart">
          <Button className="text-xl font-bold px-10 py-4 bg-primary text-primary-foreground h-full cursor-pointer rounded-full">
            Quickstart
          </Button>
        </Link>
      </div>

      {/* Footer */}
      <div className="text-center flex flex-col gap-4 justify-center items-center py-10">
        <p className="text-muted-foreground text-sm">
          Crafted with precision in Berlin. Open-sourced under MIT license.
        </p>
      </div>
    </main>
  );
}
