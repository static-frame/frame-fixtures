import datetime

import numpy as np
import pytest

from frame_fixtures.core import Fixture
from frame_fixtures.core import SourceValues
from frame_fixtures.core import iter_shift
from frame_fixtures.core import COUNT_INIT
from frame_fixtures.core import Grammar
from frame_fixtures.core import GrammarDoc
# from frame_fixtures.core import parse

from frame_fixtures.core import FrameFixtureSyntaxError
from frame_fixtures.core import repeat_count
from frame_fixtures.core import StrToTypeInterface
from frame_fixtures.core import DT64_UNITS

def test_iter_shift_a() -> None:
    assert list(iter_shift(range(5), 3, wrap=True)) == [3, 4, 0, 1, 2]
    assert list(iter_shift(range(5), 1, wrap=True)) == [1, 2, 3, 4, 0]
    assert list(iter_shift(range(5), 10, wrap=True)) == list(range(5))


def test_repeat_count_a() -> None:
    post = list(repeat_count(range(4), count=3))
    assert post == [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]

def test_repeat_count_b() -> None:
    with pytest.raises(ValueError):
        post = list(repeat_count(range(4), count=-3))


#-------------------------------------------------------------------------------
def test_source_values_a() -> None:

    SourceValues.update_primitives()
    post = SourceValues._INTS
    assert len(post) == SourceValues._COUNT
    # assert post[:3].tolist() == [845545, 563150, 468891]

    size = COUNT_INIT * 2 + 1
    SourceValues.update_primitives(size)
    assert len(SourceValues._INTS) == size * 2
    assert len(SourceValues._CHARS) == size * 2

    assert SourceValues._INTS[:4].tolist() == post[:4].tolist()


def test_source_values_b() -> None:

    SourceValues.update_primitives()
    post = SourceValues._CHARS
    assert len(post) == SourceValues._COUNT
    # assert post[:3].tolist() == ['fa14b27e5f09', 'ebbc39aaf008', '04e42a6ee7a9']
    # import ipdb; ipdb.set_trace()


def test_source_values_dtype_to_element_iter_a() -> None:

    for dtype in (
            np.dtype('i'),
            np.dtype('u8'),
            np.dtype('f8'),
            np.dtype('c16'),
            np.dtype('?'),
            np.dtype('U'),
            np.dtype('datetime64[D]'),
            np.dtype(object),
            ):
        gen = SourceValues.dtype_to_element_iter(dtype)
        [next(gen) for x in range(10)]


def test_source_values_dtype_to_element_iter_b() -> None:
    a = list(x for x, _ in zip(
            SourceValues.dtype_to_element_iter(np.dtype('i')),
            range(8),
            ))
    b = list(x for x, _ in zip(
            SourceValues.dtype_to_element_iter(np.dtype('i'), shift=3),
            range(5),
            ))
    assert a[3:] == b

def test_source_values_dtype_to_element_iter_c() -> None:
    a = list(x for x, _ in zip(
            SourceValues.dtype_to_element_iter(np.dtype('i')),
            range(8),
            ))

def test_source_values_dtype_spec_to_array_c() -> None:

    a = SourceValues.dtype_spec_to_array(np.dtype('timedelta64[Y]'),
            shift=101, count=3)
    assert len(a) == 3
    assert a.tolist() == [188510, 61878, 194249]

def test_source_values_dtype_spec_to_array_d() -> None:
    with pytest.raises(NotImplementedError):
        a = SourceValues.dtype_spec_to_array(np.dtype('V'), shift=101, count=3)


def test_source_values_dtype_spec_to_array_e() -> None:
    a = SourceValues.dtype_spec_to_array((int, str), shift=101, count=3)
    assert a.tolist() == [(188510, 'zlm0'), (-61878, 'zDIP'), (194249, 'zOgj')]



#-------------------------------------------------------------------------------
def test_grammer_a() -> None:

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('i(I,str)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('f(a,b)|s(3,3)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('i(a)|s(3,3)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('i(a,b,c)|s(3,3)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('c(a)|s(3,3)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('c(a,b,c)|s(3,3)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('x(a,b,c)|s(3,3)')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('lambda x: 3')

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('s(3,3)|i(I,lambda x: 3)')

#-------------------------------------------------------------------------------



def test_fixture_to_frame_a() -> None:
    # msg1 = 'f(Fg)|i(I,str)|c(IDg,dtD)|v(float)|s(4,6)'
    msg = 'f(F)|i((I,I),(str,int))|c((Is,I),(dts,int))|v(str,bool,object)|s(4,6)'
    f1 = Fixture.parse(msg)

    assert f1.to_pairs(0) == (((datetime.datetime(1970, 1, 1, 9, 38, 35), 105269), ((('zZbu', 105269), 'zjZQ'), (('zZbu', 119909), 'zO5l'), (('ztsv', 194224), 'zEdH'), (('ztsv', 172133), 'zB7E'))), ((datetime.datetime(1970, 1, 1, 9, 38, 35), 119909), ((('zZbu', 105269), False), (('zZbu', 119909), False), (('ztsv', 194224), False), (('ztsv', 172133), False))), ((datetime.datetime(1970, 1, 1, 1, 0, 48), 194224), ((('zZbu', 105269), True), (('zZbu', 119909), False), (('ztsv', 194224), 105269), (('ztsv', 172133), 119909))), ((datetime.datetime(1970, 1, 1, 1, 0, 48), 172133), ((('zZbu', 105269), 'z2Oo'), (('zZbu', 119909), 'z5l6'), (('ztsv', 194224), 'zCE3'), (('ztsv', 172133), 'zr4u'))), ((datetime.datetime(1970, 1, 2, 1, 21, 41), 96520), ((('zZbu', 105269), True), (('zZbu', 119909), True), (('ztsv', 194224), True), (('ztsv', 172133), False))), ((datetime.datetime(1970, 1, 2, 1, 21, 41), -88017), ((('zZbu', 105269), 92867), (('zZbu', 119909), 3884.98), (('ztsv', 194224), -646.86), (('ztsv', 172133), -314.34))))


def test_fixture_to_frame_b() -> None:
    f1 = Fixture.parse('s(2,2)')
    assert f1.to_pairs(0) == ((0, ((0, 1930.4), (1, -1760.34))), (1, ((0, -610.8), (1, 3243.94))))

def test_fixture_to_frame_c() -> None:
    f1 = Fixture.parse('s(2,6)|c(IH,(str,dtD,int,int))')
    assert f1.to_pairs(0) == ((('zZbu', datetime.date(2258, 3, 21), 58768, -97851), ((0, 1930.4), (1, -1760.34))), (('zZbu', datetime.date(2258, 3, 21), 58768, 168362), ((0, -610.8), (1, 3243.94))), (('zZbu', datetime.date(2258, 3, 21), 146284, 130010), ((0, 694.3), (1, -72.96))), (('zZbu', datetime.date(2258, 3, 21), 146284, -150573), ((0, 1080.4), (1, 2580.34))), (('zZbu', datetime.date(2298, 4, 20), 170440, -157437), ((0, 3511.58), (1, 1175.36))), (('zZbu', datetime.date(2298, 4, 20), 170440, 35684), ((0, 1857.34), (1, 1699.34))))


def test_fixture_to_frame_d() -> None:
    f1 = Fixture.parse('s(2,2)|v(tdD,tds)')
    assert f1.to_pairs(0) == ((0, ((0, np.timedelta64(88017,'D')), (1, np.timedelta64(92867,'D')))), (1, ((0, np.timedelta64(162197,'s')), (1, np.timedelta64(41157,'s')))))


def test_fixture_to_frame_e() -> None:
    with pytest.raises(RuntimeError):
        f1 = Fixture.parse('s(2,2)|c(IH,tds)')

    with pytest.raises(RuntimeError):
        f1 = Fixture.parse('s(2,2)|c((I,I),(int,str,float))')


def test_large_a() -> None:
    f1 = Fixture.parse('s(200000,4)|i(I,int)|c(I,str)|v(str)')
    assert f1.shape == (200000, 4)


#-------------------------------------------------------------------------------
def test_bytes_a() -> None:
    f1 = Fixture.parse('s(4,2)|(v(bytes))')
    assert f1.dtypes.values.tolist() == [np.dtype('S4'), np.dtype('S4')]

def test_uint_a() -> None:
    f1 = Fixture.parse('s(4,2)|(v(uint8))')
    assert f1.dtypes.values.tolist() == [np.dtype(np.uint8), np.dtype(np.uint8)]


#-------------------------------------------------------------------------------
def test_str_type_interface_a() -> None:
    stti = StrToTypeInterface()
    assert stti['int'] is int

    with pytest.raises(FrameFixtureSyntaxError):
        _ = stti['foo']


#-------------------------------------------------------------------------------
def test_import() -> None:

    import frame_fixtures as ff

    f1 = ff.parse('s(2,2)|i(I,str)')

    assert f1.to_pairs(0) == ((0, (('zZbu', 1930.4), ('ztsv', -1760.34))), (1, (('zZbu', -610.8), ('ztsv', 3243.94))))


#-------------------------------------------------------------------------------
def test_grammar_definition() -> None:
    cc = GrammarDoc.container_components()
    cc = GrammarDoc.specifiers_constructor()
    cc = GrammarDoc.specifiers_dtype()


#-------------------------------------------------------------------------------
def test_index_dt64_a() -> None:

    for u in DT64_UNITS:
        f = Fixture.parse(f's(3,2)|i(I{u}, dt{u})')
        assert f.index.dtype == np.dtype(f'datetime64[{u}]') # type: ignore


#-------------------------------------------------------------------------------
def test_int8() -> None:
    dt64 = np.datetime64
    f1 = Fixture.parse('s(2,4)|v(int8,str)|i(ID,dtD)|c(ID,dtD)').rename('x', index='y', columns='z')
    assert(f1.to_pairs() ==
            ((dt64('2065-01-17'), ((dt64('2065-01-17'), np.int8(47)), (dt64('1979-12-28'), np.int8(-61)))), (dt64('1979-12-28'), ((dt64('2065-01-17'), np.str_('zaji')), (dt64('1979-12-28'), np.str_('zJnC')))), (dt64('2219-12-23'), ((dt64('2065-01-17'), np.int8(-64)), (dt64('1979-12-28'), np.int8(-91)))), (dt64('2052-09-12'), ((dt64('2065-01-17'), np.str_('z2Oo')), (dt64('1979-12-28'), np.str_('z5l6'))))))
    # <Frame: x>
    # <IndexDate: z>  2065-01-17 1979-12-28 2219-12-23 2052-09-12 <datetime64[D]>
    # <IndexDate: y>
    # 2065-01-17      47         zaji       -64        z2Oo
    # 1979-12-28      -61        zJnC       -91        z5l6
    # <datetime64[D]> <int8>     <<U4>      <int8>     <<U4>