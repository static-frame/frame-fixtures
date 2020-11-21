import sys
import os
import typing as tp

import invoke

#-------------------------------------------------------------------------------

@invoke.task
def clean(context):
    '''Clean doc and build artifacts
    '''
    context.run('rm -rf .coverage')
    context.run('rm -rf coverage.xml')
    context.run('rm -rf htmlcov')
    context.run('rm -rf build')
    context.run('rm -rf dist')
    context.run('rm -rf *.egg-info')
    context.run('rm -rf .mypy_cache')
    context.run('rm -rf .pytest_cache')



#-------------------------------------------------------------------------------

@invoke.task
def test(context,
        unit=False,
        cov=False,):
    '''Run tests.
    '''

    cmd = f'pytest -s --color no --disable-pytest-warnings --tb=native frame_fixtures'
    if cov:
        cmd += ' --cov=frame_fixtures --cov-report=xml'
    print(cmd)
    context.run(cmd)

@invoke.task
def grammar(context):
    from frame_fixtures.core import GrammarDoc
    import static_frame as sf #type: ignore

    config = sf.DisplayConfig(include_index=False, type_show=False, cell_max_width=40)
    # container components
    cc = GrammarDoc.container_components()
    print(cc.to_rst(config))

    # container types
    cc = GrammarDoc.specifiers_constructor()
    print(cc.to_rst(config))

    # container types
    cc = GrammarDoc.specifiers_dtype()
    print(cc.to_rst(config))



@invoke.task
def coverage(context):
    '''
    Perform code coverage, and open report HTML.
    '''
    cmd = 'pytest -s --color no --disable-pytest-warnings --cov=frame_fixtures --cov-report html'
    print(cmd)
    context.run(cmd)
    import webbrowser
    webbrowser.open('htmlcov/index.html')


@invoke.task
def mypy(context):
    '''Run mypy static analysis.
    '''
    context.run('mypy --strict')

@invoke.task
def lint(context):
    '''Run pylint static analysis.
    '''
    context.run('pylint frame_fixtures')

@invoke.task(pre=(lint, mypy))
def quality(context):
    '''Run quality checks.
    '''
    pass

#-------------------------------------------------------------------------------

@invoke.task(pre=(clean,))
def build(context):
    '''Build packages
    '''
    context.run(f'{sys.executable} setup.py sdist bdist_wheel')

@invoke.task(pre=(build,), post=(clean,))
def release(context):
    context.run('twine upload dist/*')


