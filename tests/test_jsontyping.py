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

from datetime import date, datetime, timedelta
from io import BytesIO
from jsontyping import from_jsondata, read_json, read_json_gz, serialize_json, serialize_json_gz, to_jsondata, write_json, write_json_gz
from pytest import raises
from typing import Dict, List, NamedTuple, Union

if str is bytes:
    str = unicode # Compatibility with Python 2

def test_jsondata_roundtrip():
    NamedTupleEmpty = NamedTuple('NamedTupleEmpty', [
    ])
    NamedTupleA = NamedTuple('NamedTupleA', [
        ('a', str),
    ])
    NamedTupleB = NamedTuple('NamedTupleB', [
        ('a', int),
        ('b', bool),
    ])
    NamedTupleC = NamedTuple('NamedTupleC', [
        ('a', int),
        ('b', bool),
        ('c', int),
        ('d', str),
        ('e', float),
        ('f', datetime),
        ('g', datetime),
        ('h', NamedTupleA),
        ('i', Union[NamedTupleA, NamedTupleB]),
        ('j', List[Union[NamedTupleA, NamedTupleB]]),
        ('k', NamedTupleEmpty),
        ('l', Union[NamedTupleEmpty, NamedTupleA, NamedTupleB]),
        ('m', timedelta),
        ('n', date),
        ('o', Dict[str, date]),
    ])
    class NamedTupleCSubClass(NamedTupleC):
        def submethod(self):
            return True
    value = NamedTupleCSubClass(
        a=1,
        b=True,
        c=123456789012345678901234567890,
        d='test\u00a7',
        e=1.4,
        f=datetime(2016, 7, 1, 18, 0, 28, 123456),
        g=None,
        h=NamedTupleA(
            a='sub',
        ),
        i=NamedTupleA(
            a='sub in union',
        ),
        j=[
            NamedTupleA(
                a='sub in list of union',
            ),
            NamedTupleB(
                a=2,
                b=False,
            ),
        ],
        k=NamedTupleEmpty(),
        l=NamedTupleEmpty(),
        m=timedelta(minutes=10, microseconds=3),
        n=date(2017, 1, 2),
        o={
            '2': date(2016, 1, 2),
            '4': date(2016, 3, 4),
        },
    )
    jsondata = {
        'a': 1,
        'b': True,
        'c': 123456789012345678901234567890,
        'd': 'test\u00a7',
        'e': 1.4,
        'f': '2016-07-01T18:00:28.123456Z',
        'g': None,
        'h': {
            'a': 'sub',
        },
        'i': {
            'type': 'NamedTupleA',
            'a': 'sub in union',
        },
        'j': [
            {
                'type': 'NamedTupleA',
                'a': 'sub in list of union',
            },
            {
                'type': 'NamedTupleB',
                'a': 2,
                'b': False,
            },
        ],
        'k': {
        },
        'l': {
            'type': 'NamedTupleEmpty',
        },
        'm': 600.000003,
        'n': '2017-01-02',
        'o': {
            '2': '2016-01-02',
            '4': '2016-03-04',
        },
    }
    assert to_jsondata(value) == jsondata
    generated_value = from_jsondata(NamedTupleCSubClass, jsondata)
    assert isinstance(generated_value, NamedTupleCSubClass)
    assert generated_value == value

def test_to_jsondata_untyped():
    value = {
        'a': 1,
        'b': True,
        'c': 2,
        'd': 'test',
        'e': 1.4,
        'f': datetime(2016, 7, 1, 18, 0, 28, 123456),
        'g': None,
        'h': {
            'x': 'sub',
            'y': {},
        },
        'm': timedelta(minutes=10, microseconds=3),
        'n': date(2017, 1, 2),
    }
    jsondata = {
        'a': 1,
        'b': True,
        'c': 2,
        'd': 'test',
        'e': 1.4,
        'f': '2016-07-01T18:00:28.123456Z',
        'g': None,
        'h': {
            'x': 'sub',
            'y': {},
        },
        'm': 600.000003,
        'n': '2017-01-02',
    }
    assert to_jsondata(value) == jsondata

def test_jsondata_empty():
    NamedTupleEmpty = NamedTuple('NamedTupleEmpty', [
    ])
    class NamedTupleEmptySubClass(NamedTupleEmpty):
        def submethod(self):
            return True
    value = NamedTupleEmptySubClass()
    jsondata = {}
    assert to_jsondata(value) == jsondata
    generated_value = from_jsondata(NamedTupleEmptySubClass, jsondata)
    assert isinstance(generated_value, NamedTupleEmptySubClass)
    assert generated_value == value

def test_from_jsondata_unsupported_type_object():
    with raises(ValueError) as excinfo:
        from_jsondata(object, {})
    assert str(excinfo.value).startswith('Unable to generate instance of ')

def test_from_jsondata_unsupported_type_dict():
    with raises(ValueError) as excinfo:
        from_jsondata(dict, {})
    assert str(excinfo.value).startswith('Unable to generate instance of ')

def test_from_jsondata_unsupported_type_list():
    with raises(ValueError) as excinfo:
        from_jsondata(list, {})
    assert str(excinfo.value).startswith('Unable to generate instance of ')

def test_from_jsondata_unsupported_class():
    class UnsupportedClass(object):
        pass
    with raises(ValueError) as excinfo:
        from_jsondata(UnsupportedClass, {'some': 'test'})
    assert str(excinfo.value).startswith('Unable to generate instance of ')

def test_from_jsondata_unsupported_nontype():
    UnsupportedNonType = 42
    with raises(ValueError) as excinfo:
        from_jsondata(UnsupportedNonType, {'some': 'test'})
    assert str(excinfo.value).startswith('Unable to generate instance of ')

def test_from_jsondata_unsupported_dict_key_type():
    with raises(ValueError) as excinfo:
        from_jsondata(Dict[int, str], {'some': 'test'})
    assert str(excinfo.value) == 'Invalid key type for JSON object: int'

def test_from_jsondata_missing_union_type():
    NamedTupleA = NamedTuple('NamedTupleA', [
        ('a', int),
    ])
    NamedTupleB = NamedTuple('NamedTupleB', [
        ('b', int),
    ])
    NamedTupleC = NamedTuple('NamedTupleC', [
        ('c', Union[NamedTupleA, NamedTupleB]),
    ])
    with raises(ValueError) as excinfo:
        from_jsondata(NamedTupleC, {'c': {'type': 'NonExistingType'}})
    assert str(excinfo.value).startswith('Unable to find type ')

def test_from_jsondata_ambiguous_union_type():
    NamedTupleA = NamedTuple('NamedTupleA', [
        ('a', int),
    ])
    OtherNamedTupleA = NamedTuple('NamedTupleA', [
        ('b', int),
    ])
    NamedTupleC = NamedTuple('NamedTupleC', [
        ('c', Union[NamedTupleA, OtherNamedTupleA]),
    ])
    with raises(ValueError) as excinfo:
        from_jsondata(NamedTupleC, {'c': {'type': 'NamedTupleA'}})
    assert str(excinfo.value).startswith('Multiple matching types for ')

def test_from_jsondata_additional_fields():
    NamedTupleA = NamedTuple('NamedTupleA', [
        ('a', str),
        ('b', datetime),
    ])
    with raises(ValueError) as excinfo:
        from_jsondata(NamedTupleA, {'a': 'test', 'b': None, 'c': None})
    assert str(excinfo.value).startswith('Unable to generate instance of ')

def test_to_jsondata_unsupported_type():
    with raises(ValueError) as excinfo:
        to_jsondata(object())
    assert str(excinfo.value).startswith('Unable to convert value to JSON data structure: ')

def test_to_jsondata_unsupported_class():
    class UnsupportedClass(object):
        pass
    with raises(ValueError) as excinfo:
        to_jsondata(UnsupportedClass())
    assert str(excinfo.value).startswith('Unable to convert value to JSON data structure: ')

def test_to_jsondata_invalid_key():
    with raises(ValueError) as excinfo:
        to_jsondata({1: 'test'})
    assert str(excinfo.value) == 'Invalid key for JSON object structure: 1'

def test_to_jsondata_unsupported_union():
    NamedTupleA = NamedTuple('NamedTupleA', [
        ('a', int),
    ])
    NamedTupleC = NamedTuple('NamedTupleC', [
        ('c', Union[NamedTupleA, str]),
    ])
    value = NamedTupleC(c='some string')
    with raises(ValueError) as excinfo:
        to_jsondata(value)
    assert str(excinfo.value).startswith('Unable to handle non-object within union: ')

def test_to_jsondata_type_already_present():
    NamedTupleA = NamedTuple('NamedTupleA', [
        ('a', int),
        ('type', str),
    ])
    NamedTupleB = NamedTuple('NamedTupleB', [
        ('b', int),
    ])
    NamedTupleC = NamedTuple('NamedTupleC', [
        ('c', Union[NamedTupleA, NamedTupleB]),
    ])
    value = NamedTupleC(c=NamedTupleA(1, 'somevalue'))
    with raises(ValueError) as excinfo:
        to_jsondata(value)
    assert str(excinfo.value).startswith('Unable to add "type" field, because it is already present: ')

def test_write_json_nospecialchar():
    value = {
        'a': 'x',
        'b': [
            {
                'b1a': 1,
                'b1b': 'yyy',
                'b1c': None,
            },
            {
                'b2a': True,
            },
        ],
        'd': datetime(2016, 7, 1, 18, 0, 28, 123456),
    }
    jsonbytes = (
        b'{\n'
        b'  "a": "x",\n'
        b'  "b": [\n'
        b'    {\n'
        b'      "b1a": 1,\n'
        b'      "b1b": "yyy",\n'
        b'      "b1c": null\n'
        b'    },\n'
        b'    {\n'
        b'      "b2a": true\n'
        b'    }\n'
        b'  ],\n'
        b'  "d": "2016-07-01T18:00:28.123456Z"\n'
        b'}\n'
    )
    jsonbytes_gz = (
        b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff\xab\xe6RPPJT\xb2RP\xaaP'
        b'\xd2\x01\xb1\x93\x80\xech CA\xa1\x1aL\x82\x84\x0cA\n\x0cu\x10|'
        b'\x90"\xa5\xca\xcaJ%$\xb1d\xa0X^iN\x0eX\xa4V\x07\xcd\x08#\x90\x11'
        b'%E\xa5\xa9\x10i \x19\x0b\xb6.\x05d\x92\x91\x81\xa1\x99\xae\x81'
        b'\xb9\xae\x81a\x88\xa1\x85\x95\x81\x81\x95\x91\x85\x9e\xa1\x91'
        b'\xb1\x89\xa9Y\x94\x12W-\x17\x00o\xd6\x01z\xa4\x00\x00\x00'
    )
    output_stream = BytesIO()
    write_json(output_stream, value)
    assert output_stream.getvalue() == jsonbytes
    output_stream_gz = BytesIO()
    write_json_gz(output_stream_gz, value)
    assert output_stream_gz.getvalue() == jsonbytes_gz
    generated_jsonbytes = serialize_json(value)
    assert type(generated_jsonbytes) is bytes
    assert generated_jsonbytes == jsonbytes
    generated_jsonbytes_gz = serialize_json_gz(value)
    assert type(generated_jsonbytes_gz) is bytes
    assert generated_jsonbytes_gz == jsonbytes_gz

def test_serialize_json_specialchar():
    value = {
        'a': 'x\u00a7',
        'b': datetime(2016, 7, 1, 18, 0, 28, 123456),
    }
    jsonbytes = (
        b'{\n'
        b'  "a": "x\xc2\xa7",\n'
        b'  "b": "2016-07-01T18:00:28.123456Z"\n'
        b'}\n'
    )
    jsonbytes_gz = (
        b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff\xab\xe6RPPJT\xb2RP\xaa8'
        b'\xb4\\I\x07\xc4K\x02\xf1\x8c\x0c\x0c\xcdt\r\xccu\r\x0cC\x0c-\xac'
        b'\x0c\x0c\xac\x8c,\xf4\x0c\x8d\x8cML\xcd\xa2\x94\xb8j\xb9\x00\xdb'
        b'Az\xf47\x00\x00\x00'
    )
    output_stream = BytesIO()
    write_json(output_stream, value)
    assert output_stream.getvalue() == jsonbytes
    output_stream_gz = BytesIO()
    write_json_gz(output_stream_gz, value)
    assert output_stream_gz.getvalue() == jsonbytes_gz
    generated_jsonbytes = serialize_json(value)
    assert type(generated_jsonbytes) is bytes
    assert generated_jsonbytes == jsonbytes
    generated_jsonbytes_gz = serialize_json_gz(value)
    assert type(generated_jsonbytes_gz) is bytes
    assert generated_jsonbytes_gz == jsonbytes_gz

def test_read_write_json_roundtrip():
    jsonbytes = (
        b'{\n'
        b'  "a": "x",\n'
        b'  "b": {\n'
        b'    "b1a": 1,\n'
        b'    "b1b": [\n'
        b'      "yyy"\n'
        b'    ],\n'
        b'    "b1c": null\n'
        b'  },\n'
        b'  "c": "2016-07-01T18:00:28.123456Z"\n'
        b'}\n'
    )
    jsonbytes_gz = (
        b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff\xab\xe6RPPJT\xb2RP\xaaP'
        b'\xd2\x01\xb1\x93\x80\xecj \x03\xc44\x04I\x18\xea\xc0x \xa9h0\x07'
        b'\xc8\xad\xac\xacT\x02\xb3c\xe1\xf2\xc9@\xf9\xbc\xd2\x9c\x1c \xbf'
        b'\x16l\x16H@\xc9\xc8\xc0\xd0L\xd7\xc0\\\xd7\xc00\xc4\xd0\xc2\xca'
        b'\xc0\xc0\xca\xc8B\xcf\xd0\xc8\xd8\xc4\xd4,J\x89\xab\x96\x0b\x00'
        b'\x9b\x99\x1b\xf2\x81\x00\x00\x00'
    )
    HelperClass = NamedTuple('HelperClass', [
        ('b1a', int),
        ('b1b', List[str]),
        ('b1c', int),
    ])
    ResultClass = NamedTuple('ResultClass', [
        ('a', str),
        ('b', HelperClass),
        ('c', datetime),
    ])
    value = ResultClass(
        a='x',
        b=HelperClass(
            b1a=1,
            b1b=['yyy'],
            b1c=None,
        ),
        c=datetime(2016, 7, 1, 18, 0, 28, 123456),
    )
    assert read_json(ResultClass, BytesIO(jsonbytes)) == value
    assert read_json_gz(ResultClass, BytesIO(jsonbytes_gz)) == value
    assert serialize_json(value) == jsonbytes
    assert serialize_json_gz(value) == jsonbytes_gz

def test_nonobject_from_jsondata_list():
    assert from_jsondata(List[int], [1, 2, 3]) == [1, 2, 3]

def test_nonobject_from_jsondata_int():
    assert from_jsondata(int, 2) == 2

def test_nonobject_to_jsondata_list():
    to_jsondata([1, 2, 3]) == [1, 2, 3]

def test_nonobject_to_jsondata_int():
    assert to_jsondata(2) == 2

def test_nonobject_write_json():
    with raises(ValueError) as excinfo:
        output_stream = BytesIO()
        write_json(output_stream, [1, 2, 3])
    assert str(excinfo.value) == 'For security reasons, refusing to handle JSON data whose toplevel is not a JSON object'

def test_nonobject_write_json_gz():
    with raises(ValueError) as excinfo:
        output_stream_gz = BytesIO()
        write_json_gz(output_stream_gz, [1, 2, 3])
    assert str(excinfo.value) == 'For security reasons, refusing to handle JSON data whose toplevel is not a JSON object'

def test_nonobject_serialize_json():
    with raises(ValueError) as excinfo:
        serialize_json([1, 2, 3])
    assert str(excinfo.value) == 'For security reasons, refusing to handle JSON data whose toplevel is not a JSON object'

def test_nonobject_serialize_json_gz():
    with raises(ValueError) as excinfo:
        serialize_json_gz([1, 2, 3])
    assert str(excinfo.value) == 'For security reasons, refusing to handle JSON data whose toplevel is not a JSON object'

def test_nonobject_read_json():
    with raises(ValueError) as excinfo:
        read_json(List[int], BytesIO(b'[1, 2, 3]'))
    assert str(excinfo.value) == 'For security reasons, refusing to handle JSON data whose toplevel is not a JSON object'

def test_nonobject_read_json_gz():
    with raises(ValueError) as excinfo:
        # b'[1, 2, 3]'
        read_json_gz(List[int], BytesIO(b'\x1f\x8b\x08\x00\x00\x00\x00\x00\x02\xff\x8b6\xd4Q0\xd2Q0\x8e\x05\x00\xc1;!\xb8\t\x00\x00\x00'))
    assert str(excinfo.value) == 'For security reasons, refusing to handle JSON data whose toplevel is not a JSON object'
