import io
import math
import json
from pathlib import Path
from fastapi.testclient import TestClient
from openpyxl import Workbook
import pytest
from backend.semantic import Engine, SemanticError, parse_dax
import backend.server as server

@pytest.fixture
def client(tmp_path,monkeypatch):
    monkeypatch.setattr(server,'STATE',tmp_path/'workspace.json')
    monkeypatch.setattr(server,'MODEL',server.demo())
    return TestClient(server.app)

def test_parser_and_basic_dax():
    m=server.demo();e=Engine(m)
    assert e.measure('Lotes')==504
    assert e.measure('Energía total')>0
    assert abs(e.eval('SUM(Lecturas[Produccion_kg])') - e.measure('Producción total')) < 1e-7
    assert abs(e.measure('Consumo específico')- e.measure('Energía total')/e.measure('Producción total'))<1e-8
    assert abs(e.measure('Producción ponderada') - e.measure('Producción total')*0.98)<1e-6
    assert e.eval('IF(1=1, 42, 3)')==42
    assert e.eval('DIVIDE(3, 0, 99)')==99
    assert e.eval('ROUND(10 / 3,2)')==3.33
    assert e.eval('SUMX(Lecturas, Lecturas[Produccion_kg] * RELATED(Equipos[EquipoID]))')>0
    assert e.eval('CALCULATE([Producción total], Equipos[Area] = "Mezclas")')==e.measure('Producción mezclas')
    with pytest.raises(SemanticError,match='no implementada'):
        e.eval('EVALUATE(1)')
    with pytest.raises(SemanticError):parse_dax('__import__("os").system("id")')

def test_filter_context_replacement_vs_intersection():
    e=Engine(server.demo())
    total=e.measure('Producción total')
    north=e.measure('Producción total',{'Equipos[Linea]':'Línea 01'})
    south=e.measure('Producción total',{'Equipos[Linea]':'Línea 02'})
    assert 0<north<total
    assert abs(north+south-e.measure('Producción mezclas'))<1e-6
    assert abs(e.measure('% del total por línea',{'Equipos[Linea]':'Línea 01'})-(north/total*100))<1e-8
    overridden=e.eval('CALCULATE([Producción total], Equipos[Linea] = "Línea 02")',{'Equipos[Linea]':'Línea 01'})
    assert overridden==south
    removed=e.eval('CALCULATE([Producción total], REMOVEFILTERS(Equipos[Linea]))',{'Equipos[Linea]':'Línea 01'})
    assert removed==total
    context={'Equipos[Area]':'Mezclas','Turnos[Turno]':'Noche'}
    assert e.measure('Producción total',context)<e.measure('Producción mezclas')
    assert e.eval('SELECTEDVALUE(Equipos[Area], "Varios")',{'Equipos[Area]':'Mezclas'})=='Mezclas'
    assert e.eval('SELECTEDVALUE(Equipos[Area], "Varios")')=='Varios'
    assert e.eval('HASONEVALUE(Equipos[Area])',{'Equipos[Area]':'Mezclas'}) is True
    assert e.eval('SUMX(Lecturas, Lecturas[Produccion_kg])')==total
    from backend.semantic import as_num
    assert as_num('1.234,56')==1234.56
    assert as_num('1,234.56')==1234.56

def test_invalid_relationship_and_cycle():
    m=server.demo();r={'from_table':'Turnos','from_column':'TurnoID','to_table':'Lecturas','to_column':'TurnoID'}
    with pytest.raises(SemanticError):server.validate_relation(m,r)
    m['tables']['Duplicate']=[{'ID':1},{'ID':1}]
    with pytest.raises(SemanticError,match='única'):
        server.validate_relation(m,{'from_table':'Lecturas','from_column':'TurnoID','to_table':'Duplicate','to_column':'ID'})

def test_api_spreadsheet_semantic_visual_roundtrip(client):
    initial=client.get('/api/model').json()
    assert len(initial['tables'])==4
    book=Workbook();ws=book.active;ws.title='Pedidos';ws.append(['PedidoID','Importe','ClienteID']);ws.append([1,100,10]);ws.append([2,50,20])
    clients=book.create_sheet('Clientes');clients.append(['ClienteID','Región']);clients.append([10,'Norte']);clients.append([20,'Sur'])
    buffer=io.BytesIO();book.save(buffer)
    response=client.post('/api/import',files={'file':('prueba.xlsx',buffer.getvalue(),'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')})
    assert response.status_code==200,response.text
    assert set(response.json()['added'])=={'Pedidos','Clientes'}
    relation={'from_table':'Pedidos','from_column':'ClienteID','to_table':'Clientes','to_column':'ClienteID'}
    assert client.post('/api/relationship',json=relation).status_code==200
    res=client.put('/api/measure',json={'name':'Ventas','expression':'SUM(Pedidos[Importe])'})
    assert res.status_code==200,res.text
    assert client.post('/api/evaluate',json={'expression':'[Ventas]','filters':{'Clientes[Región]':'Norte'}}).json()['result']==100
    v={'type':'bar','title':'Por región','measure':'Ventas','dimension':'Clientes[Región]','sort':'desc','limit':8}
    assert client.post('/api/visual',json=v).status_code==200
    data=client.post('/api/dashboard',json={'filters':{}}).json()['visuals']
    chart=next(v for v in data if v.get('title')=='Por región')
    assert [x['value'] for x in chart['result']['data']]==[100,50]
    export=client.get('/api/export');assert export.status_code==200
    proj=json.loads(export.content)
    assert proj['measures']['Ventas']=='SUM(Pedidos[Importe])'
    assert len(proj['relationships'])==4
    loaded=client.post('/api/project/import',files={'file':('model.abbi',export.content,'application/json')})
    assert loaded.status_code==200,loaded.text
    assert client.post('/api/evaluate',json={'expression':'[Ventas]'}).json()['result']==150
    assert client.get('/api/table/Pedidos').json()['rows'][0]['Importe']==100
    profile=client.get('/api/profile/Pedidos')
    assert profile.status_code==200
    assert any(c['name']=='Importe' and c['average']==75 for c in profile.json()['columns'])
    assert client.post('/api/evaluate',json={'expression':'SUM(Pedidos[Importe])'}).json()['result']==150

def test_sql_read_only(client):
    response=client.post('/api/sql',json={'query':'SELECT Area, COUNT(*) AS count_ FROM Equipos GROUP BY Area ORDER BY Area'})
    assert response.status_code==200,response.text
    assert response.json()['rows']==[['Extrusión',2],['Mezclas',2]]
    for sql in ['DELETE FROM Equipos','DROP TABLE Equipos','PRAGMA writable_schema=ON','SELECT 1; DELETE FROM Equipos']:
        assert client.post('/api/sql',json={'query':sql}).status_code==422
    assert client.get('/api/table/Equipos').json()['total']==4

def test_legacy_project_import(client):
    legacy={'format':'AB-BI Studio Project','version':2,'dataset':{'name':'Viejo','rows':[{'a':1},{'a':2} ]},'charts':[]}
    r=client.post('/api/project/import',files={'file':('viejo.abbi',json.dumps(legacy),'application/json')})
    assert r.status_code==200
    assert client.post('/api/evaluate',json={'expression':'[Recuento]'}).json()['result']==2
