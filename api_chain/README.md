# API chain

## Description

The API chain allows users to interact with APIs using natural language. It can be used to provision resources on public clouds or virtualization platforms.

This module provides the PowerfulAPIChain class which subclasses Langchain's APIChain to provide support for more HTTP methods.

## Getting started

Steps to get started with the project assuming you have Python 3 installed:

```bash
git clone https://gitlab.coralio.fr/infrastructure-management-x/generative-ai/agent-scripts.git
cd agent-scripts/api_chain
python -m venv env
env\Scripts\Activate
pip install -r requirements.txt
```

## Roadmap

* [X] Test HTTP GET request
* [X] Test HTTP POST request
* [ ] Test HTTP PUT request
* [ ] Test HTTP DELETE request
* [ ] Test HTTP PATCH request
* [X] Implement async support
* [ ] Optimize API docs formatting
* [ ] Optimize default prompt templates
* [ ] Document recommended prompting strategies
* [ ] Construct a graph of agents that can provision resources on multiple cloud providers and virtualization platforms
* [ ] Implement Langfuse for tracing
* [ ] Implement Langcheck or Guardrails for LLM validation

---
