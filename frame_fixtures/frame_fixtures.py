import typing as tp
from types import ModuleType
from collections import defaultdict
import ast

if tp.TYPE_CHECKING:
    from static_frame import Frame # pylint: disable=W0611 #pragma: no cover


StrToType = tp.Dict[str, tp.Type]
ConstructorType = tp.Tuple[tp.Union[str, tp.Tuple[str, ...]], ...]

class Fixture:

    TL_KEYS = {'f', 'i', 'c', 'v', 's'}

    @staticmethod
    def get_str_to_type(
            module_sf: tp.Optional[ModuleType],
            module_np: tp.Optional[ModuleType],
            ) -> StrToType:
        if module_sf is None:
            import static_frame as sf
            module_sf = sf
        if module_np is None:
            import numpy as np
            module_np = np

        ref = {}
        for cls in (
                module_sf.Frame,
                module_sf.FrameGO,
                module_sf.Index,
                module_sf.IndexGO,
                module_sf.IndexHierarchy,
                module_sf.IndexHierarchyGO,
                module_sf.IndexYear,
                module_sf.IndexYearGO,
                module_sf.IndexYearMonth,
                module_sf.IndexYearMonthGO,
                module_sf.IndexDate,
                module_sf.IndexDateGO,
                module_sf.IndexSecond,
                module_sf.IndexSecondGO,
                module_sf.IndexNanosecond,
                module_sf.IndexNanosecondGO,
                ):
            key = ''.join(c for c in cls.__name__ if c.isupper()).replace('GO', 'g')
            ref[key] = cls

        for cls in (
                module_np.dtype('datetime64[Y]'),
                module_np.dtype('datetime64[M]'),
                module_np.dtype('datetime64[D]'),
                # NOTE: we not expose hour as IH is ambiguous
                module_np.dtype('datetime64[s]'),
                module_np.dtype('datetime64[ns]'),
                ):
            # np.datetime_data(dt)
            key = f'dt{module_np.datetime_data(cls)[0]}'
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
            ) -> ConstructorType:

        tree = ast.parse(dsl)
        bin_op_active = tree.body[0].value # this is as BinOp

        def parts() -> tp.Iterator[ast.Call]:
            nonlocal bin_op_active
            while True:
                yield bin_op_active.right # this is a Call object
                if isinstance(bin_op_active.left, ast.Call):
                    yield bin_op_active.left
                    return
                bin_op_active = bin_op_active.left

        constructors = defaultdict(list)

        for p in parts(): # each is a Call object
            key = p.func.id

            for arg in p.args:
                if isinstance(arg, ast.Tuple):
                    constructors[key].append(tuple(sub.id for sub in arg.elts))
                elif isinstance(arg, ast.Name):
                    constructors[key].append(arg.id)
                elif isinstance(arg, ast.Constant):
                    constructors[key].append(arg.value)
                else:
                    raise NotImplementedError(f'no handling for {arg}')

            constructors[key] = tuple(constructors[key])

        if set(constructors.keys()) != cls.TL_KEYS:
            raise SyntaxError(f'missing keys: {cls.TL_KEYS - constructors.keys()}')

        return constructors

    @classmethod
    def to_frame(cls,
            dsl: str,
            module_sf: tp.Optional[ModuleType] = None,
            module_np: tp.Optional[ModuleType] = None,
            ) -> 'Frame':

        str_to_type = cls.get_str_to_type(
                module_sf=module_sf,
                module_np=module_np,
                )
        constructors = cls.dsl_to_constructors(dsl)
        print(constructors)
        import ipdb; ipdb.set_trace()