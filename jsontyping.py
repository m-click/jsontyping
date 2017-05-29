from __future__ import absolute_import, division, print_function, unicode_literals

__copyright__ = '''\
Copyright (C) m-click.aero GmbH

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''

from collections import OrderedDict
from datetime import date, datetime, timedelta
from gzip import GzipFile
from inspect import isclass
from io import BytesIO
from typing import Dict, List, Union
from codecs import getreader, getwriter
from json import dump as json_dump, load as json_load
from numbers import Integral

if str is bytes:
    str = unicode # Compatibility with Python 2

_DATE_FORMAT = '%Y-%m-%d'
_DATETIME_UTC_FORMAT_MICROSECONDS = '%Y-%m-%dT%H:%M:%S.%fZ'
_DATETIME_UTC_FORMAT_SECONDS = '%Y-%m-%dT%H:%M:%SZ'

def _gzipfile(output_stream):
    compresslevel = 9
    return GzipFile(filename='', fileobj=output_stream, mode='wb', compresslevel=compresslevel, mtime=0)

def _check_toplevel_jsondata(jsondata):
    if not isinstance(jsondata, dict):
        raise ValueError('For security reasons, refusing to handle JSON data whose toplevel is not a JSON object')

def _check_json_key(key):
    if isinstance(key, str):
        return str(key)
    raise ValueError('Invalid key for JSON object structure: {!r}'.format(key))

def _from_jsondata_typed(result_type, jsondata):
    if jsondata is None:
        return None
    if result_type is bool and isinstance(jsondata, bool):
        return bool(jsondata)
    if result_type is int and isinstance(jsondata, Integral):
        return int(jsondata)
    if result_type is float and isinstance(jsondata, float):
        return float(jsondata)
    if result_type is str and isinstance(jsondata, str):
        return str(jsondata)
    if result_type is datetime and isinstance(jsondata, str):
        if '.' in jsondata:
            return datetime.strptime(jsondata, _DATETIME_UTC_FORMAT_MICROSECONDS)
        return datetime.strptime(jsondata, _DATETIME_UTC_FORMAT_SECONDS)
    if result_type is date and isinstance(jsondata, str):
        return datetime.strptime(jsondata, _DATE_FORMAT).date()
    if result_type is timedelta and isinstance(jsondata, float):
        return timedelta(seconds=jsondata)
    if hasattr(result_type, '__origin__') and result_type.__origin__ is Dict and isinstance(jsondata, dict):
        (key_type, value_type) = result_type.__args__
        if key_type is not str:
            raise ValueError('Invalid key type for JSON object: {key_type.__name__}'.format(**locals()))
        return {_check_json_key(key_jsondata): _from_jsondata_typed(value_type, value_jsondata) for key_jsondata, value_jsondata in jsondata.items()}
    if hasattr(result_type, '__origin__') and result_type.__origin__ is List and isinstance(jsondata, list):
        (item_type,) = result_type.__args__
        return [_from_jsondata_typed(item_type, item_jsondata) for item_jsondata in jsondata]
    if hasattr(result_type, '__origin__') and result_type.__origin__ is Union and isinstance(jsondata, dict):
        typename = jsondata['type']
        matching_types = [t for t in result_type.__args__ if t.__name__ == typename]
        if not matching_types:
            raise ValueError('Unable to find type {!r} in union {!r}'.format(typename, result_type))
        if len(matching_types) != 1:
            raise ValueError('Multiple matching types for {!r}: {!r}'.format(typename, matching_types))
        matching_type = matching_types[0]
        reduced_jsondata = {k: v for k, v in jsondata.items() if k != 'type'}
        return _from_jsondata_typed(matching_type, reduced_jsondata)
    if isclass(result_type) and issubclass(result_type, tuple) and hasattr(result_type, '_field_types') and isinstance(jsondata, dict) and len(jsondata) == len(result_type._fields): # typing.NamedTuple
        return result_type(*(_from_jsondata_typed(result_type._field_types[field], jsondata[field]) for field in result_type._fields))
    raise ValueError('Unable to generate instance of {result_type} from JSON data structure: {jsondata!r}'.format(**locals()))

def from_jsondata(result_type, jsondata):
    return _from_jsondata_typed(result_type, jsondata)

def _to_jsondata_typed(value_type, value):
    if hasattr(value_type, '__origin__') and value_type.__origin__ is List:
        (item_type,) = value_type.__args__
        return [_to_jsondata_typed(item_type, item_value) for item_value in value]
    if hasattr(value_type, '__origin__') and value_type.__origin__ is Union:
        plain_jsondata = _to_jsondata_untyped(value)
        if not isinstance(plain_jsondata, dict):
            raise ValueError('Unable to handle non-object within union: {!r}'.format(plain_jsondata))
        jsondata = plain_jsondata.copy()
        if 'type' in jsondata:
            raise ValueError('Unable to add "type" field, because it is already present: {!r}'.format(plain_jsondata))
        jsondata['type'] = str(value.__class__.__name__)
        return jsondata
    return _to_jsondata_untyped(value)

def _to_jsondata_untyped(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return bool(value)
    if isinstance(value, Integral):
        return int(value)
    if isinstance(value, float):
        return float(value)
    if isinstance(value, str):
        return str(value)
    if isinstance(value, datetime):
        if value.microsecond == 0:
            return str(value.strftime(_DATETIME_UTC_FORMAT_SECONDS))
        return str(value.strftime(_DATETIME_UTC_FORMAT_MICROSECONDS))
    if isinstance(value, date):
        return str(value.strftime(_DATE_FORMAT))
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, tuple) and hasattr(value, '_field_types'): # typing.NamedTuple
        return OrderedDict(
            (str(field), _to_jsondata_typed(value._field_types[field], getattr(value, field)))
            for field in value._fields
        )
    if isinstance(value, list):
        return [_to_jsondata_untyped(item) for item in value]
    if isinstance(value, dict):
        return OrderedDict((_check_json_key(key), _to_jsondata_untyped(item)) for key, item in value.items())
    raise ValueError('Unable to convert value to JSON data structure: {!r}'.format(value))

def to_jsondata(value):
    '''Convert value to a structure that consists exclusively of JSON types.

    These JSON types are: NoneType, bool, int/long, float, str (Python 2: unicode), list, OrderedDict
    '''
    jsondata = _to_jsondata_untyped(value)
    return jsondata

def write_json(output_stream, value):
    jsondata = to_jsondata(value)
    _check_toplevel_jsondata(jsondata)
    output_unicode_stream = getwriter('utf-8')(output_stream)
    json_dump(obj=jsondata, fp=output_unicode_stream, ensure_ascii=False, separators=(',', ': '), indent=2, sort_keys=True)
    output_unicode_stream.write('\n')

def write_json_gz(output_stream, value):
    with _gzipfile(output_stream) as uncompressed_stream:
        write_json(uncompressed_stream, value)

def serialize_json(value):
    output_stream = BytesIO()
    write_json(output_stream, value)
    return output_stream.getvalue()

def serialize_json_gz(value):
    output_stream = BytesIO()
    write_json_gz(output_stream, value)
    return output_stream.getvalue()

def read_json(result_type, input_stream):
    unicode_input_stream = getreader('utf-8')(input_stream)
    jsondata = json_load(unicode_input_stream)
    _check_toplevel_jsondata(jsondata)
    return from_jsondata(result_type, jsondata)

def read_json_gz(result_type, input_stream):
    with GzipFile(fileobj=input_stream, mode='rb') as uncompressed_stream:
        return read_json(result_type, uncompressed_stream)
