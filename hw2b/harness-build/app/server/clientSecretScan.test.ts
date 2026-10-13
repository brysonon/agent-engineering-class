import { mkdtemp, readFile, readdir, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterEach, describe, expect, it } from "vitest";
import { build } from "vite";
import react from "@vitejs/plugin-react";

let temporaryDirectory: string | undefined;
afterEach(async () => { if (temporaryDirectory) await rm(temporaryDirectory, { recursive: true, force: true }); });

async function files(directory: string): Promise<string[]> {
  const entries = await readdir(directory, { withFileTypes: true });
  return (await Promise.all(entries.map((entry) => entry.isDirectory() ? files(path.join(directory, entry.name)) : [path.join(directory, entry.name)]))).flat();
}

describe("client bundle", () => {
  it("contains neither an API-key sentinel nor server environment names", async () => {
    temporaryDirectory = await mkdtemp(path.join(tmpdir(), "conference-compass-client-"));
    process.env.OPENAI_API_KEY = "sk-test-client-bundle-sentinel";
    await build({
      root: path.resolve("app/client"), plugins: [react()], logLevel: "silent",
      build: { outDir: temporaryDirectory, emptyOutDir: true }
    });
    const bundle = (await Promise.all((await files(temporaryDirectory)).map((file) => readFile(file, "utf8")))).join("\n");
    expect(bundle).not.toContain("sk-test-client-bundle-sentinel");
    expect(bundle).not.toContain("OPENAI_API_KEY");
    expect(bundle).not.toContain("api.openai.com");
  });
});
