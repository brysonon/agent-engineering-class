import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
FENCE = '````'

CASES = [
    ('Mixed signals (the 1a Avatar case)', 'bender-input-mixed.txt', 'bender'),
    ('Empty input (the 1a hallucination case)', 'bender-input-empty.txt', 'bender'),
    ('Off-topic input', 'bender-input-offtopic.txt', 'bender'),
    ('Clear single element', 'bender-input-clear.txt', 'bender'),
    ('Forbidden library requested (the 1a CANNOT COMPLY case)', 'code-input-numpy.txt', 'code'),
    ('Satisfiable request', 'code-input-valid.txt', 'code'),
]

PROMPTS = {
    'bender': ('bender-prompt-1a.md', 'bender-prompt.md'),
    'code': ('code-prompt-1a.md', 'code-prompt.md'),
}


def compiles(source: str) -> str:
    try:
        compile(source, '<generated>', 'exec')
        return 'parses as valid Python'
    except SyntaxError as error:
        return f'**SyntaxError: {error.msg} (line {error.lineno})**'


def run(model: str, prompt: str, input_file: str, schema: str | None):
    command = [sys.executable, 'structured_app.py', prompt, input_file, '--model', model]
    if schema:
        command += ['--schema', schema]

    result = subprocess.run(command, cwd=HERE, capture_output=True, text=True)
    if result.returncode != 0:
        raise SystemExit(f'Run failed: {" ".join(command)}\n{result.stderr}')

    cost = re.search(r'Total cost \(USD\): (\S+)', result.stderr)
    seconds = re.search(r'(\S+) seconds elapsed', result.stderr)
    return {
        'command': ' '.join(['python'] + command[1:]),
        'output': result.stdout.strip(),
        'cost': cost.group(1) if cost else '?',
        'seconds': seconds.group(1) if seconds else '?',
    }


def extract_code(output: str, schema: str | None) -> tuple[str | None, str]:
    if schema:
        return json.loads(output).get('code'), 'the `code` field, unescaped'
    match = re.search(r'```(?:python)?\n(.*?)```', output, re.S)
    source = match.group(1) if match else None
    return source, 'the fenced block, after stripping the Markdown fence'


def main(model: str, out_file: Path):
    lines = [
        '# Side-by-side: 1a plain text vs 1b structured output',
        '',
        f'Every run below uses `{model}` and the same app, `structured_app.py`. Within '
        'each case the input file is identical; the only differences are which prompt '
        'file is passed and whether `--schema` is set. The 1a column is the prompt and '
        'plain-text output from homework 1a, reproduced here so the two can be compared '
        'directly.',
        '',
        "Cost and elapsed time are from the app's own usage report. Single runs, so treat "
        'the timings as rough.',
        '',
    ]

    for title, input_file, schema in CASES:
        prompt_1a, prompt_1b = PROMPTS[schema]
        print('running', title, file=sys.stderr)
        lines += [
            f'## {title}',
            '',
            f'**Input** (`{input_file}`):',
            f'{FENCE}text',
            (HERE / input_file).read_text(encoding='utf-8') or '(empty file)',
            FENCE,
            '',
        ]

        variants = [('1a - plain text', prompt_1a, None), ('1b - structured output', prompt_1b, schema)]
        for label, prompt, active_schema in variants:
            result = run(model, prompt, input_file, active_schema)
            lines += [
                f'### {label}',
                '',
                f'{FENCE}console',
                f'$ {result["command"]}',
                FENCE,
                '',
                f'{FENCE}{"json" if active_schema else "text"}',
                result['output'] or '(no output)',
                FENCE,
                '',
            ]

            if schema == 'code':
                source, origin = extract_code(result['output'], active_schema)
                if source:
                    lines += [
                        f'Extracted from {origin}:',
                        '',
                        f'{FENCE}python',
                        source.strip(),
                        FENCE,
                        '',
                        f'Result: {compiles(source)}.',
                        '',
                    ]

            lines += [f'*{result["seconds"]}s, {result["cost"]}*', '']

    out_file.write_text('\n'.join(lines), encoding='utf-8')
    print(f'wrote {out_file.name}', file=sys.stderr)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Regenerate the side-by-side comparison transcript')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--out', type=Path, default=HERE / 'side-by-side-output.md')
    args = parser.parse_args()
    main(args.model, args.out)
