import os
import pytest
from template_manager import TemplateManager


def create_pine_file(dir_path, filename, content):
    file_path = os.path.join(dir_path, filename)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    return file_path

@pytest.fixture
def pine_dir(tmp_path):
    templates_path = tmp_path / "templates"
    templates_path.mkdir()

    # Various input declarations
    int_content = (
        '//@version=5\n'
        'indicator("Test Int")\n'
        'len = input.int(title="Len", defval=14, minval=1, maxval=50, step=1)\n'
    )
    float_content = (
        '//@version=5\n'
        'indicator("Test Float")\n'
        'th = input.float(title="Threshold", defval=0.5, minval=0.0, maxval=1.0)\n'
    )
    bool_content = (
        '//@version=5\n'
        'indicator("Test Bool")\n'
        'useMA = input.bool(title="Use MA", defval=true)\n'
    )
    string_content = (
        '//@version=5\n'
        'indicator("Test String")\n'
        'mode = input.string(title="Mode", defval="long")\n'
    )

    create_pine_file(str(templates_path), 'int_test.pine', int_content)
    create_pine_file(str(templates_path), 'float_test.pine', float_content)
    create_pine_file(str(templates_path), 'bool_test.pine', bool_content)
    create_pine_file(str(templates_path), 'string_test.pine', string_content)

    return str(templates_path)


def test_int_and_float_parsing(pine_dir):
    tm = TemplateManager(pine_dir)
    templates = {t.name: t for t in tm.get_templates()}

    # Test int input
    assert 'int_test' in templates
    t_int = templates['int_test']
    ps_int = t_int.param_space
    assert 'Len' in ps_int
    entry_int = ps_int['Len']
    assert entry_int['type'] == 'int'
    assert entry_int['default'] == 14
    assert entry_int['bounds'] == (1, 50)
    assert entry_int['step'] == 1

    # Test float input
    assert 'float_test' in templates
    t_float = templates['float_test']
    ps_float = t_float.param_space
    assert 'Threshold' in ps_float
    entry_float = ps_float['Threshold']
    assert entry_float['type'] == 'float'
    assert entry_float['default'] == pytest.approx(0.5)
    assert entry_float['bounds'] == (0.0, 1.0)
    assert entry_float['step'] is None


def test_bool_and_string_parsing(pine_dir):
    tm = TemplateManager(pine_dir)
    templates = {t.name: t for t in tm.get_templates()}

    # Test bool input
    assert 'bool_test' in templates
    t_bool = templates['bool_test']
    ps_bool = t_bool.param_space
    assert 'Use MA' in ps_bool
    entry_bool = ps_bool['Use MA']
    assert entry_bool['type'] == 'bool'
    assert entry_bool['default'] is True
    assert entry_bool['bounds'] is None
    assert entry_bool['step'] is None

    # Test string input
    assert 'string_test' in templates
    t_string = templates['string_test']
    ps_string = t_string.param_space
    assert 'Mode' in ps_string
    entry_string = ps_string['Mode']
    assert entry_string['type'] == 'string'
    assert entry_string['default'] == 'long'
    assert entry_string['bounds'] is None
    assert entry_string['step'] is None
