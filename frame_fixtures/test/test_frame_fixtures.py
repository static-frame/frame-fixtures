
import numpy as np #type: ignore
# import static_frame as sf #type: ignore
from frame_fixtures.frame_fixtures import Fixture
from frame_fixtures.frame_fixtures import SourceValues
from frame_fixtures.frame_fixtures import iter_shift

def test_iter_shift_a() -> None:
    assert list(iter_shift(range(5), 3)) == [3, 4, 0, 1, 2]
    assert list(iter_shift(range(5), 1)) == [1, 2, 3, 4, 0]
    assert list(iter_shift(range(5), 10)) == list(range(5))

def test_parser_a() -> None:

    msg = 'f(Fg)|i(I,str)|c(IDg,dtD)|v(float)'
    msg = 'f(F)|i((I,I),(str,bool))|c((IN,I),(dtns,int))|v(str,bool,object)|s(10,10)'

    f1 = Fixture.to_frame(msg)


def test_source_values_a() -> None:

    SourceValues.update_primitives()
    post = SourceValues._INTS
    assert len(post) == SourceValues._COUNT
    # assert post[:3].tolist() == [845545, 563150, 468891]

    SourceValues.update_primitives(200_000)
    assert len(SourceValues._INTS) == 400_000
    assert len(SourceValues._CHARS) == 400_000

    assert SourceValues._INTS[:4].tolist() ==  post[:4].tolist()


def test_source_values_b() -> None:

    SourceValues.update_primitives()
    post = SourceValues._CHARS
    assert len(post) == SourceValues._COUNT
    # assert post[:3].tolist() == ['fa14b27e5f09', 'ebbc39aaf008', '04e42a6ee7a9']
    # import ipdb; ipdb.set_trace()


def test_source_valuies_dtype_to_element_iter_a() -> None:

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
        print(dtype)
        for i in range(10):
            print(next(gen))

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

if __name__ == '__main__':
    test_parser_a()







