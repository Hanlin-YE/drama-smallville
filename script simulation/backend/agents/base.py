from __future__ import annotations

from pathlib import Path

from llm.gateway import LLMGateway


class MarkdownAgent:
    def __init__(self, agent_id: str, prompt_file: str, llm: LLMGateway) -> None:
        self.agent_id = agent_id
        self.prompt_file = Path(prompt_file)
        self.llm = llm

    def load_prompt(self) -> str:
        if self.prompt_file.exists():
            return self.prompt_file.read_text(encoding="utf-8")
        return f"# {self.agent_id}\nNo prompt file found. Use schema strictly."

