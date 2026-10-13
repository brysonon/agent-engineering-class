// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from "vitest";
import "@testing-library/jest-dom/vitest";
import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { AnswerResponse } from "../../shared/contracts";
import { App } from "./App";

afterEach(() => { cleanup(); vi.restoreAllMocks(); });

const result = (status: AnswerResponse["evidenceStatus"]): AnswerResponse => ({
  requestId: "request", question: "Faith?", evidenceStatus: status,
  answer: status === "none" ? "The October 2026 conference corpus does not directly address this question." : "A grounded answer.",
  themes: status === "none" ? [] : [{ title: "Faith", synthesis: "Trust grows through trials.", sourceIds: ["p1"] }],
  closingNote: "Read the source in context.", usedTalkCount: status === "none" ? 0 : 1,
  sources: status === "none" ? [] : [{ id: "talk1", speaker: "A Speaker", title: "A Talk", canonicalUrl: "https://www.churchofjesuschrist.org/study/x", passages: [{ id: "p1", excerpt: "Trust grows through trials." }] }]
});

function mockFetch(answerResponse: Response | Promise<Response>) {
  vi.stubGlobal("fetch", vi.fn()
    .mockResolvedValueOnce(new Response(JSON.stringify({ corpusReady: true, apiConfigured: true }), { status: 200 }))
    .mockImplementationOnce(() => answerResponse));
}

describe("App", () => {
  it("exposes empty and oversized validation", async () => {
    mockFetch(new Response(JSON.stringify(result("none"))));
    const user = userEvent.setup(); render(<App />);
    await user.click(screen.getByRole("button", { name: "Search conference" }));
    expect(screen.getByRole("alert")).toHaveTextContent("Enter a question");
    fireEvent.change(screen.getByLabelText("Question or topic"), { target: { value: "x".repeat(1001) } });
    await user.click(screen.getByRole("button", { name: "Search conference" }));
    expect(screen.getByRole("alert")).toHaveTextContent("1,000 characters");
  });

  it.each(["sufficient", "limited", "none"] as const)("renders the %s evidence state", async (status) => {
    mockFetch(new Response(JSON.stringify(result(status)), { status: 200, headers: { "content-type": "application/json" } }));
    const user = userEvent.setup(); render(<App />);
    await user.type(screen.getByLabelText("Question or topic"), "Faith?");
    await user.click(screen.getByRole("button", { name: "Search conference" }));
    expect(await screen.findByText(status === "sufficient" ? "Sufficient evidence" : status === "limited" ? "Limited evidence" : "No direct evidence")).toBeInTheDocument();
    expect(screen.getByText(`Used evidence from ${status === "none" ? 0 : 1} of 37 talks`)).toBeInTheDocument();
  });

  it("announces loading, blocks duplicate submission, and renders server errors", async () => {
    let resolve!: (value: Response) => void;
    const pending = new Promise<Response>((done) => { resolve = done; });
    mockFetch(pending);
    const user = userEvent.setup(); render(<App />);
    await user.type(screen.getByLabelText("Question or topic"), "Faith?");
    await user.click(screen.getByRole("button", { name: "Search conference" }));
    expect(screen.getByText("Searching 37 talks…")).toBeInTheDocument();
    expect(screen.getByLabelText("Question or topic")).toBeDisabled();
    resolve(new Response(JSON.stringify({ code: "synthesis_failed", message: "The synthesis service is temporarily unavailable." }), { status: 502 }));
    const errorHeading = await screen.findByRole("heading", { name: "We couldn’t complete that search" });
    expect(screen.getByRole("alert")).toHaveTextContent("temporarily unavailable");
    expect(errorHeading).toHaveFocus();
    await user.tab();
    const retry = screen.getByRole("button", { name: "Try again" });
    expect(retry).toHaveFocus();
    await user.keyboard("{Enter}");
    await waitFor(() => expect(screen.getByLabelText("Question or topic")).toHaveFocus());
  });

  it("renders one talk card with distinct passage anchors and excerpts", async () => {
    const grouped = result("sufficient");
    grouped.themes = [{ title: "Faith", synthesis: "Two supported ideas.", sourceIds: ["p1", "p2"] }];
    grouped.usedTalkCount = 1;
    grouped.sources = [{
      id: "talk1", speaker: "A Speaker", title: "One Talk", canonicalUrl: "https://www.churchofjesuschrist.org/study/x",
      passages: [{ id: "p1", excerpt: "First exact source excerpt." }, { id: "p2", excerpt: "Second exact source excerpt." }]
    }];
    mockFetch(new Response(JSON.stringify(grouped), { status: 200 }));
    const user = userEvent.setup(); render(<App />);
    await user.type(screen.getByLabelText("Question or topic"), "Faith?");
    await user.click(screen.getByRole("button", { name: "Search conference" }));
    expect(await screen.findByText("Used evidence from 1 of 37 talks")).toBeInTheDocument();
    expect(screen.getAllByRole("link", { name: "Read the full talk (opens in a new tab)" })).toHaveLength(1);
    expect(screen.getAllByRole("blockquote")).toHaveLength(2);
    expect(document.getElementById("source-p1")).not.toBeNull();
    expect(document.getElementById("source-p2")).not.toBeNull();
  });
});
