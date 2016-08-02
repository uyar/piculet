from subprocess import Popen, PIPE

import os


def test_no_arguments_should_fail_with_usage_string():
    command = ['woody']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 1
    assert stdout.startswith(b'usage:')
    assert stderr == b''


def test_start_through_module_should_be_accessible():
    command = ['python', '-m', 'woody']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 1
    assert stdout.startswith(b'usage:')
    assert stderr == b''


def test_dash_h_should_output_usage_string():
    command = ['woody', '-h']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 0
    assert stdout.startswith(b'usage:')
    assert stderr == b''


def test_double_dash_help_should_output_usage_string():
    command = ['woody', '--help']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 0
    assert stdout.startswith(b'usage:')
    assert stderr == b''


def test_unrecognized_arguments_should_fail_with_error_message():
    command = ['woody', '--foo']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 2
    assert stderr.startswith(b'usage:')
    assert b'unrecognized arguments' in stderr


def test_unknown_command_should_fail_with_error_message():
    command = ['woody', 'foo']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 2
    assert stderr.startswith(b'usage:')
    assert b'argument command: invalid choice' in stderr


def test_debug_mode_should_generate_debug_messages():
    command = ['woody', '--debug']
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 1
    assert b'running in debug mode' in stderr


def test_h2x_should_be_accessible():
    infile = os.path.join(os.path.dirname(__file__), 'files',
                          'utf-8_charset_utf-8.html')
    with open(infile) as f:
        content = f.read()
    command = ['woody', 'h2x', infile]
    process = Popen(command, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 0
    assert stdout == content.encode('utf-8')


def test_h2x_should_be_accessible_from_stdin():
    infile = os.path.join(os.path.dirname(__file__), 'files',
                          'utf-8_charset_utf-8.html')
    with open(infile) as f:
        content = f.read()
    command = 'cat {} | woody h2x -'.format(infile)
    process = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    stdout, stderr = process.communicate()
    assert process.returncode == 0
    assert stdout == content.encode('utf-8')
