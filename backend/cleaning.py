"""Deterministic preparation pipeline. Preview and apply use the same function."""
import copy
import hashlib
import json
import re
import unicodedata
from datetime import datetime
from .filtering import blank, number, typed, matches, validate_rule
from .semantic import columns, model_validate, SemanticError

OPERATIONS = {
    'trim', 'collapse_spaces', 'upper', 'lower', 'strip_accents', 'null_markers',
    'replace', 'fill_null', 'to_number', 'to_date', 'to_boolean', 'to_text',
    'deduplicate', 'drop_empty', 'drop_missing', 'keep_rows',
}


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False, separators=(',', ':')).encode()).hexdigest()


def related_orphans(model):
    result = []
    for rel in model.get('relationships', []):
        if not rel.get('active', True):
            continue
        parent = {str(r.get(rel['to_column'])) for r in model['tables'][rel['to_table']]
                  if not blank(r.get(rel['to_column']))}
        missing = sum(not blank(r.get(rel['from_column'])) and str(r.get(rel['from_column'])) not in parent
                      for r in model['tables'][rel['from_table']])
        if missing:
            result.append({'relationship': f"{rel['from_table']}[{rel['from_column']}] → "
                           f"{rel['to_table']}[{rel['to_column']}]", 'rows': missing})
    return result


def prepare(model, table, steps):
    if table not in model['tables']:
        raise SemanticError('Selecciona una tabla existente')
    if not isinstance(steps, list) or not 1 <= len(steps) <= 20:
        raise SemanticError('Añade entre 1 y 20 pasos de limpieza')
    names = columns(model, table)
    original = model['tables'][table]
    records = [(i, dict(row)) for i, row in enumerate(original)]
    results, issues = [], []
    invalid_total = 0
    for index, step in enumerate(steps):
        if not isinstance(step, dict) or step.get('op') not in OPERATIONS:
            raise SemanticError('Operación de limpieza no admitida')
        op = step['op']
        selected = step.get('columns', [])
        if not isinstance(selected, list) or any(c not in names for c in selected):
            raise SemanticError('Columna de limpieza inexistente')
        selected = list(dict.fromkeys(selected))
        if not selected:
            raise SemanticError('Selecciona al menos una columna para cada paso')
        mode = step.get('on_error', 'keep')
        if mode not in ('keep', 'null', 'abort'):
            raise SemanticError('Tratamiento de errores inválido')
        value = step.get('value', '')
        if isinstance(value, (dict, list)) or len(str(value)) > 2000:
            raise SemanticError('Valor de limpieza inválido o demasiado largo')
        if op == 'replace' and (not isinstance(value, str) or value == ''):
            raise SemanticError('Indica el texto literal que se va a sustituir')
        if op == 'replace' and (not isinstance(step.get('replacement', ''), str)
                                or len(step.get('replacement', '')) > 2000):
            raise SemanticError('Texto de sustitución inválido')
        if op == 'to_number' and step.get('locale', 'es') not in ('es', 'en'):
            raise SemanticError('Selecciona coma decimal o punto decimal')
        if op == 'to_date' and step.get('format', '%d/%m/%Y') not in ('%d/%m/%Y', '%m/%d/%Y', '%Y-%m-%d'):
            raise SemanticError('Formato de fecha no admitido')
        if op == 'null_markers':
            markers = step.get('markers', ['null', 'none', 'n/a', 'na', '-', ''])
            if not isinstance(markers, list) or len(markers) > 50 or any(not isinstance(x, str) for x in markers):
                raise SemanticError('Lista de marcadores vacíos inválida')
            markers = {x.strip().casefold() for x in markers}
        rule = validate_rule(step.get('rule', {})) if op == 'keep_rows' else None
        if op == 'keep_rows' and len(selected) != 1:
            raise SemanticError('Conservar filas requiere una sola columna')
        before_count, changes, invalid = len(records), 0, 0
        if op in ('deduplicate', 'drop_empty', 'drop_missing', 'keep_rows'):
            kept, seen = [], set()
            for row_id, row in records:
                key = fingerprint([row.get(c) for c in selected])
                keep = True
                if op == 'deduplicate':
                    keep = key not in seen
                    seen.add(key)
                elif op == 'drop_empty': keep = not all(blank(row.get(c)) for c in selected)
                elif op == 'drop_missing': keep = not any(blank(row.get(c)) for c in selected)
                elif op == 'keep_rows': keep = matches(row.get(selected[0]), rule)
                if keep: kept.append((row_id, row))
            records = kept
        else:
            for row_id, row in records:
                for col in selected:
                    old = row.get(col)
                    new = old
                    try:
                        if op == 'fill_null':
                            if blank(old): new = value
                        elif op == 'null_markers':
                            if isinstance(old, str) and old.strip().casefold() in markers: new = None
                        elif not blank(old) or (isinstance(old,str) and op in ('trim','collapse_spaces','upper','lower','strip_accents','replace','to_text')):
                            if op == 'trim' and isinstance(old, str): new = old.strip()
                            elif op == 'collapse_spaces' and isinstance(old, str): new = re.sub(r'\s+', ' ', old).strip()
                            elif op == 'upper' and isinstance(old, str): new = old.upper()
                            elif op == 'lower' and isinstance(old, str): new = old.lower()
                            elif op == 'strip_accents' and isinstance(old, str):
                                new = ''.join(c for c in unicodedata.normalize('NFD', old) if not unicodedata.combining(c))
                            elif op == 'replace' and isinstance(old, str): new = old.replace(value, step.get('replacement', ''))
                            elif op == 'to_number': new = number(old, step.get('locale', 'es'))
                            elif op == 'to_date': new = datetime.strptime(str(old).strip(), step.get('format', '%d/%m/%Y')).date().isoformat()
                            elif op == 'to_boolean': new = typed(old, 'boolean')
                            elif op == 'to_text': new = str(old)
                        elif op in ('to_number', 'to_date', 'to_boolean'):
                            new = None
                    except (ValueError, TypeError, OverflowError):
                        invalid += 1
                        if len(issues) < 12:
                            issues.append({'step': index+1, 'row': row_id+1, 'column': col, 'value': old})
                        if mode == 'abort':
                            raise SemanticError(f'Paso {index+1}: valor no convertible en fila {row_id+1}, columna {col}')
                        new = None if mode == 'null' else old
                    if fingerprint(old) != fingerprint(new):
                        changes += 1
                        row[col] = new
        invalid_total += invalid
        results.append({'step': index+1, 'op': op, 'changed_cells': changes,
                        'removed_rows': before_count-len(records), 'invalid_values': invalid})
    updated = copy.deepcopy(model)
    updated['tables'][table] = [row for _, row in records]
    updated.setdefault('column_schema', {})[table] = names
    model_validate(updated)
    # Do not allow normalization/removal to silently break joins with other tables.
    old_orphans = {r['relationship']: r['rows'] for r in related_orphans(model)}
    orphans = related_orphans(updated)
    if any(r['rows'] > old_orphans.get(r['relationship'], 0) for r in orphans):
        raise SemanticError('La receta dejaría claves sin correspondencia en una relación. '
                            'Conserva el tipo de las claves o ajusta las relaciones antes de transformar esas columnas.')
    changed_rows, changed_cells, sample = 0, 0, []
    remaining = {row_id for row_id, _ in records}
    for row_id, row in records:
        changed = [c for c in names if fingerprint(original[row_id].get(c)) != fingerprint(row.get(c))]
        if changed:
            changed_rows += 1
            changed_cells += len(changed)
            if len(sample) < 12:
                sample.append({'row': row_id+1, 'status': 'changed', 'columns': changed,
                               'before': original[row_id], 'after': row})
    for row_id, row in enumerate(original):
        if row_id not in remaining and len(sample) < 12:
            sample.append({'row': row_id+1, 'status': 'removed', 'columns': [], 'before': row, 'after': None})
    token = fingerprint({'model': model, 'table': table, 'steps': steps})
    preview = {'table': table, 'before_rows': len(original), 'after_rows': len(records),
               'changed_rows': changed_rows, 'changed_cells': changed_cells,
               'removed_rows': len(original)-len(records), 'invalid_values': invalid_total,
               'issues': issues, 'steps': results, 'sample': sample, 'columns': names,
               'orphans': orphans, 'token': token}
    return updated, preview
