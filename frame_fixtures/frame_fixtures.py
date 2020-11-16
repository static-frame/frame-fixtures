import typing as tp
from types import ModuleType
import ast
from itertools import chain
from itertools import cycle
from functools import lru_cache
import string
from hashlib import blake2b
from itertools import permutations
from itertools import chain

import numpy as np #type: ignore

if tp.TYPE_CHECKING:
    from static_frame import Frame #type: ignore #pylint: disable=W0611 #pragma: no cover
    from static_frame.core.util import DtypeSpecifier #type: ignore
    from static_frame.core.container import ContainerOperand
    from static_frame import Index
    from static_frame import IndexHierarchy
    from static_frame import TypeBlocks

StrToType = tp.Dict[str, tp.Type[tp.Any]]
ConstructorArg = tp.Union[str, tp.Tuple[str, ...]]
ConstructorType = tp.Tuple[ConstructorArg, ...]

ConstructorOrConstructors = tp.Union[
        tp.Type['ContainerOperand'],
        tp.Tuple[tp.Type['ContainerOperand'], ...]
        ]
ShapeType = tp.Tuple[int, int]
IndexTypes = tp.Union['Index', 'IndexHierarchy']


DtypeSpecOrSpecs = tp.Union['DtypeSpecifier', tp.Tuple['DtypeSpecifier', ...]]
DTYPE_OBJECT = np.dtype(object)
DTYPE_INT = np.dtype(int)
DTYPE_FLOAT = np.dtype(float)
DTYPE_STR = np.dtype(str)

DTYPE_KINDS_NO_FROMITER = ('O', 'U', 'S')

COUNT_INIT = 100_000 # will be doubled on first usage

T = tp.TypeVar('T')

def iter_shift(iter: tp.Iterable[T],
        count: int,
        wrap: bool = False,
        ) -> tp.Iterable[T]:
    '''
    If an array grows, wrapping will produce an order-dependent result.
    '''
    if wrap:
        store = []
    for i, v in enumerate(iter):
        if i < count:
            if wrap:
                store.append(v)
            continue
        yield v
    if wrap:
        yield from store


class SourceValues:
    _SEED = 22
    _COUNT = 0
    _INTS: tp.Optional[np.ndarray] = None
    _CHARS: tp.Optional[np.ndarray] = None
    _SIG_DIGITS = 12

    _LABEL_ALPHABET = permutations(
            chain(reversed(string.ascii_lowercase),
            string.ascii_uppercase,
            string.digits), 4)
    # 62 options in groups of 4 gives 13,388,280 permutations

    @classmethod
    def shuffle(cls, mutable: np.ndarray) -> None:
        state = np.random.get_state()
        np.random.seed(cls._SEED)
        np.random.shuffle(mutable)
        np.random.set_state(state)

    @classmethod
    def _ints_to_chars(cls,
            array: np.ndarray,
            offset: int = 0,
            ) -> np.ndarray:
        import time
        t = time.time()
        # values_char = np.empty(len(array), dtype='<U12')
        # h = blake2b(digest_size=6) # gives 4214d8ebb6f8
        # for i, v in enumerate(array):
        #     h.update(str.encode(str(v)))
        #     values_char[i] = h.hexdigest()

        values_char = np.empty(len(array), dtype=f'<U4')
        for i, v in enumerate(array):
            values_char[v - offset] = ''.join(next(cls._LABEL_ALPHABET))

        return values_char

    @classmethod
    def update_primitives(cls, count: int = COUNT_INIT) -> None:
        '''Update fixed sequences integers, characters.
        '''
        count = max(count, COUNT_INIT)
        if count > cls._COUNT:
            cls._COUNT = count * 2

            if cls._INTS is None:
                values_int = np.arange(cls._COUNT, dtype=np.int64)
                cls.shuffle(values_int)
                cls._INTS = values_int
                cls._CHARS = cls._ints_to_chars(cls._INTS)
            else:
                offset = len(cls._INTS)
                values_ext = np.arange(offset, cls._COUNT, dtype=np.int64)
                cls.shuffle(values_ext)
                cls._INTS = np.concatenate((cls._INTS, values_ext))
                cls._CHARS = np.concatenate((
                        cls._CHARS,
                        cls._ints_to_chars(values_ext, offset=offset),
                        ))

    @classmethod
    def dtype_to_element_iter(cls,
            dtype: np.dtype,
            count: int = COUNT_INIT,
            shift: int = 0,
            ) -> tp.Iterator[tp.Any]:

        cls.update_primitives(count)
        ints = tp.cast(np.ndarray, cls._INTS)
        chars = tp.cast(np.ndarray, cls._CHARS)

        if dtype.kind == 'i': # int
            def gen() -> tp.Iterator[tp.Any]:
                for v in ints:
                    yield v * (-1 if v % 3 == 0 else 1)

        elif dtype.kind == 'u': # int unsigned
            def gen() -> tp.Iterator[tp.Any]:
                yield from iter_shift(ints, 100)

        elif dtype.kind == 'f': # float
            def gen() -> tp.Iterator[tp.Any]:
                yield np.nan
                for v in ints:
                    # round to avoid tiny floating-point noise
                    if v % 3 == 0:
                        yield round(v * -0.02, cls._SIG_DIGITS)
                    else:
                        yield round(v * 0.02, cls._SIG_DIGITS)

        elif dtype.kind == 'c': # complex
            def gen() -> tp.Iterator[tp.Any]:
                for v, i in zip(
                        cls.dtype_to_element_iter(
                                DTYPE_FLOAT,
                                count=count,
                                ),
                        cls.dtype_to_element_iter(
                                DTYPE_FLOAT,
                                count=count,
                                shift=100),
                        ):
                    yield complex(v, i)

        elif dtype.kind == 'b': # boolean
            def gen() -> tp.Iterator[tp.Any]:
                for v in ints:
                    yield v % 2 == 0

        elif dtype.kind in ('U', 'S'): # str
            def gen() -> tp.Iterator[tp.Any]:
                yield from chars

        elif dtype.kind == 'O': # object
            def gen() -> tp.Iterator[tp.Any]:
                yield None
                yield True
                yield False

                gens = (cls.dtype_to_element_iter(
                                DTYPE_INT,
                                count=count,
                                shift=10,
                                ),
                        cls.dtype_to_element_iter(
                                DTYPE_FLOAT,
                                count=count,
                                shift=100,
                                ),
                        cls.dtype_to_element_iter(
                                DTYPE_STR,
                                count=count,
                                shift=50,
                                ),
                        )
                for i in range(cls._COUNT):
                    for gen in gens:
                        yield next(gen)

        elif dtype.kind == 'M': # datetime64
            def gen() -> tp.Iterator[tp.Any]:
                for v in ints:
                    # NOTE: numpy ints, can use astype
                    yield v.astype(dtype)
                    # yield np.datetime64(int(v), np.datetime_data(dtype)[0])

        elif dtype.kind == 'm': # timedelta64
            def gen() -> tp.Iterator[tp.Any]:
                for v in ints:
                    yield v.astype(dtype)

        else:
            raise NotImplementedError(f'no handling for {dtype}')

        if shift == 0:
            return gen()

        def shifted() -> tp.Iterator[tp.Any]:
            yield from iter_shift(gen(), shift)

        return shifted()


    @classmethod
    def dtype_to_array(cls,
            dtype: np.dtype,
            count: int = COUNT_INIT,
            shift: int = 0,
            gen: tp.Optional[tp.Iterator[tp.Any]] = None,
            ) -> np.ndarray:
        '''
        Args:
            gen: optionally supply a generator of values
        '''
        if not gen:
            gen = cls.dtype_to_element_iter(
                    dtype,
                    count=count,
                    shift=shift,
                    )

        if dtype.kind not in DTYPE_KINDS_NO_FROMITER:
            array = np.fromiter(gen, count=count, dtype=dtype)
        elif dtype.kind == 'O':
            array = np.empty(shape=count, dtype=dtype) # object
            for i, v in zip(range(len(array)), gen):
                array[i] = v
        else: # string typpes
            array = np.array([next(gen) for _ in range(count)])

        array.flags.writeable = False
        return array

    @classmethod
    @lru_cache()
    def dtype_spec_to_array(cls,
            dtype_spec: DtypeSpecOrSpecs,
            count: int = COUNT_INIT,
            shift: int = 0,
            ) -> np.ndarray:

        if isinstance(dtype_spec, tuple):
            # an object type of tuples
            gen = zip(*(cls.dtype_to_element_iter(
                    np.dtype(dts), count=count, shift=shift)
                    for dts in dtype_spec))
            return cls.dtype_to_array(DTYPE_OBJECT,
                    count=count,
                    shift=shift,
                    gen=gen)

        return cls.dtype_to_array(np.dtype(dtype_spec),
                count=count,
                shift=shift,
                )




class Builder:

    @staticmethod
    def build_index(
            count: int,
            constructor: ConstructorOrConstructors,
            dtype_spec: DtypeSpecOrSpecs,
            ) -> IndexTypes:

        if isinstance(constructor, tuple):
            # dtype_spec must be a tuple
            if not isinstance(dtype_spec, tuple) or len(dtype_spec) < 2:
                raise RuntimeError(f'for building IH dtype_spec must be a tuple')
            if len(constructor) != len(dtype_spec):
                raise RuntimeError(f'length of index_constructors must be the same as dtype_spec')

            is_static = {c.STATIC for c in constructor}
            assert len(is_static) == 1

            cls = (sf.IndexHierarchy if is_static.pop()
                    else sf.IndexHierarchyGO)

            tb = sf.TypeBlocks.from_blocks(dtype_spec_to_array(dts, count=count)
                    for dts in dtype_spec)

            return cls._from_type_blocks(tb,
                    index_constructors=constructor,
                    own_blocks=True,
                    )

        # if constructor is IndexHierarchy, this will work, as array will be a 1D array of tuples that, when given to from_labels, will work
        array = dtype_spec_to_array(dtype_spec, count=count)

        return constructor.from_labels(array)

    @staticmethod
    def build_values(
            shape: ShapeType,
            dtype_specs: tp.Sequence[DtypeSpecOrSpecs]
            ) -> 'TypeBlocks':

        count_row, count_col = shape
        count_dtype = len(dtype_specs)

        def gen() -> tp.Iterator[np.ndarray]:
            for col in range(count_col):
                yield dtype_spec_to_array(
                        dtype_specs[col % count_dtype],
                        count=count_row,
                        )
        return sf.TypeBlocks.from_blocks(gen()).consolidate()


    @staticmethod
    def build_frame(index, columns, blocks, constructor) -> 'Frame':
        return constructor(blocks,
                index=index,
                columns=columns,
                own_data=True,
                own_index=True,
                own_columns=True,
                )


#-------------------------------------------------------------------------------
class Fixture:

    TL_KEYS = {'f', 'i', 'c', 'v', 's'}

    @staticmethod
    def get_str_to_type(
            module_sf: tp.Optional[ModuleType],
            ) -> StrToType:
        if module_sf is None:
            import static_frame as sf
            module_sf = sf

        ref = {}
        for cls in (
                module_sf.Frame, #type: ignore
                module_sf.FrameGO, #type: ignore
                module_sf.Index, #type: ignore
                module_sf.IndexGO, #type: ignore
                module_sf.IndexHierarchy, #type: ignore
                module_sf.IndexHierarchyGO, #type: ignore
                module_sf.IndexYear, #type: ignore
                module_sf.IndexYearGO, #type: ignore
                module_sf.IndexYearMonth, #type: ignore
                module_sf.IndexYearMonthGO, #type: ignore
                module_sf.IndexDate, #type: ignore
                module_sf.IndexDateGO, #type: ignore
                module_sf.IndexSecond, #type: ignore
                module_sf.IndexSecondGO, #type: ignore
                module_sf.IndexNanosecond, #type: ignore
                module_sf.IndexNanosecondGO, #type: ignore
                ):
            key = ''.join(c for c in cls.__name__ if c.isupper()).replace('GO', 'g')
            ref[key] = cls

        for cls in (
                np.dtype('datetime64[Y]'),
                np.dtype('datetime64[M]'),
                np.dtype('datetime64[D]'),
                # NOTE: we not expose hour as IH is ambiguous
                np.dtype('datetime64[s]'),
                np.dtype('datetime64[ns]'),
                ):
            key = f'dt{np.datetime_data(cls)[0]}'
            ref[key] = cls

        for cls in (
                int,
                float,
                bool,
                complex,
                object,
                ):
            ref[cls.__name__] = cls

        return ref

    @classmethod
    def dsl_to_constructors(cls,
            dsl: str,
            ) -> tp.Dict[str, ConstructorType]:

        root = ast.parse(dsl).body[0]
        assert isinstance(root, ast.Expr)
        bin_op_active: ast.BinOp = tp.cast(ast.BinOp, root.value)

        def parts() -> tp.Iterator[ast.Call]:
            nonlocal bin_op_active
            while True:
                yield tp.cast(ast.Call, bin_op_active.right) # this is a Call object
                if isinstance(bin_op_active.left, ast.Call):
                    yield bin_op_active.left
                    return
                bin_op_active = tp.cast(ast.BinOp, bin_op_active.left)

        constructors: tp.Dict[str, ConstructorType] = {}

        for p in parts(): # each is a Call object
            key = p.func.id #type: ignore

            args: tp.List[ConstructorArg] = []
            for arg in p.args:
                if isinstance(arg, ast.Tuple):
                    args.append(tuple(sub.id for sub in arg.elts)) #type: ignore
                elif isinstance(arg, ast.Name):
                    args.append(arg.id)
                elif isinstance(arg, ast.Constant):
                    args.append(arg.value)
                else:
                    raise NotImplementedError(f'no handling for {arg}')

            constructors[key] = tuple(args)

        if set(constructors.keys()) != cls.TL_KEYS:
            raise SyntaxError(f'missing keys: {cls.TL_KEYS - constructors.keys()}')

        return constructors

    @classmethod
    def to_frame(cls,
            dsl: str,
            module_sf: tp.Optional[ModuleType] = None,
            ) -> 'Frame':

        str_to_type = cls.get_str_to_type(
                module_sf=module_sf,
                )
        constructors = cls.dsl_to_constructors(dsl)
        print(constructors)
        # import ipdb; ipdb.set_trace()



















