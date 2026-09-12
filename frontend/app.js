"use strict";
const $ = (id) => document.getElementById(id);
const api = (window.SOURCEBOOK_API || "").replace(/\/$/, "");
const guided = !api && !["localhost", "127.0.0.1"].includes(location.hostname);
const guidedNote = guided ? "Prepared sample demo: these answers were recorded from the local CPU model. Live uploads and arbitrary questions become available when the hosted backend is connected." : "";
let demo = null;
let token = sessionStorage.getItem("sourcebook-session");
let documents = [];
let busy = false;
function notice(text = guidedNote) { $("notice").textContent = text; $("notice").hidden = !text; }
function controls() {
  $("question").disabled = busy || !documents.length;
  $("ask-button").disabled = busy || !documents.length;
  $("sample-button").disabled = busy || (guided ? !demo || documents.length > 0 : !token || documents.length >= 5);
  $("file-input").disabled = guided || busy || !token || documents.length >= 5;
  $("clear-button").disabled = busy || !documents.length;
  document.querySelectorAll(".document button").forEach(b => b.disabled = busy);
}
async function request(path, options = {}) {
  const headers = new Headers(options.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${api}${path}`, {...options, headers});
  const body = await response.json().catch(() => ({}));
  if (!response.ok) {
    if (response.status === 401) { sessionStorage.removeItem("sourcebook-session"); token = null; }
    throw new Error(typeof body.detail === "string" ? body.detail : `Request failed (${response.status}).`);
  }
  return body;
}
function renderDocuments() {
  $("documents").replaceChildren();
  $("document-count").textContent = `${documents.length} / 5`;
  for (const doc of documents) {
    const row = document.createElement("div"); row.className = "document";
    const title = document.createElement("div"); title.className = "doc-title"; title.textContent = doc.name;
    const detail = document.createElement("small"); detail.textContent = `${doc.chunks} passages · ${doc.pages} ${doc.pages === 1 ? "section" : "pages / sections"}`;
    title.append(detail);
    const remove = document.createElement("button"); remove.textContent = "×"; remove.setAttribute("aria-label", `Remove ${doc.name}`);
    remove.onclick = () => perform(async () => { if (guided) { documents = []; renderDocuments(); return; } await request(`/api/documents/${doc.id}`, {method:"DELETE"}); await refresh(); });
    row.append(title, remove); $("documents").append(row);
  }
  if (!documents.length) { const p = document.createElement("p"); p.className = "empty-library"; p.textContent = "Your sources will appear here."; $("documents").append(p); }
  controls();
}
async function refresh() { documents = await request("/api/documents"); renderDocuments(); }
async function perform(action) {
  if (busy) return; busy = true; notice(); controls();
  try { return await action(); } catch(e) { notice(e.message || "Something went wrong. Please try again."); }
  finally { busy = false; $("upload-progress").textContent = ""; controls(); }
}
async function upload(file) {
  if (guided) return notice();
  if (!file) return;
  if (file.size > 10 * 1024 * 1024) return notice("Please choose a file smaller than 10 MB.");
  await perform(async () => {
    $("upload-progress").textContent = "Reading and indexing your document…";
    const data = new FormData(); data.append("file", file);
    await request("/api/documents", {method:"POST", body:data}); await refresh();
  });
  $("file-input").value = "";
}
function message(role, text) {
  $("welcome")?.remove();
  const node = document.createElement("article"); node.className = `message ${role}`;
  const label = document.createElement("div"); label.className = "label"; label.textContent = role === "user" ? "YOU" : "SOURCEBOOK";
  const content = document.createElement("div"); content.className = "answer-text"; content.textContent = text;
  node.append(label, content); $("messages").append(node); node.scrollIntoView({block:"nearest"}); return node;
}
async function ask(question) {
  if (busy || !documents.length || !question.trim()) return;
  if (question.length > 1000) throw new Error("Keep questions under 1,000 characters.");
  return perform(async () => {
    message("user", question); $("question").value = "";
    const pending = message("assistant", "Finding evidence and preparing your answer…");
    try {
      const answer = guided ? (demo.answers[question] || {answer:"This prepared preview includes the two suggested questions only. Choose one of them, or run the full application locally to ask your own questions.",sources:[],mode:"preview",elapsed_ms:0}) : await request("/api/questions", {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify({question})});
      pending.querySelector(".answer-text").textContent = answer.answer;
      for (const source of answer.sources) {
        const box = document.createElement("details"); box.className = "source";
        const summary = document.createElement("summary"); summary.textContent = `[${source.label}] ${source.name} · ${source.location}`;
        const quote = document.createElement("blockquote"); quote.textContent = source.text;
        box.append(summary, quote); pending.append(box);
      }
      const meta = document.createElement("div"); meta.className = "meta";
      meta.textContent = `${answer.mode === "extractive" ? "Retrieved excerpts · generated answer unavailable" : answer.mode === "abstained" ? "Insufficient evidence" : "Generated from retrieved passages"} · ${(answer.elapsed_ms / 1000).toFixed(1)}s`;
      if (guided) meta.textContent = "Prepared example · no live model call";
      pending.append(meta); pending.scrollIntoView({block:"nearest"}); return answer;
    } catch (e) { pending.querySelector(".answer-text").textContent = "The request could not be completed."; throw e; }
  });
}
$("file-input").addEventListener("change", e => upload(e.target.files[0]));
$("sample-button").onclick = () => perform(async () => { if (guided) { documents = [{id:"sample",name:"Employee handbook.txt",chunks:7,pages:7}]; renderDocuments(); return; } $("upload-progress").textContent = "Indexing the sample handbook…"; await request("/api/sample", {method:"POST"}); await refresh(); });
$("clear-button").onclick = () => perform(async () => { if (guided) { documents = []; renderDocuments(); } else { await request("/api/documents", {method:"DELETE"}); await refresh(); } $("messages").replaceChildren(); });
$("question-form").onsubmit = e => { e.preventDefault(); ask($("question").value.trim()); };
$("question").onkeydown = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); $("question-form").requestSubmit(); } };
document.querySelectorAll("[data-question]").forEach(b => b.onclick = () => { if (!documents.length) return notice("Load the sample document first to try this question."); $("question").value = b.dataset.question; $("question").focus(); });
const drop = $("drop-zone");
for (const event of ["dragenter","dragover"]) drop.addEventListener(event, e => { e.preventDefault(); drop.classList.add("drag"); });
for (const event of ["dragleave","drop"]) drop.addEventListener(event, e => { e.preventDefault(); drop.classList.remove("drag"); });
drop.addEventListener("drop", e => { if (!busy && token) upload(e.dataTransfer.files[0]); });
async function start() {
  controls();
  try {
    if (guided) {
      const response = await fetch("./demo.json");
      if (!response.ok) throw new Error("Prepared sample could not be loaded.");
      demo = await response.json();
      $("connection").textContent = "Prepared sample demo";
      document.querySelector(".drop-zone strong").textContent = "Live uploads not connected";
      document.querySelector(".drop-zone > span:not(.upload-icon)").textContent = "Try the sample document below";
      document.querySelector(".privacy").textContent = "This static preview uses a fictional handbook and recorded answers. No documents are uploaded.";
      notice(); controls(); return;
    }
    const health = await request("/api/health");
    $("connection").textContent = health.model_ready ? "Local model connected" : "Search ready · model offline";
    if (token) { try { await refresh(); } catch { token = null; } }
    if (!token) { const session = await request("/api/sessions", {method:"POST"}); token = session.token; sessionStorage.setItem("sourcebook-session", token); await refresh(); }
    if (!health.model_ready) notice("The language model is offline. You can still upload documents and inspect matching excerpts; generated answers will be available when the model starts.");
  } catch { $("connection").textContent = "Backend unavailable"; notice("Cannot reach the document service. Start the Python backend, or configure its address for the hosted demo."); }
  controls();
}
start();
if (document.modelContext?.registerTool) {
  const lifecycle = new AbortController();
  Promise.resolve(document.modelContext.registerTool({name:"ask_document_question",description:"Ask a question against documents already loaded in this workspace and display the answer and sources.",inputSchema:{type:"object",properties:{question:{type:"string",minLength:1,maxLength:1000}},required:["question"],additionalProperties:false},annotations:{readOnlyHint:false,untrustedContentHint:true},execute: async input => { if (typeof input?.question !== "string" || !input.question.trim() || input.question.length > 1000 || busy || !documents.length) throw new Error("Load documents and supply a question of 1–1000 characters while the workspace is idle."); const result = await ask(input.question); if (!result) throw new Error("Question failed; see the workspace notice."); return result; }},{signal:lifecycle.signal})).catch(() => {});
  window.addEventListener("pagehide", () => lifecycle.abort(), {once:true});
}
