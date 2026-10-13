import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from "react";
import type { AnswerResponse } from "../../shared/contracts";
import { MAX_QUESTION_CODEPOINTS } from "../../shared/constants";
import { ApiError, askConference, fetchStatus } from "./api";

export const EXAMPLES = [
  "What was taught about faith during trials?",
  "How can I become more Christlike?",
  "What did leaders teach about covenants?",
  "What was said about gambling?"
];

type State = { kind: "idle" } | { kind: "loading"; message: string } | { kind: "success"; result: AnswerResponse } | { kind: "error"; code: string; message: string };

function Sources({ result }: { result: AnswerResponse }) {
  return <section aria-labelledby="sources-heading" className="sources">
    <h3 id="sources-heading">Sources</h3>
    <ol>
      {result.sources.map((source) => <li key={source.canonicalUrl} className="source-card">
        <p className="source-title"><strong>{source.speaker}</strong> · <cite>{source.title}</cite></p>
        <div className="passage-evidence">{source.passages.map((passage) => <div key={passage.id} id={`source-${encodeURIComponent(passage.id)}`}>
          {passage.excerpt ? <blockquote>“{passage.excerpt}”</blockquote> : <p className="no-excerpt">Cited passage; no short exact excerpt is available.</p>}
        </div>)}</div>
        <a href={source.canonicalUrl} target="_blank" rel="noopener noreferrer">Read the full talk (opens in a new tab)</a>
      </li>)}
    </ol>
  </section>;
}

function Results({ result, onReset, headingRef }: { result: AnswerResponse; onReset: () => void; headingRef: React.RefObject<HTMLHeadingElement | null> }) {
  const labels = { sufficient: "Sufficient evidence", limited: "Limited evidence", none: "No direct evidence" };
  const sourceById = new Map(result.sources.flatMap((source, index) => source.passages.map((passage) => [passage.id, { source, index }] as const)));
  const answerSourceIds = [...new Set(result.themes.flatMap((theme) => theme.sourceIds))];
  return <section className="results" aria-labelledby="result-heading">
    <p className={`evidence evidence-${result.evidenceStatus}`}>{labels[result.evidenceStatus]}</p>
    <h2 id="result-heading" ref={headingRef} tabIndex={-1}>Conference teachings for your question</h2>
    <p className="question-restatement">“{result.question}”</p>
    <div className="combined-answer"><p>{result.answer}</p>{answerSourceIds.length > 0 && <p className="citations" aria-label="Sources supporting the combined answer">{answerSourceIds.map((id) => {
      const entry = sourceById.get(id);
      return entry ? <a key={id} href={`#source-${encodeURIComponent(id)}`} aria-label={`Source ${entry.index + 1}: ${entry.source.title}`}>[{entry.index + 1}]</a> : null;
    })}</p>}</div>
    {result.themes.length > 0 && <section aria-labelledby="themes-heading">
      <h3 id="themes-heading">Themes in the conference</h3>
      <div className="theme-grid">{result.themes.map((theme) => <article className="theme-card" key={theme.title}>
        <h4>{theme.title}</h4><p>{theme.synthesis}</p>
        <p className="citations" aria-label="Supporting sources">{theme.sourceIds.map((id) => {
          const entry = sourceById.get(id);
          return entry ? <a key={id} href={`#source-${encodeURIComponent(id)}`} aria-label={`Source ${entry.index + 1}: ${entry.source.title}`}>[{entry.index + 1}]</a> : null;
        })}</p>
      </article>)}</div>
    </section>}
    <p className="coverage">Used evidence from {result.usedTalkCount} of 37 talks</p>
    {result.sources.length > 0 && <Sources result={result} />}
    {result.evidenceStatus === "none" && <p className="try-again">Try one of the example prompts above to explore a conference topic.</p>}
    <p className="closing">{result.closingNote}</p>
    <p className="disclaimer">Generated summaries may be incomplete. Follow the citations to read each talk in context.</p>
    <button type="button" className="secondary" onClick={onReset}>Ask another question</button>
  </section>;
}

export function App() {
  const [question, setQuestion] = useState("");
  const [validation, setValidation] = useState("");
  const [state, setState] = useState<State>({ kind: "idle" });
  const [readiness, setReadiness] = useState<string>("");
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const headingRef = useRef<HTMLHeadingElement>(null);
  const errorHeadingRef = useRef<HTMLHeadingElement>(null);
  const activeRef = useRef(false);

  useEffect(() => {
    void fetchStatus().then((status) => {
      if (!status.corpusReady) setReadiness("The corpus is not imported. Run npm run import, then restart the server.");
      else if (!status.apiConfigured) setReadiness("OpenAI configuration is required. Follow .env.example, then restart the server.");
    }).catch(() => setReadiness("Server status is unavailable. Start the app with npm run dev."));
  }, []);
  useEffect(() => {
    if (state.kind === "success") headingRef.current?.focus();
    if (state.kind === "error") errorHeadingRef.current?.focus();
  }, [state.kind]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    if (activeRef.current) return;
    const trimmed = question.trim();
    const length = [...trimmed].length;
    if (!trimmed) { setValidation("Enter a question to search the conference."); inputRef.current?.focus(); return; }
    if (length > MAX_QUESTION_CODEPOINTS) { setValidation(`Keep your question to ${MAX_QUESTION_CODEPOINTS.toLocaleString()} characters or fewer.`); inputRef.current?.focus(); return; }
    setValidation(""); activeRef.current = true; setState({ kind: "loading", message: "Searching 37 talks…" });
    const timer = window.setTimeout(() => setState((current) => current.kind === "loading" ? { kind: "loading", message: "Bringing the teachings together…" } : current), 800);
    try { setState({ kind: "success", result: await askConference(trimmed) }); }
    catch (error) {
      setState({ kind: "error", code: error instanceof ApiError ? error.code : "server_error", message: error instanceof Error ? error.message : "The search failed. Please try again." });
    } finally { window.clearTimeout(timer); activeRef.current = false; }
  }

  function onKeyDown(event: KeyboardEvent<HTMLTextAreaElement>) {
    if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); void submit(); }
  }
  function reset() { setState({ kind: "idle" }); setQuestion(""); setValidation(""); window.setTimeout(() => inputRef.current?.focus(), 0); }
  function retry() { setState({ kind: "idle" }); window.setTimeout(() => inputRef.current?.focus(), 0); }

  const loading = state.kind === "loading";
  return <>
    <header className="site-header"><div className="header-inner">
      <div><p className="eyebrow">Independent study project</p><h1>Conference Compass</h1><p className="tagline">Explore shared teachings from October 2026 general conference.</p></div>
      <p className="badge">October 2026 · 37 talks</p>
    </div></header>
    <main>
      <section className="search-panel" aria-labelledby="search-heading">
        <h2 id="search-heading">What would you like to study?</h2>
        <p>Ask one question. Conference Compass searches the complete English conference collection and shows the passages behind its summary.</p>
        {readiness && <p className="readiness" role="status">{readiness}</p>}
        <form onSubmit={(event) => void submit(event)} noValidate>
          <label htmlFor="question">Question or topic</label>
          <textarea id="question" ref={inputRef} value={question} disabled={loading} aria-invalid={Boolean(validation)} aria-describedby="question-help question-error" onKeyDown={onKeyDown} onChange={(event) => setQuestion(event.target.value)} rows={3} placeholder="What did leaders teach about…?" />
          <div className="field-meta"><span id="question-help">Enter searches · Shift+Enter adds a line</span><span>{[...question].length} / {MAX_QUESTION_CODEPOINTS}</span></div>
          {validation && <p id="question-error" className="validation" role="alert">{validation}</p>}
          <button className="primary" disabled={loading} type="submit">{loading ? "Searching…" : "Search conference"}</button>
        </form>
        <div className="examples" aria-labelledby="examples-heading"><h3 id="examples-heading">Example questions</h3><div>{EXAMPLES.map((example) => <button type="button" disabled={loading} key={example} onClick={() => { setQuestion(example); setValidation(""); inputRef.current?.focus(); }}>{example}</button>)}</div></div>
      </section>
      <div className="status-region" aria-live="polite" aria-atomic="true">{state.kind === "loading" && <div className="loading"><span className="spinner" aria-hidden="true" />{state.message}</div>}</div>
      {state.kind === "error" && <section className="error-panel" role="alert"><h2 ref={errorHeadingRef} tabIndex={-1}>We couldn’t complete that search</h2><p>{state.message}</p><button type="button" className="secondary" onClick={retry}>Try again</button></section>}
      {state.kind === "success" && <Results result={state.result} onReset={reset} headingRef={headingRef} />}
    </main>
    <footer><p>Conference Compass is an independent class project and is not affiliated with or endorsed by The Church of Jesus Christ of Latter-day Saints.</p></footer>
  </>;
}
