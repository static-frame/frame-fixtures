from __future__ import annotations

import typing as tp
from types import ModuleType
import ast
from itertools import chain
from functools import lru_cache
import string
from itertools import permutations

import numpy as np

if tp.TYPE_CHECKING:
    from static_frame import Frame #pragma: no cover
    from static_frame.core.util import TDtypeSpecifier #pragma: no cover
    from static_frame.core.container import ContainerOperand #pragma: no cover
    from static_frame import Index #pragma: no cover
    from static_frame import IndexHierarchy #pragma: no cover
    from static_frame import TypeBlocks #pragma: no cover

    TNDArrayAny = np.ndarray[tp.Any, tp.Any] #pragma: no cover
    TDtypeAny = np.dtype[tp.Any] #pragma: no cover


TStrToType = tp.Dict[str, tp.Type[tp.Any]]
TStrConstructorArg = tp.Union[str, tp.Tuple[str, ...]]
TStrConstructorType = tp.Tuple[TStrConstructorArg, ...]
TStrConstructorsType = tp.Dict[str, TStrConstructorType]

TConstructorOrConstructors = tp.Union[
        tp.Type['ContainerOperand'],
        tp.Tuple[tp.Type['ContainerOperand'], ...]
        ]
TDtypeSpecOrSpecs = tp.Union['TDtypeSpecifier', tp.Tuple['TDtypeSpecifier', ...]]

TBuildElement = tp.Union[tp.Type['ContainerOperand'], 'TDtypeSpecifier']
TBuildArg = tp.Union[TBuildElement, tp.Tuple[TBuildElement]]
TBuildType = tp.Tuple[TBuildArg, ...]

TShapeType = tp.Tuple[int, int]
TIndexTypes = tp.Union['Index', 'IndexHierarchy']


DTYPE_OBJECT = np.dtype(object)
DTYPE_INT = np.dtype(np.int64)
DTYPE_FLOAT = np.dtype(np.float64)
DTYPE_COMPLEX = np.dtype(complex)
DTYPE_STR = np.dtype('U4')
DTYPE_BYTES = np.dtype('S4')

DTYPE_KINDS_NO_FROMITER = ('O', 'U', 'S')

DT64_UNITS = ('Y', 'M', 'D', 'h', 'm', 's', 'ms', 'us', 'ns')

COUNT_INIT = 100_000 # will be doubled on first usage
EMPTY_ARRAY: TNDArrayAny = np.array(())


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
def get_str_to_constructor(
        module_sf: tp.Optional[ModuleType],
        ) -> TStrToType:
    if module_sf is None:
        import static_frame as sf
        module_sf = sf

    # NOTE: IndexHour, IndexMillisecond, IndexMicrosecond cannot be used as abreviated here because they would collide with IndexHierarchy or themselves; would need to chagne encoding
    ref = {}
    for cls in (
            module_sf.TypeBlocks,
            module_sf.Frame,
            module_sf.FrameGO,
            module_sf.Index,
            module_sf.IndexGO,
            module_sf.IndexHierarchy,
            module_sf.IndexHierarchyGO,
            module_sf.IndexAutoConstructorFactory,
            ):
        key = ''.join(c for c in cls.__name__ if c.isupper()).replace('GO', 'g')
        ref[key] = cls

    for (cls, label) in (
            (module_sf.IndexYear, 'IY'),
            (module_sf.IndexYearGO, 'IYg'),
            (module_sf.IndexYearMonth, 'IM'),
            (module_sf.IndexYearMonthGO, 'IMg'),
            (module_sf.IndexYearMonth, 'IYM'),
            (module_sf.IndexYearMonthGO, 'IYMg'),
            (module_sf.IndexDate, 'ID'),
            (module_sf.IndexDateGO, 'IDg'),
            (module_sf.IndexHour, 'Ih'),
            (module_sf.IndexHourGO, 'Ihg'),
            (module_sf.IndexMinute, 'Im'),
            (module_sf.IndexMinuteGO, 'Img'),
            (module_sf.IndexSecond, 'Is'),
            (module_sf.IndexSecondGO, 'Isg'),
            (module_sf.IndexMillisecond, 'Ims'),
            (module_sf.IndexMillisecondGO, 'Imsg'),
            (module_sf.IndexMicrosecond, 'Ius'),
            (module_sf.IndexMicrosecondGO, 'Iusg'),
            (module_sf.IndexNanosecond, 'Ins'),
            (module_sf.IndexNanosecondGO, 'Insg'),
            ):
        ref[label] = cls

    return ref


def get_str_to_dtype() -> TStrToType:
    '''Get a mapping from a string representation to a dtype specifier (not always a dtype)
    '''
    ref = {}
    cls: tp.Any
    for unit in DT64_UNITS:
        cls = np.dtype(f'datetime64[{unit}]')
        key = f'dt{np.datetime_data(cls)[0]}'
        ref[key] = cls

    for unit in DT64_UNITS:
        cls = np.dtype(f'timedelta64[{unit}]')
        key = f'td{np.datetime_data(cls)[0]}'
        ref[key] = cls

    for cls in (
            int,
            str,
            bytes,
            float,
            bool,
            complex,
            object,
            np.int8,
            np.int16,
            np.int32,
            np.int64,
            np.uint8,
            np.uint16,
            np.uint32,
            np.uint64,
            np.float16,
            np.float32,
            np.float64,
            # np.float128, # not available on win
            np.complex64,
            np.complex128,
            ):
        ref[cls.__name__] = cls
    return ref


class StrToTypeInterface:
    '''Wrapper around TStrToType mapping that provides informative key-errors.
    '''
    def __init__(self,
            module_sf: tp.Optional[ModuleType] = None,
            ):
        if module_sf is None:
            import static_frame as sf
            module_sf = sf

        self._constructor_specifiers = get_str_to_constructor(module_sf)
        self._dtype_specifiers = get_str_to_dtype()

        assert len(self._constructor_specifiers.keys()
                & self._dtype_specifiers.keys()) == 0
        self._map = dict(chain(
                self._constructor_specifiers.items(),
                self._dtype_specifiers.items()
                ))

    def __getitem__(self, key: str) -> tp.Type[tp.Any]:
        try:
            return self._map[key]
        except KeyError:
            raise FrameFixtureSyntaxError(f'{key!r} is not a valid specifier. Choose a constructor specifier ({", ".join(self._constructor_specifiers.keys())}) or a dtype specifier ({", ".join(self._dtype_specifiers.keys())})') from None

#-------------------------------------------------------------------------------
class SourceValues:
    _SEED = 22
    _COUNT = 0 # current count; this values is mutated

    _INTS = EMPTY_ARRAY # will be a numpy array of int64
    _INTS_DTYPE = np.dtype(np.int64)
    _CHARS = EMPTY_ARRAY
    _BYTES = EMPTY_ARRAY

    _SIG_DIGITS = 12

    _LABEL_ALPHABET = permutations(
            chain(reversed(string.ascii_lowercase),
            string.ascii_uppercase,
            string.digits), 4)
    # 62 options in groups of 4 gives 13,388,280 permutations

    @classmethod
    def shuffle(cls, mutable: TNDArrayAny) -> None:
        state = np.random.get_state()
        np.random.seed(cls._SEED)
        np.random.shuffle(mutable)
        np.random.set_state(state)

    @classmethod
    def _ints_to_chars(cls,
            array: TNDArrayAny,
            offset: int = 0,
            ) -> TNDArrayAny:

        values_char = np.empty(len(array), dtype=DTYPE_STR)
        for i, v in enumerate(array):
            values_char[v - offset] = ''.join(next(cls._LABEL_ALPHABET))

        return values_char

    @classmethod
    def update_primitives(cls, count: int = COUNT_INIT) -> None:
        '''Update fixed sequences integers, characters.
        '''
        count = max(count, COUNT_INIT)

        # NOTE: if count is more than 2x of cls._COUNT, grow in 2x iteations to always match growth done incrementall
        while count > cls._COUNT:
            cls._COUNT = count * 2

            if not len(cls._INTS):
                values_int = np.arange(cls._COUNT, dtype=cls._INTS_DTYPE)
                cls.shuffle(values_int)
                cls._INTS = values_int
                cls._CHARS = cls._ints_to_chars(cls._INTS)
                cls._BYTES = cls._CHARS.astype(DTYPE_BYTES)
            else:
                offset = len(cls._INTS)
                values_ext = np.arange(offset, cls._COUNT, dtype=cls._INTS_DTYPE)
                cls.shuffle(values_ext)
                cls._INTS = np.concatenate((cls._INTS, values_ext))
                cls._CHARS = np.concatenate((
                        cls._CHARS,
                        cls._ints_to_chars(values_ext, offset=offset),
                        ))
                cls._BYTES = cls._CHARS.astype(DTYPE_BYTES)

    @classmethod
    def dtype_to_element_iter(cls,
            dtype: TDtypeAny,
            count: int = COUNT_INIT,
            shift: int = 0,
            ) -> tp.Iterator[tp.Any]:

        cls.update_primitives(count)

        if dtype.kind == 'i': # int
            if dtype == cls._INTS_DTYPE:
                def gen() -> tp.Iterator[tp.Any]:
                    for v in cls._INTS:
                        yield v * (-1 if v % 3 == 0 else 1)
            else:
                def gen() -> tp.Iterator[tp.Any]:
                    for v in cls._INTS:
                        # NOTE: have to astype here with NumPy2, as fromiter rejects casting
                        yield v.astype(dtype) * (-1 if v % 3 == 0 else 1)

        elif dtype.kind == 'u': # int unsigned
            def gen() -> tp.Iterator[tp.Any]:
                yield from iter_shift(cls._INTS, 100)

        elif dtype.kind == 'f': # float
            def gen() -> tp.Iterator[tp.Any]:
                yield np.nan
                for v in cls._INTS:
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
                for v in cls._INTS:
                    yield v % 2 == 0

        elif dtype.kind  == 'U': # str
            def gen() -> tp.Iterator[tp.Any]:
                yield from cls._CHARS

        elif dtype.kind == 'S': # bytes
            def gen() -> tp.Iterator[tp.Any]:
                yield from cls._BYTES

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
                for i in cls._INTS:
                    for gen in gens:
                        # return at most 3 values from the gen
                        yield from take_count(gen, (i % 3) + 1)

        elif dtype.kind == 'M': # datetime64
            def gen() -> tp.Iterator[tp.Any]:
                for v in cls._INTS:
                    # NOTE: numpy ints, can use astype
                    yield v.astype(dtype)

        elif dtype.kind == 'm': # timedelta64
            def gen() -> tp.Iterator[tp.Any]:
                for v in cls._INTS:
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
            dtype: TDtypeAny,
            count: int = COUNT_INIT,
            shift: int = 0,
            gen: tp.Optional[tp.Iterator[tp.Any]] = None,
            ) -> TNDArrayAny:
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
            array = np.array([next(gen) for _ in range(count)], dtype=dtype)

        array.flags.writeable = False
        return array

    @classmethod
    @lru_cache(maxsize=128)
    def dtype_spec_to_array(cls,
            dtype_spec: TDtypeSpecOrSpecs,
            count: int = COUNT_INIT,
            shift: int = 0,
            ) -> TNDArrayAny:

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

class Grammar:
    FRAME = 'f'
    INDEX = 'i'
    COLUMNS = 'c'
    VALUES = 'v'
    SHAPE = 's'

    # KNOWN = {FRAME, INDEX, COLUMNS, VALUES, SHAPE}
    KNOWN = {
            FRAME: 'Frame',
            INDEX: 'Index',
            COLUMNS: 'Columns',
            VALUES: 'Values',
            SHAPE: 'Shape',
            }

    ARG_COUNT = {
            FRAME: frozenset((0, 1)),
            INDEX: frozenset((0, 2)),
            COLUMNS: frozenset((0, 2)),
            # VALUES can have any number of args
            SHAPE: frozenset((2,)),
            }

    SIGNATURES = {
            FRAME: '(CS,)',
            INDEX: '(CS, DS) or ((CS, ...), (DS, ...))',
            COLUMNS: '(CS, DS) or ((CS, ...), (DS, ...))',
            VALUES: '(DS, ...)',
            SHAPE: '(int, int)',
            }


    @classmethod
    def validate(cls,
            constructors: TStrConstructorsType,
            ) -> None:
        if cls.SHAPE not in constructors:
            raise FrameFixtureSyntaxError(f'missing required label: {cls.SHAPE}')

        for token in constructors.keys():
            if token in cls.ARG_COUNT:
                sizes = cls.ARG_COUNT[token]
                if len(constructors[token]) not in sizes:
                    raise FrameFixtureSyntaxError(f'component {token} has invalid number of arguments: {len(constructors[token])} not in {sizes}')
            elif token == cls.VALUES:
                pass
            else:
                raise FrameFixtureSyntaxError(f'invalid token: {token}')

    @classmethod
    def dsl_to_str_constructors(cls,
            dsl: str,
            ) -> TStrConstructorsType:

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

        constructors: TStrConstructorsType = {}

        for p in parts(): # each is a Call object
            key = p.func.id #type: ignore

            args: tp.List[TStrConstructorArg] = []
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
                    raise FrameFixtureSyntaxError(f'no handling for {arg}')

            constructors[key] = tuple(args)

        cls.validate(constructors) # will raise

        return constructors


class GrammarDoc:
    '''
    Tables for producing documentation of the grammar. These are not used at library runtime.
    '''

    @staticmethod
    def container_components(
            module_sf: tp.Optional[ModuleType] = None,
            ) -> 'Frame':
        str_to_type = StrToTypeInterface(module_sf)

        def records() -> tp.Iterator[tp.Tuple[tp.Any, ...]]:
            for arg, label in Grammar.KNOWN.items():
                not_required = arg not in Grammar.ARG_COUNT or 0 in Grammar.ARG_COUNT[arg]
                arguments = max(Grammar.ARG_COUNT.get(arg, ('unbound',)))
                sig = str(Grammar.SIGNATURES[arg])
                yield (arg, label, not not_required, arguments, sig)

        f = str_to_type['F'].from_records(
                records(),
                columns=('Symbol', 'Component', 'Required', 'Arguments', 'Signature'),
                dtypes=(str, str, bool, object, str),
                )
        return f #type: ignore

    @staticmethod
    def specifiers_constructor(
            module_sf: tp.Optional[ModuleType] = None,
            ) -> 'Frame':
        str_to_type = StrToTypeInterface(module_sf)

        def records() -> tp.Iterator[tp.Tuple[tp.Any, ...]]:
            for k, v in get_str_to_constructor(module_sf).items():
                if k == 'TB':
                    continue
                yield k, v.__name__

        f = str_to_type['F'].from_records(
                records(),
                columns=('Symbol', 'Class'),
                dtypes=(str, str),
                )
        return f #type: ignore

    @staticmethod
    def specifiers_dtype(
            module_sf: tp.Optional[ModuleType] = None,
            ) -> 'Frame':
        str_to_type = StrToTypeInterface(module_sf)

        def records() -> tp.Iterator[tp.Tuple[tp.Any, ...]]:
            for k, v in get_str_to_dtype().items():
                yield k, repr(v)

        f = str_to_type['F'].from_records(
                records(),
                columns=('Symbol', 'Class'),
                dtypes=(str, str),
                )
        return f #type: ignore



#-------------------------------------------------------------------------------
class Fixture:

    @staticmethod
    def _build_index(
            count: int,
            constructor: TConstructorOrConstructors,
            dtype_spec: TDtypeSpecOrSpecs,
            str_to_type: StrToTypeInterface,
            ) -> TIndexTypes:

        constructor_is_tuple = isinstance(constructor, tuple)

        if constructor_is_tuple or issubclass(constructor, str_to_type['IH']): #type: ignore
            # dtype_spec must be a tuple

            if not isinstance(dtype_spec, tuple) or len(dtype_spec) < 2:
                raise RuntimeError('for building IH dtype_spec must be a tuple')

            if constructor_is_tuple:
                if len(constructor) != len(dtype_spec): #type: ignore
                    raise RuntimeError('length of index_constructors must be the same as dtype_spec')
                is_static = {c.STATIC for c in constructor} #type: ignore
                assert len(is_static) == 1
                builder = str_to_type['IH'] if is_static.pop() else str_to_type['IHg']
                index_constructors = constructor
            else:
                builder = constructor #type: ignore
                index_constructors = str_to_type['IACF']

            # depth of 3 will provide repeats of 4, 2, 1
            repeats = [(x * 2 if x > 0 else 1) for x in range(len(dtype_spec)-1, -1, -1)]

            gens: tp.List[tp.Any] = []
            for i, dts in enumerate(dtype_spec):
                array = SourceValues.dtype_spec_to_array(dts, count=count, shift=10 * i)
                gens.append(repeat_count(array, repeats[i]))

            def labels() -> tp.Iterator[tp.Tuple[tp.Any, ...]]:
                for _ in range(count):
                    yield tuple(next(x) for x in gens)

            return builder.from_labels(labels(), index_constructors=index_constructors) #type: ignore

        # if constructor is IndexHierarchy, this will work, as array will be a 1D array of tuples that, when given to from_labels, will work
        array = SourceValues.dtype_spec_to_array(dtype_spec, count=count)
        return constructor.from_labels(array) #type: ignore

    @staticmethod
    def _build_type_blocks(
            shape: TShapeType,
            dtype_specs: tp.Sequence[TDtypeSpecOrSpecs],
            str_to_type: StrToTypeInterface,
            ) -> 'TypeBlocks':

        count_row, count_col = shape
        count_dtype = len(dtype_specs)

        def gen() -> tp.Iterator[TNDArrayAny]:
            ints = SourceValues.dtype_to_array(DTYPE_INT, count=count_col)
            max_shift = 100

            for col in range(count_col):
                yield SourceValues.dtype_spec_to_array(
                        dtype_specs[col % count_dtype],
                        count=count_row,
                        shift=ints[col] % max_shift
                        )
        return str_to_type['TB'].from_blocks(gen()).consolidate() #type: ignore

    #---------------------------------------------------------------------------
    @staticmethod
    def _str_to_build(
            constructor: TStrConstructorType, # typle of elements or tuples
            str_to_type: StrToTypeInterface,
            ) -> TBuildType:
        '''Convert strings to types or SF classes.
        '''
        def gen() -> tp.Iterator[TBuildArg]:
            for v in constructor:
                if isinstance(v, tuple):
                    yield tuple(str_to_type[part] for part in v) # type: ignore
                else:
                    yield str_to_type[v]
        return tuple(gen())

    @classmethod
    def _to_containers(cls,
            constructors: TStrConstructorsType,
            str_to_type: StrToTypeInterface,
            ) -> tp.Tuple['TypeBlocks',
                    tp.Optional[TIndexTypes],
                    tp.Optional[TIndexTypes],
                    ]:

        shape: TShapeType = tp.cast(TShapeType, constructors['s'])

        if Grammar.VALUES not in constructors:
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
                    constructor, # type: ignore
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
                    constructor, # type: ignore
                    dtype_spec,
                    str_to_type,
                    )
        else:
            columns = None

        return tb, index, columns

    @classmethod
    def parse(cls,
            dsl: str,
            module_sf: tp.Optional[ModuleType] = None,
            ) -> 'Frame':

        str_to_type = StrToTypeInterface(
                module_sf=module_sf,
                )
        constructors = Grammar.dsl_to_str_constructors(dsl)

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




def parse(dsl: str) -> 'Frame':
    '''
    Given a FrameFixtures DSL string, return a Fraem.
    '''
    return Fixture.parse(dsl=dsl)








