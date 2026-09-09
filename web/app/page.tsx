"use client";

import { FormEvent, useEffect, useState } from "react";
import { AskResult, askQuestion, checkHealth, indexRepository } from "../lib/api";

type Status = "checking" | "online" | "offline";

export default function Home() {
  const [status, setStatus] = useState<Status>("checking");
  const [path, setPath] = useState(".");
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState<AskResult | null>(null);
  const [indexSummary, setIndexSummary] = useState("");
  const [busy, setBusy] = useState<"index" | "ask" | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    checkHealth()
      .then(() => setStatus("online"))
      .catch(() => setStatus("offline"));
  }, []);

  async function handleIndex(event: FormEvent) {
    event.preventDefault();
    setBusy("index");
    setError("");
    try {
      const response = await indexRepository(path);
      setIndexSummary(`${response.files} files · ${response.chunks} searchable chunks`);
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "Indexing failed.");
    } finally {
      setBusy(null);
    }
  }

  async function handleAsk(event: FormEvent) {
    event.preventDefault();
    if (!question.trim()) return;
    setBusy("ask");
    setError("");
    try {
      setResult(await askQuestion(question.trim()));
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : "The request failed.");
    } finally {
      setBusy(null);
    }
  }

  return (
    <main>
      <nav>
        <a className="brand" href="#">CBA<span>/</span>AI</a>
        <div className="status">
          <span className={`status-dot ${status}`} />
          API {status}
        </div>
      </nav>

      <section className="hero">
        <p className="eyebrow">Repository intelligence · grounded by your code</p>
        <h1>Understand a codebase<br />without guessing.</h1>
        <p className="lede">
          Index React and TypeScript repositories, ask implementation questions,
          and inspect every answer through file-and-line citations.
        </p>
      </section>

      <section className="workspace">
        <aside className="index-panel">
          <div className="panel-label"><span>01</span> Index</div>
          <h2>Choose a repository</h2>
          <p>The path must be inside the server&apos;s configured CODEBASE_ROOT.</p>
          <form onSubmit={handleIndex}>
            <label htmlFor="path">Relative path</label>
            <div className="input-row">
              <input id="path" value={path} onChange={(e) => setPath(e.target.value)} />
              <button disabled={busy !== null}>{busy === "index" ? "Indexing…" : "Index"}</button>
            </div>
          </form>
          {indexSummary && <div className="success">{indexSummary}</div>}
          <div className="boundary">
            <span>Read-only</span>
            <span>Path restricted</span>
            <span>Cited output</span>
          </div>
        </aside>

        <div className="ask-panel">
          <div className="panel-label"><span>02</span> Ask</div>
          <form onSubmit={handleAsk}>
            <label htmlFor="question">Question for this codebase</label>
            <textarea
              id="question"
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              placeholder="Where is authentication state managed, and how does it reach protected routes?"
              rows={5}
            />
            <div className="ask-actions">
              <p>Answers use only retrieved repository context.</p>
              <button disabled={busy !== null || !question.trim()}>
                {busy === "ask" ? "Analyzing…" : "Analyze code"}
              </button>
            </div>
          </form>
        </div>
      </section>

      {error && <div className="error" role="alert">{error}</div>}

      <section className={`answer ${result ? "visible" : ""}`}>
        <div className="panel-label"><span>03</span> Answer</div>
        {result ? (
          <>
            <p className="answer-copy">{result.answer}</p>
            <h3>Retrieved sources</h3>
            <div className="citations">
              {result.citations.map((citation, index) => (
                <div className="citation" key={`${citation.path}-${index}`}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <code>{citation.path}</code>
                  <small>L{citation.start_line}–{citation.end_line}</small>
                </div>
              ))}
            </div>
          </>
        ) : (
          <p className="empty">Your grounded answer and source ranges will appear here.</p>
        )}
      </section>

      <footer>
        <span>AI Codebase Agent</span>
        <span>FastAPI · OpenAI · Qdrant · Next.js</span>
      </footer>
    </main>
  );
}
