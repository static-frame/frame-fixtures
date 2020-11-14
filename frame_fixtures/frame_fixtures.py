import typing as tp
from types import ModuleType
import ast

import numpy as np #type: ignore

if tp.TYPE_CHECKING:
    from static_frame import Frame #type: ignore #pylint: disable=W0611 #pragma: no cover


StrToType = tp.Dict[str, tp.Type[tp.Any]]
ConstructorArg = tp.Union[str, tp.Tuple[str, ...]]
ConstructorType = tp.Tuple[ConstructorArg, ...]

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
            # np.datetime_data(dt)
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



















