from typing import Literal
import yaml
from pydantic import BaseModel, Field, model_validator

WorkflowType = Literal[
    "sequential",
    "supervisor_workers",
    "planner_executor",
    "critic_reviewer",
    "parallel_research",
    "human_approval",
]


class ModelConfig(BaseModel):
    default_provider: str = "openai_compatible"
    default_model: str = "gpt-4o-mini"
    fallback_provider: str | None = "ollama"


class AgentConfig(BaseModel):
    id: str
    name: str
    role: str
    goal: str
    system_prompt: str
    tools: list[str] = Field(default_factory=list)
    max_steps: int = 4
    output_schema: str = "text"


class WorkflowEdge(BaseModel):
    from_: str = Field(alias="from")
    to: str
    condition: str | None = None


class WorkflowConfig(BaseModel):
    type: WorkflowType
    start: str
    nodes: list[str]
    edges: list[WorkflowEdge] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_start(self):
        if self.start not in self.nodes:
            raise ValueError("workflow.start must exist in workflow.nodes")
        return self


class MemoryConfig(BaseModel):
    type: str = "project"
    sources: list[str] = Field(default_factory=list)


class PoliciesConfig(BaseModel):
    require_approval: list[str] = Field(default_factory=list)
    blocked: list[str] = Field(default_factory=list)
    rules: list[dict] = Field(default_factory=list)


class EvaluationConfig(BaseModel):
    cases_file: str = "eval_cases.json"


class AgentPack(BaseModel):
    name: str
    version: str = "1.0.0"
    description: str
    models: ModelConfig = Field(default_factory=ModelConfig)
    agents: list[AgentConfig]
    workflow: WorkflowConfig
    tools: list[str] = Field(default_factory=list)
    memory: MemoryConfig = Field(default_factory=MemoryConfig)
    policies: PoliciesConfig = Field(default_factory=PoliciesConfig)
    evaluation: EvaluationConfig | None = None

    @model_validator(mode="after")
    def validate_graph_references(self):
        agent_ids = {agent.id for agent in self.agents}
        missing_nodes = set(self.workflow.nodes) - agent_ids
        if missing_nodes:
            raise ValueError(f"workflow nodes not found in agents: {sorted(missing_nodes)}")
        for edge in self.workflow.edges:
            if edge.from_ not in agent_ids or edge.to not in agent_ids:
                raise ValueError(f"workflow edge references unknown agent: {edge}")
        return self


def validate_pack_yaml(yaml_text: str) -> AgentPack:
    data = yaml.safe_load(yaml_text)
    if not isinstance(data, dict):
        raise ValueError("Agent Pack YAML must be a mapping")
    return AgentPack.model_validate(data)
