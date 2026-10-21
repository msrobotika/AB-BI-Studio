"""Shared, bounded predicates for the semantic engine and table explorer."""
import math
import re
from datetime import date, datetime

OPS = {'eq', 'ne', 'in', 'not_in', 'contains', 'not_contains', 'starts_with',
       'ends_with', 'gt', 'gte', 'lt', 'lte', 'between', 'is_blank', 'not_blank'}
TYPES = {'text', 'number', 'date', 'boolean'}


def blank(value):
    return value is None or (isinstance(value, str) and not value.strip())


def number(value, locale='auto'):
    if isinstance(value, bool) or blank(value):
        raise ValueError('Se esperaba un número no vacío')
    if isinstance(value, (int, float)):
        n = float(value)
    else:
        text = str(value).strip().replace('\u00a0', '').replace(' ', '')
        if locale in ('es', 'en'):
            decimal, group = (',', '.') if locale == 'es' else ('.', ',')
            pattern = (r'[+-]?(?:\d{1,3}(?:' + re.escape(group) + r'\d{3})+|\d+)'
                       r'(?:' + re.escape(decimal) + r'\d+)?(?:[eE][+-]?\d+)?')
            if not re.fullmatch(pattern, text):
                raise ValueError('Formato numérico inválido para la configuración elegida')
            text = text.replace(group, '').replace(decimal, '.')
        else:
            # Filter inputs use a decimal point or comma, without thousands separators.
            if not re.fullmatch(r'[+-]?(?:\d+(?:[.,]\d+)?|[.,]\d+)(?:[eE][+-]?\d+)?', text):
                raise ValueError('Usa un número sin separador de miles')
            text = text.replace(',', '.')
        n = float(text)
    if not math.isfinite(n):
        raise ValueError('El número debe ser finito')
    return n


def typed(value, kind):
    if kind == 'number':
        return number(value)
    if kind == 'date':
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value
        return date.fromisoformat(str(value))
    if kind == 'boolean':
        if isinstance(value, bool):
            return value
        key = str(value).strip().casefold()
        if key in ('true', '1', 'sí', 'si', 'yes'):
            return True
        if key in ('false', '0', 'no'):
            return False
        raise ValueError('Se esperaba sí/no o true/false')
    return str(value).casefold()


def validate_rule(rule):
    if not isinstance(rule, dict):
        if isinstance(rule, list):
            rule = {'op': 'in', 'values': rule, 'type': 'text'}
        elif rule is None or isinstance(rule, (str, int, float, bool)):
            if isinstance(rule, float) and not math.isfinite(rule):
                raise ValueError('Filtro no finito')
            return rule
        else:
            raise ValueError('Filtro inválido')
    op, kind = rule.get('op'), rule.get('type', 'text')
    if op not in OPS or kind not in TYPES:
        raise ValueError('Operador o tipo de filtro no admitido')
    out = {'op': op, 'type': kind}
    if op in ('is_blank', 'not_blank'):
        return out
    if op in ('in', 'not_in'):
        vals = rule.get('values')
        if not isinstance(vals, list) or not 1 <= len(vals) <= 300:
            raise ValueError('Selecciona entre 1 y 300 valores')
        for val in vals:
            if isinstance(val, (dict, list)):
                raise ValueError('Valor de filtro inválido')
            if val is not None:
                typed(val, kind)
        out['values'] = vals
    else:
        if 'value' not in rule or (blank(rule['value']) and not (op in ('eq','ne') and kind=='text' and isinstance(rule['value'],str))) or isinstance(rule['value'], (dict, list)):
            raise ValueError('Indica un valor de filtro')
        typed(rule['value'], kind)
        out['value'] = rule['value']
        if op == 'between':
            if 'value2' not in rule or blank(rule['value2']):
                raise ValueError('Indica los dos extremos del intervalo')
            if typed(rule['value'], kind) > typed(rule['value2'], kind):
                raise ValueError('El inicio del intervalo debe ser menor o igual al final')
            out['value2'] = rule['value2']
    return out


def matches(value, rule):
    """Rules are validated once by the caller, never interpreted as executable code."""
    if not isinstance(rule, dict):
        # Preserve v0.3's equality rules, including its numeric string comparisons.
        if value is None or rule is None:
            return value is rule
        from .semantic import same
        return same(value, rule)
    op, kind = rule['op'], rule.get('type', 'text')
    if op == 'is_blank':
        return blank(value)
    if op == 'not_blank':
        return not blank(value)
    if op in ('in', 'not_in'):
        result = False
        for candidate in rule['values']:
            if value is None or candidate is None:
                result |= value is candidate
            else:
                try:
                    result |= typed(value, kind) == typed(candidate, kind)
                except (ValueError, TypeError, OverflowError):
                    pass
        return result if op == 'in' else not result
    if blank(value):
        if value is not None and op in ('eq','ne') and kind=='text':
            equal=typed(value,kind)==typed(rule['value'],kind)
            return equal if op=='eq' else not equal
        return op in ('ne', 'not_contains')
    try:
        a, b = typed(value, kind), typed(rule['value'], kind)
        if op == 'eq': return a == b
        if op == 'ne': return a != b
        if op == 'gt': return a > b
        if op == 'gte': return a >= b
        if op == 'lt': return a < b
        if op == 'lte': return a <= b
        if op == 'between': return b <= a <= typed(rule['value2'], kind)
        if op == 'contains': return str(b) in str(a)
        if op == 'not_contains': return str(b) not in str(a)
        if op == 'starts_with': return str(a).startswith(str(b))
        if op == 'ends_with': return str(a).endswith(str(b))
    except (ValueError, TypeError, OverflowError):
        return False
    return False
