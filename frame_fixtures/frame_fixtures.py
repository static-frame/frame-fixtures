import typing as tp
from types import ModuleType
import ast
import random
from itertools import chain
from itertools import cycle
from functools import lru_cache
import string
from hashlib import blake2b

import numpy as np #type: ignore

if tp.TYPE_CHECKING:
    from static_frame import Frame #type: ignore #pylint: disable=W0611 #pragma: no cover
    from static_frame.core.util import DtypeSpecifier
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
DTYPE_KINDS_NO_FROMITER = ('O', 'U', 'S')

COUNT_INIT = 100_100

class SourceValues:
    SEED = 22

    _COUNT = 0
    _INTS = None
    _CHARS = None

    @classmethod
    def shuffle(cls, mutable: np.ndarray) -> None:
        state = np.random.get_state()
        np.random.seed(cls.SEED)
        np.random.shuffle(mutable)
        np.random.set_state(state)


    @classmethod
    def update_primitives(cls, count: int = COUNT_INIT) -> None:
        '''Update fixed sequences integers, characters.
        '''
        if count > cls._COUNT:
            cls._COUNT = count * 2

            values_int = np.arange(cls._COUNT, dtype=np.int64)
            cls.shuffle(values_int)
            cls._INTS = values_int

            values_char = np.empty(len(values_int), dtype='<U12')

            h = blake2b(digest_size=6) # gives 4214d8ebb6f8
            for i in values_int:
                h.update(str.encode(str(i)))
                values_char[i] = h.hexdigest()

            cls._CHARS = values_char

    @classmethod
    def dtype_to_element_iter(cls,
            dtype: np.dtype,
            count: int = COUNT_INIT,
            ) -> tp.Iterator[tp.Any]:
        # TODO: add a rotation or look ahead value

        cls.update_primitives(count)
        ints = cls._INTS
        chars = cls._CHARS

        if dtype.kind == 'i': # int
            def gen() -> tp.Iterator[tp.Any]:
                for v in ints:
                    yield v * (-1 if v % 3 == 0 else 1)

        elif dtype.kind == 'u': # int unsigned
            def gen() -> tp.Iterator[tp.Any]:
                yield from chain(ints[-1000:], ints[:-1000])

        elif dtype.kind == 'f': # float
            def gen() -> tp.Iterator[tp.Any]:
                yield np.nan
                for v in ints:
                    yield v * (-0.02 if v % 3 else 0.02)

        elif dtype.kind == 'c': # complex
            def gen() -> tp.Iterator[tp.Any]:
                for v, i in zip(
                        cls.dtype_to_element_iter(np.dtype(float)),
                        cls.dtype_to_element_iter(np.dtype(float)),
                        ):
                    yield complex(v, i)

        elif dtype.kind == 'b': # boolean
            def gen() -> tp.Iterator[bool]:
                for v in ints:
                    yield v % 2 == 0

        elif dtype.kind in ('U', 'S'): # str
            def gen() -> tp.Iterator[str]:
                yield from chars

        elif dtype.kind == 'O': # object
            def gen() -> tp.Iterator[tp.Any]:
                yield None
                yield True
                yield False

                gens = (cls.dtype_to_element_iter(np.dtype(int)),
                        cls.dtype_to_element_iter(np.dtype(float)),
                        cls.dtype_to_element_iter(np.dtype(str)),
                        )

                for i in range(cls.MAX_SIZE):
                    for gen in gens:
                        yield next(gen)

        elif dtype.kind == 'M': # datetime64
            def gen() -> tp.Iterator[np.datetime64]:
                for v in ints:
                    yield np.datetime64(v, np.datetime_data(dtype)[0])

        elif dtype.kind == 'm': # timedelta64
            def gen() -> tp.Iterator[np.datetime64]:
                for v in ints:
                    yield np.timedelta64(v, np.datetime_data(dtype)[0])

        else:
            raise NotImplementedError(f'no handling for {dtype}')

        return gen()

    @classmethod
    def dtype_to_array(cls,
            dtype: np.dtype,
            count: int,
            gen: tp.Optional[tp.Iterator[tp.Any]] = None,
            ) -> np.ndarray:
        '''
        Args:
            gen: optionally supply a generator of values
        '''
        if not gen:
            gen = cls.dtype_to_element_iter(dtype)

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
            count: int,
            ) -> np.ndarray:

        if isinstance(dtype_spec, tuple):
            # an object type of tuples
            gen = zip(*(cls.dtype_to_element_iter(np.dtype(dts))
                    for dts in dtype_spec))
            return cls.dtype_to_array(DTYPE_OBJECT, count=count, gen=gen)

        dtype = np.dtype(dtype_spec)
        return dtype_to_array(dtype, count)




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



















