import React, { useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import { ArrowDownToLine, ArrowRight, CheckCircle2, FileText, Loader2, Send, Sparkles } from "lucide-react";
import "./styles.css";

const API_BASE = import.meta.env.VITE_API_BASE || "http://localhost:8000";

function App() {
  const [roles, setRoles] = useState([]);
  const [role, setRole] = useState("ai_ml");
  const [resume, setResume] = useState(null);
  const [session, setSession] = useState(null);
  const [answer, setAnswer] = useState("");
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    fetch(`${API_BASE}/roles`)
      .then((response) => response.json())
      .then(setRoles)
      .catch(() => setError("Backend is not reachable yet."));
  }, []);

  const currentQuestion = useMemo(() => {
    if (!session) return null;
    return session.interactions.find((item) => !item.answer) || null;
  }, [session]);

  async function seedKnowledge() {
    setLoading(true);
    setError("");
    try {
      await fetch(`${API_BASE}/ingest/seed`, { method: "POST" });
    } catch {
      setError("Could not seed the knowledge base.");
    } finally {
      setLoading(false);
    }
  }

  async function startInterview(event) {
    event.preventDefault();
    if (!resume) {
      setError("Upload a PDF or text resume first.");
      return;
    }
    setLoading(true);
    setError("");
    const form = new FormData();
    form.append("role", role);
    form.append("resume", resume);
    try {
      const response = await fetch(`${API_BASE}/sessions`, { method: "POST", body: form });
      if (!response.ok) throw new Error("Session failed");
      setSession(await response.json());
      setSummary(null);
    } catch {
      setError("Could not start the interview. Seed the knowledge base and try again.");
    } finally {
      setLoading(false);
    }
  }

  async function submitAnswer(event) {
    event.preventDefault();
    if (!answer.trim() || !session) return;
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_BASE}/sessions/${session.id}/answers`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ answer }),
      });
      if (!response.ok) throw new Error("Answer failed");
      const result = await response.json();
      setSession(result.session);
      setAnswer("");
      if (result.completed) {
        const summaryResponse = await fetch(`${API_BASE}/sessions/${session.id}/summary`);
        setSummary(await summaryResponse.json());
      }
    } catch {
      setError("Could not submit the answer.");
    } finally {
      setLoading(false);
    }
  }

  function downloadReport() {
    if (!session) return;
    window.open(`${API_BASE}/sessions/${session.id}/report.pdf`, "_blank");
  }

  return (
    <main className="app-shell">
      <section className="topbar">
        <div>
          <p className="eyebrow">AI/ML & Backend Assessment</p>
          <h1>Role Screening Interview</h1>
        </div>
        <button className="ghost-button" onClick={seedKnowledge} disabled={loading}>
          {loading ? <Loader2 className="spin" size={18} /> : <Sparkles size={18} />}
          Seed knowledge
        </button>
      </section>

      {error && <div className="alert">{error}</div>}

      {!session && (
        <section className="workspace two-column">
          <form className="panel" onSubmit={startInterview}>
            <h2>Candidate Entry</h2>
            <label className="file-picker">
              <FileText size={22} />
              <span>{resume ? resume.name : "Upload resume PDF or text"}</span>
              <input
                type="file"
                accept=".pdf,.txt,text/plain,application/pdf"
                onChange={(event) => setResume(event.target.files?.[0] || null)}
              />
            </label>

            <div className="field">
              <span>Target role</span>
              <div className="role-grid">
                {roles.map((item) => (
                  <button
                    type="button"
                    key={item.id}
                    className={role === item.id ? "role-card active" : "role-card"}
                    onClick={() => setRole(item.id)}
                  >
                    <strong>{item.name}</strong>
                    <small>{item.description}</small>
                  </button>
                ))}
              </div>
            </div>

            <button className="primary-button" type="submit" disabled={loading}>
              {loading ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />}
              Start interview
            </button>
          </form>

          <aside className="panel quiet">
            <h2>Pipeline</h2>
            <ol className="steps">
              <li>Parse resume and extract candidate signals</li>
              <li>Build role-aware retrieval queries</li>
              <li>Retrieve grounded knowledge chunks</li>
              <li>Generate and store interview questions</li>
              <li>Summarize answers with source traceability</li>
            </ol>
          </aside>
        </section>
      )}

      {session && (
        <section className="workspace interview-grid">
          <aside className="panel profile-panel">
            <h2>Profile Signals</h2>
            <TagGroup title="Skills" values={session.profile.skills} />
            <TagGroup title="Technologies" values={session.profile.technologies} />
            <TagGroup title="Domains" values={session.profile.domains} />
            <div className="signal">
              <span>Seniority signal</span>
              <strong>{session.profile.seniority_signal}</strong>
            </div>
          </aside>

          <section className="panel interview-panel">
            <div className="interview-header">
              <h2>Interview</h2>
              <span>{session.status}</span>
            </div>

            <div className="timeline">
              {session.interactions.map((item, index) => (
                <article key={item.id} className="qa-item">
                  <p className="question-label">Question {index + 1}</p>
                  <h3>{item.question}</h3>
                  <div className="sources">
                    {[...new Set(item.context.map((context) => context.source))].slice(0, 6).map((source) => (
                      <span key={source}>{source}</span>
                    ))}
                  </div>
                  {item.answer && <p className="answer">{item.answer}</p>}
                  {item.feedback && (
                    <p className="feedback">
                      <CheckCircle2 size={16} /> {item.feedback.note}
                    </p>
                  )}
                </article>
              ))}
            </div>

            {currentQuestion && (
              <form className="answer-box" onSubmit={submitAnswer}>
                <textarea
                  value={answer}
                  onChange={(event) => setAnswer(event.target.value)}
                  placeholder="Write your answer with examples, tradeoffs, and evidence."
                  rows={5}
                />
                <button className="primary-button" disabled={loading || !answer.trim()}>
                  {loading ? <Loader2 className="spin" size={18} /> : <Send size={18} />}
                  Submit answer
                </button>
              </form>
            )}
          </section>

          {summary && (
            <aside className="panel summary-panel">
              <h2>Summary</h2>
              <Metric label="Questions answered" value={summary.total_questions} />
              <TagGroup title="Strengths" values={summary.strengths} />
              <TagGroup title="Gaps" values={summary.gaps} />
              <TagGroup title="Sources used" values={summary.source_coverage} />
              <button className="primary-button" type="button" onClick={downloadReport}>
                <ArrowDownToLine size={18} />
                Download PDF report
              </button>
            </aside>
          )}
        </section>
      )}
    </main>
  );
}

function TagGroup({ title, values }) {
  return (
    <div className="tag-group">
      <span>{title}</span>
      <div>
        {values?.length ? values.map((value) => <em key={value}>{value}</em>) : <small>None detected yet</small>}
      </div>
    </div>
  );
}

function Metric({ label, value }) {
  return (
    <div className="metric">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
