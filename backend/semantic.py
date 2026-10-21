"""AB-BI semantic model and deliberately limited, non-eval DAX subset.
The grammar is parsed into an AST; no Python code is evaluated from expressions.
"""
import math
import json
from .filtering import matches, validate_rule
import re
from dataclasses import dataclass
from typing import Any

class SemanticError(ValueError):
    pass

@dataclass(frozen=True)
class Token:
    kind: str
    val: Any
    pos: int

# Quoted table identifiers ('Ordenes de venta'), bracketed column / measure names,
# strings with doubled "" escapes, decimal numbers and standard operator tokens.
LEX = re.compile(r'''\s*(?:(?P<number>\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)|(?P<string>"(?:[^"]|"")*")|(?P<qtable>'(?:[^']|'')*')|(?P<bracket>\[(?:[^\]]|\]\])*\])|(?P<ident>[A-Za-z_ÁÉÍÓÚÜÑáéíóúüñ][\wÁÉÍÓÚÜÑáéíóúüñ]*)|(?P<op><=|>=|<>|!=|&&|\|\||[=<>+*/(),-]))''')


def tokenize(source: str):
    if len(source) > 2500:
        raise SemanticError('Expresión demasiado larga (máximo 2.500 caracteres)')
    out = []
    pos = 0
    while pos < len(source):
        if source[pos:].isspace():
            break
        match = LEX.match(source, pos)
        if not match:
            raise SemanticError(f'Símbolo DAX no reconocido en posición {pos + 1}')
        kind = match.lastgroup
        val = match.group(kind)
        if kind == 'string':
            val = val[1:-1].replace('""', '"')
        elif kind == 'qtable':
            val = val[1:-1].replace("''", "'")
        elif kind == 'bracket':
            val = val[1:-1].replace(']]', ']')
        elif kind == 'number':
            val = float(val)
        out.append(Token(kind, val, pos))
        pos = match.end()
        if len(out) > 600:
            raise SemanticError('Expresión demasiado compleja')
    out.append(Token('end', '', pos))
    return out

class Parser:
    PRIORITIES = {'||':1, '&&':2, '=':3, '<>':3, '!=':3, '>':3,'<':3, '>=':3,'<=':3, '+':4,'-':4,'*':5,'/':5}
    def __init__(self, source):
        self.toks=tokenize(source)
        self.i=0
    @property
    def t(self):
        return self.toks[self.i]
    def pop(self):
        p=self.t;self.i+=1;return p
    def eat(self, value):
        if self.t.val == value:
            self.pop();return True
        return False
    def expect(self, value):
        if not self.eat(value):
            raise SemanticError(f'Se esperaba {value!r} cerca de la posición {self.t.pos+1}')
    def parse(self):
        root=self.expr(0)
        if self.t.kind != 'end':
            raise SemanticError(f'Expresión no reconocida desde posición {self.t.pos+1}')
        return root
    def expr(self, minprec):
        tok=self.pop()
        if tok.val in ('+','-') and tok.kind=='op':
            left=('unary',tok.val,self.expr(6))
        elif tok.kind in ('number','string'):
            left=('lit',tok.val)
        elif tok.kind=='bracket':
            left=('measure',tok.val)
        elif tok.val=='(':
            left=self.expr(0);self.expect(')')
        elif tok.kind in ('ident','qtable'):
            name=tok.val
            if self.t.kind=='bracket':
                left=('col',name,self.pop().val)
            elif self.eat('('):
                args=[]
                if not self.eat(')'):
                    while True:
                        args.append(self.expr(0))
                        if self.eat(')'): break
                        self.expect(',')
                left=('call',name.upper(),args)
            elif name.upper() in ('TRUE','FALSE','BLANK'):
                left=('lit',{'TRUE':True,'FALSE':False,'BLANK':None}[name.upper()])
            else:
                left=('table',name)
        else:
            raise SemanticError(f'Expresión incompleta en posición {tok.pos+1}')
        while self.t.kind=='op' and self.PRIORITIES.get(self.t.val,0) >= minprec and self.t.val in self.PRIORITIES:
            op=self.pop().val
            prec=self.PRIORITIES[op]
            right=self.expr(prec+1)
            left=('binary',op,left,right)
        return left

def parse_dax(source):
    return Parser(source).parse()


def as_num(value):
    if value is None or value == '': return None
    if isinstance(value, bool):return float(value)
    try:
        if isinstance(value,str):
            val=value.strip().replace(' ', '').replace('\u00a0','')
            if not val:return None
            if ',' in val and '.' in val:
                # Last separator is the decimal separator, the other groups thousands.
                if val.rfind(',')>val.rfind('.'):
                    val=val.replace('.','').replace(',','.')
                else:val=val.replace(',','')
            elif ',' in val:
                if val.count(',')>1 and all(len(x)==3 for x in val.split(',')[1:]):
                    val=val.replace(',','')
                else:val=val.replace(',','.')
            v=float(val)
        else:v=float(value)
        return v if math.isfinite(v) else None
    except (ValueError,TypeError):return None


def same(a,b):
    if a is None or b is None:return a is b
    na,nb=as_num(a),as_num(b)
    return na==nb if na is not None and nb is not None else str(a).casefold()==str(b).casefold()


def model_validate(model):
    schema=model.get('column_schema',{})
    if not isinstance(schema,dict) or any(not isinstance(v,list) or len(v)>150 or
            any(not isinstance(c,str) or not c or len(c)>150 for c in v) for v in schema.values()):
        raise SemanticError('Esquema de columnas inválido')
    tables=model.get('tables',{})
    if not isinstance(tables,dict) or len(tables)>24:raise SemanticError('Modelo inválido: máximo 24 tablas')
    if sum(len(v) for v in tables.values()) > 200000:raise SemanticError('Límite total de 200.000 filas')
    for name,rows in tables.items():
        if not isinstance(name,str) or not name or len(name)>80 or not isinstance(rows,list):
            raise SemanticError('Nombre de tabla o filas no válidos')
        if len(rows)>40000: raise SemanticError('Máximo 40.000 filas por tabla')
        if any(not isinstance(row,dict) or len(row)>150 for row in rows):
            raise SemanticError('Las filas deben ser objetos con máximo 150 columnas')
        for row in rows:
            for key, value in row.items():
                if not isinstance(key,str) or not key or len(key)>150:
                    raise SemanticError('Los nombres de columna deben ser textos de hasta 150 caracteres')
                if not (value is None or isinstance(value,(str,int,float,bool))):
                    raise SemanticError('Los valores deben ser texto, número, booleano o vacío; aplana los objetos JSON antes de importar')
                if isinstance(value,float) and not math.isfinite(value):
                    raise SemanticError('No se admiten números NaN o infinitos')
        if len(columns(model,name))>150:
            raise SemanticError('Máximo 150 columnas en cada tabla')
    for r in model.get('relationships',[]):
        validate_relation(model,r)
    for name,expr in model.get('measures',{}).items():
        if not isinstance(name,str) or not name or len(name)>80:raise SemanticError('Nombre de medida inválido')
        parse_dax(expr)


def validate_relation(model,r):
    keys=['from_table','from_column','to_table','to_column']
    if not isinstance(r,dict) or any(not isinstance(r.get(k),str) for k in keys):raise SemanticError('Relación incompleta')
    a,b=r['from_table'],r['to_table']
    if a==b or a not in model['tables'] or b not in model['tables']:raise SemanticError('Tablas de relación inválidas')
    if r['from_column'] not in columns(model,a) or r['to_column'] not in columns(model,b):
        raise SemanticError('Columnas de relación inexistentes')
    vals=[row.get(r['to_column']) for row in model['tables'][b] if row.get(r['to_column']) not in ('',None)]
    if len(vals)!=len(set(str(x) for x in vals)):
        raise SemanticError(f"La clave de dimensión {b}[{r['to_column']}] debe ser única")
    # Prevent joins that might create ambiguous paths.
    edges=[(x['from_table'],x['to_table']) for x in model.get('relationships',[]) if x.get('active',True)]
    edges.append((a,b))
    graph={}
    for x,y in edges:graph.setdefault(x,[]).append(y)
    def walk(n,seen):
        if n in seen:return True
        return any(walk(k, seen|{n}) for k in graph.get(n,[]))
    if any(walk(n,set()) for n in graph):raise SemanticError('La relación produciría un ciclo')


def columns(model,table):
    names=list(dict.fromkeys(model.get('column_schema',{}).get(table,[])))
    seen=set(names)
    for row in model['tables'].get(table,[]):
        for name in row:
            if name not in seen:names.append(name);seen.add(name)
    return names

class Engine:
    """Evaluation supports one-way dimension→fact filter propagation.
    Filters: {"Table[Column]": scalar}; same-key filter replacement in CALCULATE.
    Does not claim full Microsoft DAX implementation.
    """
    def __init__(self, model):
        self.model=model
        self.tables=model['tables']
        self._columns={name:set(columns(model,name)) for name in self.tables}
        self.relationships=[r for r in model.get('relationships',[]) if r.get('active',True)]
        self.measures=model.get('measures',{})
        self.parsed={k:parse_dax(v) for k,v in self.measures.items()}
        self._cache={}
    def col_key(self,t,c):return f'{t}[{c}]'
    def parse_field(self,qualified):
        m=re.fullmatch(r"(?:'((?:[^']|'')+)'|([\wÁÉÍÓÚÜáéíóúüÑñ .-]+))\[([^\]]+)\]",str(qualified))
        if not m:raise SemanticError('Campo esperado: Tabla[Columna]')
        t=(m.group(1) or m.group(2)).replace("''", "'");c=m.group(3)
        self.check_col(t,c)
        return t,c
    def context(self,context):
        if not isinstance(context,dict) or len(context)>25:
            raise SemanticError('Máximo 25 filtros válidos')
        out={}
        for key,value in context.items():
            t,c=self.parse_field(key)
            try:out[self.col_key(t,c)]=validate_rule(value)
            except (ValueError,TypeError,OverflowError) as exc:raise SemanticError(str(exc)) from exc
        return out
    def check_col(self,t,c):
        if t not in self.tables or c not in self._columns[t]:
            raise SemanticError(f'No existe la columna {t}[{c}]')
    def filtered_rows(self,table,context=None,trace=None):
        if table not in self.tables: raise SemanticError(f'Tabla desconocida: {table}')
        context=self.context(context or {})
        trace=set(trace or ())
        if table in trace:raise SemanticError('Ciclo de relaciones detectado')
        ck=(table,json.dumps(context,sort_keys=True,ensure_ascii=False))
        if ck in self._cache:return self._cache[ck]
        direct={k[len(table)+1:-1]:v for k,v in context.items() if k.startswith(table+'[') and k.endswith(']')}
        allowed={}
        for r in self.relationships:
            if r['from_table']!=table:continue
            dim=self.filtered_rows(r['to_table'],context,trace|{table})
            allowed.setdefault(r['from_column'],[]).append({str(row.get(r['to_column'])) for row in dim if row.get(r['to_column']) is not None})
        def keep(row):
            for c,v in direct.items():
                if not matches(row.get(c),v):return False
            for c,sets in allowed.items():
                if any(str(row.get(c)) not in keys for keys in sets):return False
            return True
        rows=[r for r in self.tables[table] if keep(r)]
        self._cache[ck]=rows
        return rows
    def eval(self,expr,context=None):
        self._cache={}
        return self._eval(parse_dax(expr),self.context(context or {}),None,set(),0)
    def measure(self,name,context=None):
        self._cache={}
        return self._eval(('measure',name),self.context(context or {}),None,set(),0)
    def _eval(self,node,ctx,row,stack,depth):
        if depth>65: raise SemanticError('Se excedió el límite de profundidad DAX')
        d=depth+1
        kind=node[0]
        if kind=='lit':return node[1]
        if kind=='table':return node[1]
        if kind=='col':
            self.check_col(node[1],node[2]);key=self.col_key(node[1],node[2])
            if row and row[0]==node[1]:return row[1].get(node[2])
            raise SemanticError(f'{key} requiere una agregación o contexto de fila')
        if kind=='measure':
            key=next((k for k in self.parsed if k.casefold()==node[1].casefold()),None)
            if key is None:raise SemanticError(f'Medida inexistente: [{node[1]}]')
            if key in stack:raise SemanticError('Referencia circular entre medidas')
            return self._eval(self.parsed[key],ctx,None,stack|{key},d)
        if kind=='unary':
            a=as_num(self._eval(node[2],ctx,row,stack,d))
            return (-a if node[1]=='-' else a) if a is not None else None
        if kind=='binary':
            a=self._eval(node[2],ctx,row,stack,d);b=self._eval(node[3],ctx,row,stack,d);op=node[1]
            if op in ('=','<>','!=','>','>=','<','<='):
                if op=='=':return same(a,b)
                if op in ('<>','!='):return not same(a,b)
                aa,bb=as_num(a),as_num(b)
                if aa is None or bb is None:return False
                return {'>':lambda:aa>bb,'>=':lambda:aa>=bb,'<':lambda:aa<bb,'<=':lambda:aa<=bb}[op]()
            if op in ('&&','||'):return (bool(a) and bool(b)) if op=='&&' else (bool(a) or bool(b))
            aa,bb=as_num(a),as_num(b)
            if aa is None or bb is None:return None
            if op=='+':return aa+bb
            if op=='-':return aa-bb
            if op=='*':return aa*bb
            if op=='/':return None if bb==0 else aa/bb
        if kind!='call':raise SemanticError('Expresión no soportada')
        name,args=node[1],node[2]
        def argc(lo,hi=None):
            if not lo <= len(args) <= (lo if hi is None else hi):
                raise SemanticError(f'{name} requiere {lo}'+('' if hi is None else f' a {hi}')+' argumentos')
        def value(n):return self._eval(args[n],ctx,row,stack,d)
        def column(n):
            if args[n][0]!='col':raise SemanticError(f'{name}: se esperaba Tabla[Columna]')
            t,c=args[n][1],args[n][2];self.check_col(t,c);return t,c
        if name in ('SUM','AVERAGE','MIN','MAX','COUNT','DISTINCTCOUNT'):
            argc(1);t,c=column(0)
            vals=[r.get(c) for r in self.filtered_rows(t,ctx)]
            if name=='DISTINCTCOUNT':return len(set(str(v) for v in vals if v is not None))
            if name=='COUNT':return len([v for v in vals if v is not None and v!=''])
            nums=[v for x in vals if (v:=as_num(x)) is not None]
            if not nums:return None
            if name=='SUM':return math.fsum(nums)
            if name=='AVERAGE':return math.fsum(nums)/len(nums)
            if name=='MIN':return min(nums)
            return max(nums)
        if name=='COUNTROWS':
            argc(1)
            if args[0][0]!='table':raise SemanticError('COUNTROWS requiere un nombre de tabla')
            return len(self.filtered_rows(args[0][1],ctx))
        if name=='DIVIDE':
            argc(2,3);a,b=as_num(value(0)),as_num(value(1))
            if a is None or b is None or b==0:return value(2) if len(args)==3 else None
            return a/b
        if name=='IF':
            argc(2,3)
            return value(1) if bool(value(0)) else (value(2) if len(args)==3 else None)
        if name in ('COALESCE','AND','OR'):
            argc(2,12)
            vals=[value(i) for i in range(len(args))]
            if name=='COALESCE':return next((v for v in vals if v is not None),None)
            if name=='AND':return all(vals)
            return any(vals)
        if name=='NOT':argc(1);return not bool(value(0))
        if name=='ABS':argc(1);v=as_num(value(0));return abs(v) if v is not None else None
        if name=='ROUND':argc(2);v=as_num(value(0));return round(v,int(value(1))) if v is not None else None
        if name in ('SELECTEDVALUE','HASONEVALUE'):
            argc(1,2) if name=='SELECTEDVALUE' else argc(1)
            t,c=column(0)
            distinct={str(r.get(c)):r.get(c) for r in self.filtered_rows(t,ctx)}
            if name=='HASONEVALUE':return len(distinct)==1
            return next(iter(distinct.values())) if len(distinct)==1 else (value(1) if len(args)>1 else None)
        if name=='CALCULATE':
            argc(1,12)
            new=dict(ctx)
            for modifier in args[1:]:
                if modifier[0]=='call' and modifier[1] in ('REMOVEFILTERS','ALL'):
                    for operand in modifier[2]:
                        if operand[0]=='table':
                            tn=operand[1]
                            new={k:v for k,v in new.items() if not k.startswith(tn+'[')}
                        elif operand[0]=='col':new.pop(self.col_key(operand[1],operand[2]),None)
                        else:raise SemanticError('REMOVEFILTERS/ALL espera tabla o columna')
                elif modifier[0]=='binary' and modifier[1]=='=':
                    lhs=modifier[2]
                    if lhs[0]!='col':raise SemanticError('CALCULATE espera Tabla[Columna] = valor')
                    t,c=lhs[1],lhs[2];self.check_col(t,c)
                    new[self.col_key(t,c)]=self._eval(modifier[3],ctx,row,stack,d)
                else:raise SemanticError('Filtro CALCULATE admitido: Tabla[Columna] = valor o REMOVEFILTERS')
            return self._eval(args[0],new,row,stack,d)
        if name=='SUMX':
            argc(2)
            if args[0][0]!='table':raise SemanticError('SUMX requiere nombre de tabla')
            t=args[0][1]
            nums=[]
            for r in self.filtered_rows(t,ctx):
                n=as_num(self._eval(args[1],ctx,(t,r),stack,d))
                if n is not None:nums.append(n)
            return math.fsum(nums)
        if name=='RELATED':
            argc(1)
            if row is None:raise SemanticError('RELATED requiere contexto de fila (por ejemplo SUMX)')
            target,col=column(0)
            candidates=[r for r in self.relationships if r['from_table']==row[0] and r['to_table']==target]
            if len(candidates)!=1:raise SemanticError('RELATED requiere una relación activa de varios a uno')
            r=candidates[0]
            key=row[1].get(r['from_column'])
            match=next((x for x in self.tables[target] if same(x.get(r['to_column']),key)),None)
            return match.get(col) if match is not None else None
        raise SemanticError(f'Función DAX no implementada: {name}')

    def distinct(self,qualified,ctx=None,limit=80):
        t,c=self.parse_field(qualified)
        seen={}
        for r in self.filtered_rows(t,ctx):
            v=r.get(c)
            seen.setdefault(json.dumps(v,ensure_ascii=False),v)
        vals=list(seen.values());vals.sort(key=lambda v:(v is None,str(v).casefold()))
        return vals[:limit]
    def visualize(self,visual,ctx=None):
        ctx=self.context(ctx or {})
        typ=visual.get('type','bar')
        metric=visual.get('measure')
        if metric not in self.measures:raise SemanticError(f'Medida no existente: {metric}')
        if typ=='kpi':return {'type':typ,'value':self.measure(metric,ctx)}
        dimension=visual.get('dimension','')
        maxgroups=min(40,max(1,int(visual.get('limit',12))))
        groups=self.distinct(dimension,ctx,200)
        data=[]
        for group in groups:
            context=dict(ctx);t,c=self.parse_field(dimension);context[self.col_key(t,c)]=group
            data.append({'label':group if group is not None else '(vacío)','key':group,'value':self.measure(metric,context)})
        if visual.get('sort')=='desc':data.sort(key=lambda x:float(x['value'] or 0),reverse=True)
        elif visual.get('sort')=='asc':data.sort(key=lambda x:float(x['value'] or 0))
        data=data[:maxgroups]
        return {'type':typ,'data':data,'total':self.measure(metric,ctx),'truncated':len(groups)>maxgroups}
