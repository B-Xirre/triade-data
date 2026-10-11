from typing import Literal
from pydantic import BaseModel,ConfigDict,Field,field_validator
from .numeric import checked
class StrictModel(BaseModel):
    model_config=ConfigDict(extra='forbid',strict=True)
class Change(StrictModel):
    table:str;row_key:str;column:str;value:str|bool|None
class RevisionRequest(StrictModel):
    subject_id:str
    title:str=Field(min_length=1,max_length=160)
    parent_revision_id:str|None=None
    expected_snapshot_hash:str
    changes:list[Change]=Field(default_factory=list,max_length=200)
    input_overrides:dict[str,str]=Field(default_factory=dict)
    context:dict[str,str]=Field(default_factory=dict)
class RunRequest(StrictModel):
    revision_id:str
    suite_id:Literal['combat-contracts','property-10000','item-comparison','tarot-contracts','triade-probes','all']='combat-contracts'
    root_seed:str='0'
    workers:int=Field(default=1,ge=1,le=4)
    case_budget:int=Field(default=10000,ge=1,le=100000)
    sweep:dict[str,list[str]]=Field(default_factory=dict)
    @field_validator('root_seed')
    @classmethod
    def seed(cls,v):
        if checked(int(v))<0:raise ValueError('seed_nonnegative')
        return v
class AdoptionRequest(StrictModel):
    revision_id:str;run_id:str;reviewed:Literal[True]
class SyncRequest(StrictModel):
    expected_source_hash:str|None=None
