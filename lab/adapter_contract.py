"""Public extension contract. Register reviewed implementations in code, never Grist."""
from dataclasses import dataclass
from typing import Iterable,Protocol,Mapping,Any
@dataclass(frozen=True)
class AdapterContext:
    content_snapshot_hash:str
    subject_revision:str
    fixture_version:str
    root_seed:int
    named_rng_streams:Mapping[str,str]
    integer_inputs:Mapping[str,int]
    content:Mapping[str,Any]
@dataclass(frozen=True)
class AdapterDeclaration:
    adapter_id:str
    version:str
    capability:str
    required_inputs:tuple[str,...]
    requirements:tuple[str,...]
    metrics:tuple[str,...]
    trace_fields:tuple[str,...]
class TestAdapter(Protocol):
    declaration:AdapterDeclaration
    def evaluate(self,context:AdapterContext)->Iterable[dict]:...
class CapabilityGap:
    def __init__(self,declaration:AdapterDeclaration,reason:str):self.declaration=declaration;self.reason=reason
    def evaluate(self,context:AdapterContext):
        yield {'case_id':self.declaration.adapter_id+'.capability','status':'blocked','reason':self.reason,'metrics':{},'trace':[],'rule_ids':list(self.declaration.requirements),'details':{'subject_revision':context.subject_revision}}
