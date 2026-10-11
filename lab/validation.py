"""Pydantic row boundary, JSON Schema package and Pandera analytical boundaries."""
from functools import lru_cache
from pydantic import ConfigDict,Field,create_model
from .numeric import I64_MIN,I64_MAX
@lru_cache(maxsize=512)
def row_model(table,definitions):
    fields={}
    for name,typ in definitions:
        value=int|None if typ=='Int' else bool|None if typ=='Bool' else str|None
        fields[name]=(value,Field(default=None,ge=I64_MIN,le=I64_MAX) if typ=='Int' else None)
    return create_model(table,__config__=ConfigDict(extra='forbid',strict=True),**fields)
def validate_rows(data,registry):
    for table,rows in data['tables'].items():
        definitions=tuple((n,d['type']) for n,d in registry['tables'][table].items() if n not in registry['canonical_excluded_columns'].get(table,[]))
        model=row_model(table,definitions)
        for row in rows:model.model_validate(row)
    for row in data['tables']['Design_parameters']:
        if row['value_state'] not in {'unset','provisional','locked'} or row['value_kind'] not in {'integer','fixed_point','text'}:raise ValueError('invalid_parameter_kind_or_state')
        if row['value_state']=='unset' and (any(row[k] is not None for k in ('value_q','value_int','value_text')) or not row['blocking_reason']):raise ValueError('unset_parameter_requires_null_and_reason')
        if row['value_state']!='unset' and row['value_kind'] in {'integer','fixed_point'} and row['value_int' if row['value_kind']=='integer' else 'value_q'] is None:raise ValueError('numeric_parameter_requires_value')
        if row['parameter_id'].endswith(('.base_cost','.adverse_tax_cap')) and row['value_int'] is not None and row['value_int']<0:raise ValueError('negative_action_cost')
    scale=next(r for r in data['tables']['Design_parameters'] if r['parameter_id']=='S-P01')
    if scale['value_kind']!='integer' or scale['value_state']!='locked' or scale['value_int']!=12000:raise ValueError('locked_scale_changed')
