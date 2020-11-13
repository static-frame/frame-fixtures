import typing as tp
from types import ModuleType
from collections import defaultdict
import ast



StrToType = tp.Dict[str, tp.Type]
ConstructorType = tp.Tuple[tp.Union[str, tp.Tuple[str, ...]], ...]

class Fixture:

    @staticmethod
    def get_str_to_type(
            module_sf: tp.Optional[ModuleType] = None,
            module_np: tp.Optional[ModuleType] = None,
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
            pass



    @classmethod
    def from_str(cls,
            dsl: str,
            str_to_type: StrToType = None,
            ) -> 'Fixture':

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

        print(constructors)
        return cls(constructors, str_to_type)


    def __init__(self,
            constructors: tp.Dict[str, ConstructorType],
            str_to_type: StrToType = None,
            ):
        pass