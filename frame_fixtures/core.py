import typing as tp
from types import ModuleType
import ast
from itertools import chain
from functools import lru_cache
import string
from itertools import permutations

import numpy as np #type: ignore

if tp.TYPE_CHECKING:
    from static_frame import Frame #type: ignore #pylint: disable=W0611 #pragma: no cover
    from static_frame.core.util import DtypeSpecifier #type: ignore #pylint: disable=W0611 #pragma: no cover
    from static_frame.core.container import ContainerOperand #type: ignore #pylint: disable=W0611 #pragma: no cover
    from static_frame import Index #pylint: disable=W0611 #pragma: no cover
    from static_frame import IndexHierarchy #pylint: disable=W0611 #pragma: no cover
    from static_frame import TypeBlocks #pylint: disable=W0611 #pragma: no cover


StrToType = tp.Dict[str, tp.Type[tp.Any]]
StrConstructorArg = tp.Union[str, tp.Tuple[str, ...]]
StrConstructorType = tp.Tuple[StrConstructorArg, ...]
StrConstructorsType = tp.Dict[str, StrConstructorType]


ConstructorOrConstructors = tp.Union[
        tp.Type['ContainerOperand'],
        tp.Tuple[tp.Type['ContainerOperand'], ...]
        ]
DtypeSpecOrSpecs = tp.Union['DtypeSpecifier', tp.Tuple['DtypeSpecifier', ...]]

BuildElement = tp.Union[tp.Type['ContainerOperand'], 'DtypeSpecifier']
BuildArg = tp.Union[BuildElement, tp.Tuple[BuildElement]]
BuildType = tp.Tuple[BuildArg, ...]

ShapeType = tp.Tuple[int, int]
IndexTypes = tp.Union['Index', 'IndexHierarchy']


DTYPE_OBJECT = np.dtype(object)
DTYPE_INT = np.dtype(int)
DTYPE_FLOAT = np.dtype(float)
DTYPE_COMPLEX = np.dtype(complex)
DTYPE_STR = np.dtype(str)

DTYPE_KINDS_NO_FROMITER = ('O', 'U', 'S')

COUNT_INIT = 100_000 # will be doubled on first usage


#-------------------------------------------------------------------------------
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

def take_count(iter: tp.Iterator[T],
        count: int,
        ) -> tp.Iterator[T]:
    '''
    Return `count` values from the iterator.
    '''
    for _ in range(count):
        yield next(iter)

def repeat_count(iter: tp.Iterable[T],
        count: int,
        ) -> tp.Iterable[T]:
    '''
    Repeat value from `iter` `count` times.
    '''
    if count <= 0:
        raise ValueError(f'count {count} is <= 0')
    for v in iter:
        for _ in range(count):
            yield v

#-------------------------------------------------------------------------------
def get_str_to_type(
        module_sf: tp.Optional[ModuleType],
        ) -> StrToType:
    if module_sf is None:
        import static_frame as sf
        module_sf = sf

    ref = {}
    for cls in (
            module_sf.TypeBlocks, #type: ignore
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
            str,
            float,
            bool,
            complex,
            object,
            ):
        ref[cls.__name__] = cls

    return ref

EMPTY_ARRAY = np.array(())

#-------------------------------------------------------------------------------
class SourceValues:
    _SEED = 22
    _COUNT = 0
    _INTS: np.ndarray = EMPTY_ARRAY
    _CHARS: np.ndarray = EMPTY_ARRAY
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

            if not len(cls._INTS):
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
        ints = cls._INTS
        chars = cls._CHARS

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
                for i in ints:
                    for gen in gens:
                        # return at most 3 values from the gen
                        yield from take_count(gen, (i % 3) + 1)

        elif dtype.kind == 'M': # datetime64
            def gen() -> tp.Iterator[tp.Any]:
                for v in ints:
                    # NOTE: numpy ints, can use astype
                    # yield np.datetime64(int(v), np.datetime_data(dtype)[0])
                    yield v.astype(dtype)

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
    @lru_cache(maxsize=128)
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

#-------------------------------------------------------------------------------

class FrameFixtureSyntaxError(SyntaxError):
    pass

class Grammer:
    FRAME = 'f'
    INDEX = 'i'
    COLUMNS = 'c'
    VALUES = 'v'
    SHAPE = 's'

    KNOWN = {FRAME, INDEX, COLUMNS, VALUES, SHAPE}

    ARG_COUNT_RANGE = {
            FRAME: frozenset((0, 1)),
            INDEX: frozenset((0, 2)),
            COLUMNS: frozenset((0, 2)),
            # VALUES can have any number of args
            SHAPE: frozenset((2,)),
            }

    @classmethod
    def validate(cls,
            constructors: StrConstructorsType,
            ) -> None:
        if cls.SHAPE not in constructors:
            raise FrameFixtureSyntaxError(f'missing required label: {cls.SHAPE}')

        for token in constructors.keys():
            if token in cls.ARG_COUNT_RANGE:
                sizes = cls.ARG_COUNT_RANGE[token]
                if len(constructors[token]) not in sizes:
                    raise FrameFixtureSyntaxError(f'component {token} has invalid number of arguments: {len(constructors[token])} not in {sizes}')
            elif token == cls.VALUES:
                pass
            else:
                raise FrameFixtureSyntaxError(f'invalid token: {token}')


    @classmethod
    def dsl_to_str_constructors(cls,
            dsl: str,
            ) -> StrConstructorsType:

        body = ast.parse(dsl).body
        if len(body) != 1:
            raise FrameFixtureSyntaxError('no tokens found')

        root = body[0]
        assert isinstance(root, ast.Expr)

        if isinstance(root.value, ast.BinOp):
            bin_op_active: ast.BinOp = root.value

            def parts() -> tp.Iterator[ast.Call]:
                nonlocal bin_op_active
                while True:
                    yield tp.cast(ast.Call, bin_op_active.right) # this is a Call object
                    if isinstance(bin_op_active.left, ast.Call):
                        yield bin_op_active.left
                        return
                    bin_op_active = tp.cast(ast.BinOp, bin_op_active.left)

        elif isinstance(root.value, ast.Call):
            def parts() -> tp.Iterator[ast.Call]:
                yield root.value #type: ignore

        else:
            raise FrameFixtureSyntaxError(f'no support for token {root.value}')

        constructors: StrConstructorsType = {}

        for p in parts(): # each is a Call object
            key = p.func.id #type: ignore

            args: tp.List[StrConstructorArg] = []
            for arg in p.args:
                if isinstance(arg, ast.Tuple):
                    args.append(tuple(sub.id for sub in arg.elts)) #type: ignore
                elif isinstance(arg, ast.Name):
                    args.append(arg.id)
                elif isinstance(arg, ast.Constant): # python 3.8
                    args.append(arg.value)
                elif isinstance(arg, ast.Num): # pre python 3.8
                    args.append(arg.n) #type: ignore
                else:
                    raise NotImplementedError(f'no handling for {arg}')

            constructors[key] = tuple(args)

        cls.validate(constructors) # will raise

        return constructors

#-------------------------------------------------------------------------------
class Fixture:

    @staticmethod
    def _build_index(
            count: int,
            constructor: ConstructorOrConstructors,
            dtype_spec: DtypeSpecOrSpecs,
            str_to_type: StrToType,
            ) -> IndexTypes:

        constructor_is_tuple = isinstance(constructor, tuple)

        if constructor_is_tuple or issubclass(constructor, str_to_type['IH']): #type: ignore
            # dtype_spec must be a tuple

            if not isinstance(dtype_spec, tuple) or len(dtype_spec) < 2:
                raise RuntimeError(f'for building IH dtype_spec must be a tuple')

            if constructor_is_tuple:
                if len(constructor) != len(dtype_spec): #type: ignore
                    raise RuntimeError(f'length of index_constructors must be the same as dtype_spec')
                is_static = {c.STATIC for c in constructor}
                assert len(is_static) == 1
                builder = str_to_type['IH'] if is_static.pop() else str_to_type['IHg']
            else:
                builder = constructor #type: ignore

            # depth of 3 will provide repeats of 4, 2, 1
            repeats = [(x * 2 if x > 0 else 1) for x in range(len(dtype_spec)-1, -1, -1)]

            gens: tp.List[tp.Any] = []
            for i, dts in enumerate(dtype_spec):
                array = SourceValues.dtype_spec_to_array(dts, count=count, shift=10 * i)
                gens.append(repeat_count(array, repeats[i]))

            def labels() -> tp.Iterator[tp.Tuple[tp.Any, ...]]:
                for _ in range(count):
                    yield tuple(next(x) for x in gens)

            return builder.from_labels(labels())

        # if constructor is IndexHierarchy, this will work, as array will be a 1D array of tuples that, when given to from_labels, will work
        array = SourceValues.dtype_spec_to_array(dtype_spec, count=count)
        return constructor.from_labels(array) #type: ignore

    @staticmethod
    def _build_type_blocks(
            shape: ShapeType,
            dtype_specs: tp.Sequence[DtypeSpecOrSpecs],
            str_to_type: StrToType,
            ) -> 'TypeBlocks':

        count_row, count_col = shape
        count_dtype = len(dtype_specs)

        def gen() -> tp.Iterator[np.ndarray]:
            ints = SourceValues.dtype_to_array(DTYPE_INT, count=count_col)
            max_shift = 100

            for col in range(count_col):
                yield SourceValues.dtype_spec_to_array(
                        dtype_specs[col % count_dtype],
                        count=count_row,
                        shift=ints[col] % max_shift
                        )
        return str_to_type['TB'].from_blocks(gen()).consolidate()

    #---------------------------------------------------------------------------
    @staticmethod
    def _str_to_build(
            constructor: StrConstructorType, # typle of elements or tuples
            str_to_type: StrToType,
            ) -> BuildType:
        '''Convert strings to types or SF classes.
        '''
        def gen() -> tp.Iterator[BuildArg]:
            for v in constructor:
                if isinstance(v, tuple):
                    yield tuple(str_to_type[part] for part in v)
                else:
                    yield str_to_type[v]
        return tuple(gen())

    @classmethod
    def _to_containers(cls,
            constructors: StrConstructorsType,
            str_to_type: StrToType,
            ) -> tp.Tuple['TypeBlocks',
                    tp.Optional[IndexTypes],
                    tp.Optional[IndexTypes],
                    ]:

        shape: ShapeType = tp.cast(ShapeType, constructors['s'])

        if Grammer.VALUES not in constructors:
            values_constructor = ('float',)
        else:
            values_constructor = constructors['v'] #type: ignore
        tb = cls._build_type_blocks(
                shape,
                cls._str_to_build(values_constructor, str_to_type),
                str_to_type,
                )

        # must be two args
        if 'i' in constructors and constructors['i']:
            constructor, dtype_spec = cls._str_to_build(
                    constructors['i'],
                    str_to_type,
                    )
            index = cls._build_index(
                    shape[0],
                    constructor,
                    dtype_spec,
                    str_to_type,
                    )
        else:
            index = None

        if 'c' in constructors and constructors['c']:
            constructor, dtype_spec = cls._str_to_build(
                    constructors['c'],
                    str_to_type,
                    )
            columns = cls._build_index(
                    shape[1],
                    constructor,
                    dtype_spec,
                    str_to_type,
                    )
        else:
            columns = None

        return tb, index, columns

    @classmethod
    def to_frame(cls,
            dsl: str,
            module_sf: tp.Optional[ModuleType] = None,
            ) -> 'Frame':

        str_to_type = get_str_to_type(
                module_sf=module_sf,
                )
        constructors = Grammer.dsl_to_str_constructors(dsl)

        tb, index, columns = cls._to_containers(constructors, str_to_type)

        if 'f' in constructors and constructors['f']:
            builder = cls._str_to_build(constructors['f'], str_to_type)[0]
        else:
            builder = str_to_type['F']

        return builder(tb, #type: ignore
                index=index,
                columns=columns,
                own_index=index is not None,
                own_columns=columns is not None,
                own_data=True,
                )












