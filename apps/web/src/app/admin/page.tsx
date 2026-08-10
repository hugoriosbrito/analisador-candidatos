"use client";

import { useState } from "react";
import { API } from "@/lib/api";

export default function Page() {
  const [key, setKey] = useState("");
  const [text, setText] = useState("");
  const [claimId, setClaimId] = useState<number | null>(null);
  const [result, setResult] = useState<unknown>(null);

  const headers = () => ({ "Content-Type": "application/json", "X-Admin-Key": key });

  async function createAndResearch() {
    const created = await fetch(`${API}/admin/claims`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ text }),
    });
    const createdBody = await created.json();
    if (!created.ok) {
      setResult(createdBody);
      return;
    }
    setClaimId(createdBody.id);
    const researched = await fetch(`${API}/admin/claims/${createdBody.id}/research`, {
      method: "POST",
      headers: headers(),
    });
    setResult(await researched.json());
  }

  async function review(approved: boolean) {
    if (!claimId) return;
    const response = await fetch(`${API}/admin/claims/${claimId}/review`, {
      method: "POST",
      headers: headers(),
      body: JSON.stringify({ approved, reviewer: "Editor via painel" }),
    });
    setResult(await response.json());
  }

  async function publish() {
    if (!claimId) return;
    const response = await fetch(`${API}/admin/claims/${claimId}/publish`, {
      method: "POST",
      headers: headers(),
    });
    setResult(await response.json());
  }

  return (
    <main>
      <div className="shell" style={{ maxWidth: 760 }}>
        <div className="eyebrow">Painel editorial MVP</div>
        <h1>Nova checagem</h1>
        <div className="panel form">
          <label>
            Admin key
            <input type="password" value={key} onChange={(event) => setKey(event.target.value)} />
          </label>
          <label>
            Afirmação
            <textarea
              rows={5}
              value={text}
              onChange={(event) => setText(event.target.value)}
              placeholder="Insira uma claim atômica e verificável."
            />
          </label>
          <button className="button" onClick={createAndResearch}>Criar e pesquisar</button>
          {claimId && (
            <div style={{ display: "flex", gap: 8, flexWrap: "wrap" }}>
              <button className="button secondary" onClick={() => review(true)}>Aprovar editorialmente</button>
              <button className="button secondary" onClick={() => review(false)}>Rejeitar</button>
              <button className="button" onClick={publish}>Publicar</button>
            </div>
          )}
          {result !== null && (
            <pre style={{ whiteSpace: "pre-wrap", overflow: "auto" }}>{JSON.stringify(result, null, 2)}</pre>
          )}
        </div>
        <p className="muted">
          A chave permanece apenas no estado desta página. A API também expõe o fluxo editorial completo em /docs.
        </p>
      </div>
    </main>
  );
}
