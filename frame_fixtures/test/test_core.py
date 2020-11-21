import datetime

import numpy as np #type: ignore
import pytest #type: ignore

from frame_fixtures.core import Fixture
from frame_fixtures.core import SourceValues
from frame_fixtures.core import iter_shift
from frame_fixtures.core import COUNT_INIT
from frame_fixtures.core import Grammar
from frame_fixtures.core import GrammarDoc

from frame_fixtures.core import FrameFixtureSyntaxError
from frame_fixtures.core import repeat_count

def test_iter_shift_a() -> None:
    assert list(iter_shift(range(5), 3, wrap=True)) == [3, 4, 0, 1, 2]
    assert list(iter_shift(range(5), 1, wrap=True)) == [1, 2, 3, 4, 0]
    assert list(iter_shift(range(5), 10, wrap=True)) == list(range(5))


def test_repeat_count_a() -> None:
    post = list(repeat_count(range(4), count=3))
    assert post == [0, 0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3]

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


def test_source_values_dtype_spec_to_array_a() -> None:

    a = SourceValues.dtype_spec_to_array(int, shift=101, count=3)
    assert len(a) == 3

    b = SourceValues.dtype_spec_to_array((bool, str), shift=101, count=3).tolist()
    assert len(b) == 3

    # SourceValues.update_primitives(10_000_000)
    # import ipdb; ipdb.set_trace()


#-------------------------------------------------------------------------------
def test_grammer_a() -> None:

    with pytest.raises(FrameFixtureSyntaxError):
        Grammar.dsl_to_str_constructors('')

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

#-------------------------------------------------------------------------------



def test_fixture_to_frame_a() -> None:
    # msg1 = 'f(Fg)|i(I,str)|c(IDg,dtD)|v(float)|s(4,6)'
    msg = 'f(F)|i((I,I),(str,int))|c((IN,I),(dts,int))|v(str,bool,object)|s(4,6)'
    f1 = Fixture.to_frame(msg)

    assert f1.to_pairs(0) == (((datetime.datetime(1970, 1, 1, 9, 38, 35), 105269), ((('zZbu', 105269), 'zjZQ'), (('zZbu', 119909), 'zO5l'), (('ztsv', 194224), 'zEdH'), (('ztsv', 172133), 'zB7E'))), ((datetime.datetime(1970, 1, 1, 9, 38, 35), 119909), ((('zZbu', 105269), False), (('zZbu', 119909), False), (('ztsv', 194224), False), (('ztsv', 172133), False))), ((datetime.datetime(1970, 1, 1, 1, 0, 48), 194224), ((('zZbu', 105269), True), (('zZbu', 119909), False), (('ztsv', 194224), 105269), (('ztsv', 172133), 119909))), ((datetime.datetime(1970, 1, 1, 1, 0, 48), 172133), ((('zZbu', 105269), 'z2Oo'), (('zZbu', 119909), 'z5l6'), (('ztsv', 194224), 'zCE3'), (('ztsv', 172133), 'zr4u'))), ((datetime.datetime(1970, 1, 2, 1, 21, 41), 96520), ((('zZbu', 105269), True), (('zZbu', 119909), True), (('ztsv', 194224), True), (('ztsv', 172133), False))), ((datetime.datetime(1970, 1, 2, 1, 21, 41), -88017), ((('zZbu', 105269), 92867), (('zZbu', 119909), 3884.98), (('ztsv', 194224), -646.86), (('ztsv', 172133), -314.34))))


def test_fixture_to_frame_b() -> None:
    f1 = Fixture.to_frame('s(2,2)')
    assert f1.to_pairs(0) == ((0, ((0, 1930.4), (1, -1760.34))), (1, ((0, -610.8), (1, 3243.94))))

def test_fixture_to_frame_c() -> None:
    f1 = Fixture.to_frame('s(2,6)|c(IH,(str,dtD,int,int))')
    assert f1.to_pairs(0) == ((('zZbu', datetime.date(2258, 3, 21), 58768, -97851), ((0, 1930.4), (1, -1760.34))), (('zZbu', datetime.date(2258, 3, 21), 58768, 168362), ((0, -610.8), (1, 3243.94))), (('zZbu', datetime.date(2258, 3, 21), 146284, 130010), ((0, 694.3), (1, -72.96))), (('zZbu', datetime.date(2258, 3, 21), 146284, -150573), ((0, 1080.4), (1, 2580.34))), (('zZbu', datetime.date(2298, 4, 20), 170440, -157437), ((0, 3511.58), (1, 1175.36))), (('zZbu', datetime.date(2298, 4, 20), 170440, 35684), ((0, 1857.34), (1, 1699.34))))


#-------------------------------------------------------------------------------
def test_import() -> None:

    import frame_fixtures as ff

    f1 = ff.Fixture.to_frame('s(2,2)|i(I,str)')

    assert f1.to_pairs(0) == ((0, (('zZbu', 1930.4), ('ztsv', -1760.34))), (1, (('zZbu', -610.8), ('ztsv', 3243.94))))




#-------------------------------------------------------------------------------
def test_grammar_definition() -> None:
    import static_frame as sf

    # container components
    cc = GrammarDoc.container_components()
    print(cc.to_rst(sf.DisplayConfig(include_index=False, type_show=False)))

    # container types