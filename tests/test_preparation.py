import copy
import json
import pytest
from fastapi.testclient import TestClient
import backend.server as server
from backend.semantic import Engine, SemanticError, columns
from backend.filtering import validate_rule, matches


@pytest.fixture
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(server, 'STATE', tmp_path/'workspace.json')
    model=server.demo()
    model['tables']['Datos sucios']=[
        {'Nombre':'  Ana  ', 'Importe':'1.234,56', 'Fecha':'21/10/2026', 'Grupo':' A ', 'Activo':'sí'},
        {'Nombre':'  Ana  ', 'Importe':'1.234,56', 'Fecha':'21/10/2026', 'Grupo':' A ', 'Activo':'sí'},
        {'Nombre':' Luis ', 'Importe':'error', 'Fecha':'31/02/2026', 'Grupo':' B ', 'Activo':'no'},
        {'Nombre':'   ', 'Importe':'N/A', 'Fecha':'', 'Grupo':None, 'Activo':''},
    ]
    monkeypatch.setattr(server, 'MODEL', model)
    return TestClient(server.app)


@pytest.mark.parametrize('rule,value,expected',[
    ({'op':'between','type':'number','value':'10,5','value2':'20'},12,True),
    ({'op':'between','type':'number','value':10,'value2':20},None,False),
    ({'op':'contains','value':'MEZ'},'Mezclas',True),
    ({'op':'not_contains','value':'MEZ'},'Extrusión',True),
    ({'op':'in','type':'number','values':[1,2]},'2',True),
    ({'op':'in','values':[None]},'',False),
    ({'op':'in','values':[None]},None,True),
    ({'op':'not_in','values':['A']},'b',True),
    ({'op':'is_blank'},'  ',True),
    ({'op':'not_blank'},0,True),
    ({'op':'gte','type':'date','value':'2026-10-01'},'2026-10-21',True),
    ({'op':'lt','type':'date','value':'2026-10-01'},'invalid date',False),
    ({'op':'eq','type':'boolean','value':True},'sí',True),
    ({'op':'starts_with','value':'AB'},'abc',True),
    ({'op':'ends_with','value':'XY'},'abXY',True),
])
def test_typed_predicates(rule,value,expected):
    assert matches(value,validate_rule(rule)) is expected


@pytest.mark.parametrize('rule',[
    {'op':'regex','value':'.*'},
    {'op':'in','values':[]},
    {'op':'between','type':'number','value':20,'value2':10},
    {'op':'gte','type':'date','value':'31/02/2026'},
    {'op':'eq','value':{'code':'not allowed'}},
    {'op':'in','values':['a']*301},
])
def test_invalid_predicates_rejected(client,rule):
    response=client.post('/api/filters',json={'Equipos[Area]':rule})
    assert response.status_code==422
    assert server.MODEL['filters']=={}


def test_filters_propagate_to_dax_and_table_query(client):
    model=server.demo();engine=Engine(model)
    context={'Equipos[Linea]':{'op':'in','values':['Línea 01','Línea 02']},
             'Lecturas[Produccion_kg]':{'op':'between','type':'number','value':700,'value2':900}}
    expected=[r for r in model['tables']['Lecturas'] if r['EquipoID'] in (1,2) and 700<=r['Produccion_kg']<=900]
    assert engine.eval('COUNTROWS(Lecturas)',context)==len(expected)>0
    assert engine.eval('SUM(Lecturas[Produccion_kg])',context)==pytest.approx(sum(r['Produccion_kg'] for r in expected))
    assert engine.eval('CALCULATE(COUNTROWS(Lecturas), REMOVEFILTERS(Lecturas[Produccion_kg]))',context)==252
    context={"'Datos sucios'[Nombre]":{'op':'contains','value':'ana'}}
    assert client.post('/api/filters',json=context).json()['filters']=={'Datos sucios[Nombre]':{'op':'contains','type':'text','value':'ana'}}
    result=client.post('/api/table-query',json={'table':'Datos sucios','filters':context}).json()
    assert result['total']==2
    assert Engine(server.MODEL).eval("CALCULATE(COUNTROWS('Datos sucios'), REMOVEFILTERS('Datos sucios'))",context)==4


def test_cleaning_preview_apply_undo_roundtrip(client):
    initial=copy.deepcopy(server.MODEL)
    steps=[{'op':'trim','columns':['Nombre','Grupo']},
           {'op':'null_markers','columns':['Importe'],'markers':['N/A']},
           {'op':'to_number','columns':['Importe'],'locale':'es','on_error':'keep'},
           {'op':'to_date','columns':['Fecha'],'format':'%d/%m/%Y','on_error':'null'},
           {'op':'to_boolean','columns':['Activo'],'on_error':'abort'},
           {'op':'deduplicate','columns':['Nombre','Importe','Fecha','Grupo','Activo']},
           {'op':'drop_empty','columns':['Nombre','Importe','Fecha','Grupo','Activo']}]
    payload={'table':'Datos sucios','steps':steps}
    response=client.post('/api/cleaning/preview',json=payload)
    assert response.status_code==200,response.text
    preview=response.json()
    assert preview['before_rows']==4 and preview['after_rows']==2
    assert preview['removed_rows']==2 and preview['invalid_values']==2
    assert preview['changed_cells']>0 and preview['sample']
    assert server.MODEL==initial  # Preview never changes the project.
    result=client.post('/api/cleaning/apply',json={**payload,'token':preview['token']})
    assert result.status_code==200,result.text
    rows=server.MODEL['tables']['Datos sucios']
    assert rows[0]=={'Nombre':'Ana','Importe':1234.56,'Fecha':'2026-10-21','Grupo':'A','Activo':True}
    assert rows[1]['Importe']=='error' and rows[1]['Fecha'] is None and rows[1]['Activo'] is False
    assert server.MODEL['measures']==initial['measures']
    assert server.MODEL['relationships']==initial['relationships']
    assert server.MODEL['cleaning_history'][0]['steps']==steps
    assert client.get('/api/cleaning/status').json()['can_undo']
    exported=client.get('/api/export').json()
    assert exported['cleaning_history'] and exported['tables']['Datos sucios']==rows
    assert client.post('/api/cleaning/undo').status_code==200
    assert server.MODEL==initial
    assert not client.get('/api/cleaning/status').json()['can_undo']
    assert len(list((server.STATE.parent/'backups').glob('*.json')))==1


def test_stale_preview_and_stale_undo_do_not_overwrite_later_work(client):
    payload={'table':'Datos sucios','steps':[{'op':'trim','columns':['Nombre']}]}
    preview=client.post('/api/cleaning/preview',json=payload).json()
    client.post('/api/filters',json={'Equipos[Area]':'Mezclas'})
    assert client.post('/api/cleaning/apply',json={**payload,'token':preview['token']}).status_code==409
    fresh=client.post('/api/cleaning/preview',json=payload).json()
    assert client.post('/api/cleaning/apply',json={**payload,'token':fresh['token']}).status_code==200
    client.put('/api/measure',json={'name':'Nueva','expression':'42'})
    assert client.post('/api/cleaning/undo').status_code==409
    assert server.MODEL['measures']['Nueva']=='42'


def test_cleaning_protects_relationships_and_aborts_invalid_conversion(client):
    initial=copy.deepcopy(server.MODEL)
    # Collapsing several dimension keys to the same value must fail validation.
    steps=[{'op':'replace','columns':['Linea'],'value':'02','replacement':'01'}]
    # Linea is not a primary key, so try altering the actual ID instead.
    steps=[{'op':'to_text','columns':['EquipoID']},
           {'op':'replace','columns':['EquipoID'],'value':'2','replacement':'1'}]
    r=client.post('/api/cleaning/preview',json={'table':'Equipos','steps':steps})
    assert r.status_code==422 and 'única' in r.json()['detail']
    r=client.post('/api/cleaning/preview',json={'table':'Equipos','steps':[{'op':'keep_rows','columns':['EquipoID'],'rule':{'op':'ne','type':'number','value':1}}]})
    assert r.status_code==422 and 'correspondencia' in r.json()['detail']
    r=client.post('/api/cleaning/preview',json={'table':'Datos sucios','steps':[{'op':'to_number','columns':['Importe'],'locale':'es','on_error':'abort'}]})
    assert r.status_code==422 and 'fila 3' in r.json()['detail']
    assert server.MODEL==initial


def test_zero_rows_preserve_schema_and_sparse_columns(client):
    server.MODEL['tables']['Sparse']=[{'a':1}]*201+[{'b':2}]
    assert columns(server.MODEL,'Sparse')==['a','b']
    payload={'table':'Datos sucios','steps':[{'op':'keep_rows','columns':['Nombre'],'rule':{'op':'eq','value':'inexistente'}}]}
    preview=client.post('/api/cleaning/preview',json=payload).json()
    assert preview['after_rows']==0
    assert client.post('/api/cleaning/apply',json={**payload,'token':preview['token']}).status_code==200
    assert columns(server.MODEL,'Datos sucios')==['Nombre','Importe','Fecha','Grupo','Activo']
    assert Engine(server.MODEL).eval("COUNTROWS('Datos sucios')")==0
    exported=client.get('/api/export').content
    assert client.post('/api/project/import',files={'file':('vacío.abbi',exported,'application/json')}).status_code==200


def test_query_sort_search_export_revision_and_distinct_search(client):
    context={'Equipos[Area]':{'op':'contains','value':'mez'}}
    p={'table':'Lecturas','filters':context,'sort_column':'Produccion_kg','sort_type':'number','sort_direction':'desc','limit':2}
    result=client.post('/api/table-query',json=p).json()
    assert result['total']==252 and len(result['rows'])==2
    assert result['rows'][0]['Produccion_kg']>=result['rows'][1]['Produccion_kg']
    server.MODEL['tables']['Valores']=[{'x':str(i)} for i in range(400)]
    values=client.get('/api/distinct',params={'field':'Valores[x]','search':'399'}).json()
    assert values['values']==['399'] and not values['truncated']
    assert client.post('/api/table-query',json={**p,'offset':2,'revision':result['revision']}).status_code==409
    assert client.post('/api/table-query',json={'table':'Datos sucios','search':'luis'}).json()['total']==1


def test_project_rejects_non_scalar_json_and_malformed_schema(client):
    model=copy.deepcopy(server.MODEL);model['tables']['Bad']=[{'x':{'nested':1}}]
    assert client.post('/api/project/import',files={'file':('bad.abbi',json.dumps(model),'application/json')}).status_code==422
    model=copy.deepcopy(server.MODEL);model['column_schema']={'Bad':[{}]}
    assert client.post('/api/project/import',files={'file':('bad.abbi',json.dumps(model),'application/json')}).status_code==422


def test_corrupted_backup_does_not_replace_model(client):
    payload={'table':'Datos sucios','steps':[{'op':'trim','columns':['Nombre']}]}
    preview=client.post('/api/cleaning/preview',json=payload).json()
    assert client.post('/api/cleaning/apply',json={**payload,'token':preview['token']}).status_code==200
    current=copy.deepcopy(server.MODEL)
    record=json.loads((server.STATE.parent/'cleaning_undo.json').read_text())
    backup=server.STATE.parent/'backups'/record['backup']
    changed=json.loads(backup.read_text(encoding='utf-8'));changed['name']='Altered backup'
    backup.write_text(json.dumps(changed),encoding='utf-8')
    assert client.post('/api/cleaning/undo').status_code==409
    assert server.MODEL==current


def test_persistence_failure_rolls_back_cleaning(client,monkeypatch):
    original=copy.deepcopy(server.MODEL)
    payload={'table':'Datos sucios','steps':[{'op':'trim','columns':['Nombre']}]}
    preview=client.post('/api/cleaning/preview',json=payload).json()
    def fail_persist():raise OSError('Simulated disk failure')
    monkeypatch.setattr(server,'persist',fail_persist)
    with pytest.raises(OSError,match='disk failure'):
        client.post('/api/cleaning/apply',json={**payload,'token':preview['token']})
    assert server.MODEL==original
    assert not (server.STATE.parent/'cleaning_undo.json').exists()
    assert len(list((server.STATE.parent/'backups').glob('*.json')))==1


def test_blank_text_is_distinct_from_null():
    assert matches('',validate_rule({'op':'eq','value':''}))
    assert not matches(None,validate_rule({'op':'eq','value':''}))
    assert matches('  ',validate_rule({'op':'eq','value':'  '}))
