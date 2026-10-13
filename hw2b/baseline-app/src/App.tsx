import { FormEvent, useEffect, useRef, useState } from "react";

type Source = { passageId: string; talkId: string; title: string; speaker: string; role: string; url: string; excerpt: string };
type Answer = { evidenceStatus: "sufficient" | "limited" | "none"; answer: string; themes: Array<{ title: string; synthesis: string; passageIds: string[] }>; closingNote: string; coverage: number; totalTalks: number; sources: Source[] };

const examples = [
  "What was taught about faith during trials?",
  "How can I become more Christlike?",
  "What did leaders teach about covenants?",
  "What was said about gambling?",
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState<Answer | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [phase, setPhase] = useState("");
  const resultsRef = useRef<HTMLElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => { if (answer || error) resultsRef.current?.focus(); }, [answer, error]);

  async function submit(event?: FormEvent) {
    event?.preventDefault();
    const clean = question.trim();
    if (clean.length < 3 || clean.length > 500) { setError("Enter a question between 3 and 500 characters."); setAnswer(null); return; }
    setLoading(true); setError(""); setAnswer(null); setPhase("Searching 37 talks…");
    const timer = window.setTimeout(() => setPhase("Bringing the teachings together…"), 900);
    try {
      const response = await fetch("/api/search", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question: clean }) });
      const data = await response.json();
      if (!response.ok) throw new Error(data.error || "Search failed.");
      setAnswer(data);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The search could not be completed.");
    } finally {
      window.clearTimeout(timer); setLoading(false); setPhase("");
    }
  }

  function askAgain() { setAnswer(null); setError(""); setQuestion(""); requestAnimationFrame(() => inputRef.current?.focus()); }
  const sourceById = new Map(answer?.sources.map((source) => [source.passageId, source]) ?? []);

  return <>
    <header className="site-header">
      <div className="brand"><span className="compass" aria-hidden="true">✦</span><span>Conference Compass</span></div>
      <span className="dataset">October 2026 · 37 talks</span>
    </header>
    <main>
      <section className="hero" aria-labelledby="page-title">
        <p className="eyebrow">Study across the whole conference</p>
        <h1 id="page-title">Find the shared teachings.</h1>
        <p className="intro">Ask a question and explore a sourced synthesis of messages from October 2026 general conference.</p>
        <form onSubmit={submit} className="search-card">
          <label htmlFor="question">What would you like to understand?</label>
          <textarea ref={inputRef} id="question" value={question} maxLength={500} onChange={(event) => setQuestion(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); submit(); } }} placeholder="What did leaders teach about finding peace during uncertainty?" rows={3} disabled={loading} />
          <div className="form-row"><span>{question.length}/500</span><button type="submit" disabled={loading}>{loading ? "Searching…" : "Search conference"}<span aria-hidden="true">→</span></button></div>
        </form>
        <div className="examples" aria-label="Example questions"><span>Try asking</span>{examples.map((example) => <button key={example} onClick={() => { setQuestion(example); setError(""); inputRef.current?.focus(); }}>{example}</button>)}</div>
      </section>

      {(loading || answer || error) && <section className="results" ref={resultsRef} tabIndex={-1} aria-live="polite" aria-busy={loading}>
        {loading && <div className="loading"><span className="loader" aria-hidden="true" /><p>{phase}</p></div>}
        {error && <div className="notice error"><p className="eyebrow">Unable to complete the search</p><h2>Something needs attention</h2><p>{error}</p><button onClick={() => inputRef.current?.focus()}>Return to question</button></div>}
        {answer && <>
          <div className="result-heading"><div><p className="eyebrow">Your question</p><h2>{question}</h2></div><span className={`status ${answer.evidenceStatus}`}>{answer.evidenceStatus} evidence</span></div>
          <div className="answer-lead"><p>{answer.answer}</p><span>Evidence from {answer.coverage} of {answer.totalTalks} talks</span></div>
          {answer.themes.length > 0 && <div className="theme-grid">{answer.themes.map((theme, index) => <article className="theme" key={`${theme.title}-${index}`}><span className="theme-number">0{index + 1}</span><h3>{theme.title}</h3><p>{theme.synthesis}</p><div className="citations">{theme.passageIds.map((id) => { const source = sourceById.get(id); return source ? <a key={id} href={`#source-${id}`} aria-label={`Source: ${source.title} by ${source.speaker}`}>{source.speaker}</a> : null; })}</div></article>)}</div>}
          {answer.sources.length > 0 && <section className="sources" aria-labelledby="sources-title"><p className="eyebrow">Go to the source</p><h2 id="sources-title">Talks used in this answer</h2><div>{answer.sources.map((source) => <article id={`source-${source.passageId}`} key={source.passageId} className="source"><blockquote>“{source.excerpt}”</blockquote><p><strong>{source.speaker}</strong>{source.role && <span>{source.role}</span>}</p><a href={source.url} target="_blank" rel="noreferrer">{source.title} <span aria-hidden="true">↗</span></a></article>)}</div></section>}
          <p className="closing">{answer.closingNote}</p><button className="again" onClick={askAgain}>Ask another question</button>
        </>}
      </section>}
    </main>
    <footer><p>Independent class project. Generated summaries may be incomplete; read each cited talk in context.</p></footer>
  </>;
}
