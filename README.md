# LLM-Guard

Production-grade security patterns to mitigate prompt injection, context hijacking, and unauthorized tool execution in LLM applications.

---

### 🌐 Connect & Ecosystem

* **Company:** [DigitalBricks](http://digitalbricks.ai/)
* **Deep-Dive Engineering Articles:** [Medium Profile](https://medium.com/@stefanmiladinovic)
* **Professional Network:** [LinkedIn](https://www.linkedin.com/in/stmiladinovicc/)

---

### 🧠 The Core Problem

Traditional application security relies on a fundamental rule: **Never trust user input, and never mix data with executable code.** LLMs completely break this rule. They process data and system instructions within the exact same context window. 

When you connect an LLM to external APIs, live databases, or RAG systems, a hijacked prompt can turn the model into a rogue proxy client executing actions with valid structural tokens. 

This is Prompt Injection—the SQL Injection of the AI era.

```text
[ Untrusted User Input ] 
           ↓
    [ AI Model (LLM) ]  ← Hijacked Context
           ↓
[ Tools / API / RAG System ] 
           ↓
[ Unauthorized Action Execution ] 

```

This repository provides minimal, production-ready Python implementations demonstrating how to build tactical defensive layers around your LLM context boundaries.

---

### 🧑‍💻 Maintainer

Developed by **Stefan Miladinović**, AI Engineer specializing in LLMOps and AI Application Security.

License: MIT
