import argparse
import json
import subprocess
import sys
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI


CONTAINER = 'agent-sandbox'
MAX_TURNS = 20
TIMEOUT_SECONDS = 30
MAX_OUTPUT_CHARS = 4000

INSTRUCTIONS = (
    'You are a coding agent. Your shell tool runs bash inside a Linux '
    'container whose working directory is /workspace. Explore before you '
    'act, keep commands short, and finish with a concise report of what you '
    'did and what you observed.'
)

TOOLS = [{
    'type': 'function',
    'name': 'shell',
    'description': 'Run a bash command in the sandbox container and return its output.',
    'parameters': {
        'type': 'object',
        'properties': {'command': {'type': 'string'}},
        'required': ['command'],
        'additionalProperties': False,
    },
    'strict': True,
}]


def _run_in_sandbox(command, log):
    log(f'\n$ {command}')
    try:
        # The API key stays on the host; only the command crosses into the container.
        # --exec skips the WSL shell, which would otherwise expand $(...) and
        # backticks on the host before docker ever sees the command.
        result = subprocess.run(
            ['wsl', '-d', 'Ubuntu', '--exec', 'docker', 'exec', CONTAINER,
             'timeout', str(TIMEOUT_SECONDS), 'bash', '-c', command],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
            timeout=TIMEOUT_SECONDS + 15,
        )
        output = result.stdout + result.stderr + f'\n[exit code {result.returncode}]'
    except subprocess.TimeoutExpired:
        output = f'[killed after {TIMEOUT_SECONDS} seconds]'
    if len(output) > MAX_OUTPUT_CHARS:
        output = output[:MAX_OUTPUT_CHARS] + '\n[output truncated]'
    log(output)
    return output


def run_agent(client, model, task, log):
    next_input = [{'role': 'user', 'content': task}]
    previous_response_id = None

    for _ in range(MAX_TURNS):
        response = client.responses.create(
            model=model,
            instructions=INSTRUCTIONS,
            input=next_input,
            previous_response_id=previous_response_id,
            reasoning={'effort': 'low'},
            tools=TOOLS,
        )
        calls = [item for item in response.output if item.type == 'function_call']
        if not calls:
            return response.output_text

        next_input = []
        for call in calls:
            command = json.loads(call.arguments)['command']
            next_input.append({
                'type': 'function_call_output',
                'call_id': call.call_id,
                'output': _run_in_sandbox(command, log),
            })
        previous_response_id = response.id

    return f'[stopped at the {MAX_TURNS}-turn limit]'


def main(model, task_file, transcript):
    load_dotenv(Path(__file__).resolve().parents[2] / '.env')
    task = task_file.read_text()
    lines = [f'# Task: {task_file.name}\n\n{task}']

    def log(text):
        print(text, file=sys.stderr)
        lines.append(text)

    # WSL shuts down when idle, which stops the container, so hold a session open.
    keepalive = subprocess.Popen(['wsl', '-d', 'Ubuntu', '--', 'sleep', 'infinity'])
    try:
        subprocess.run(['wsl', '-d', 'Ubuntu', '--', 'docker', 'start', CONTAINER],
                       check=True, capture_output=True)
        answer = run_agent(OpenAI(), model, task, log)
    finally:
        keepalive.terminate()
    lines.append(f'\nAGENT: {answer}')
    print('AGENT:', answer)
    transcript.parent.mkdir(exist_ok=True)
    transcript.write_text('\n'.join(lines), encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Agent whose shell runs in a Docker sandbox')
    parser.add_argument('task_file', type=Path)
    parser.add_argument('--model', default='gpt-5.6-sol')
    parser.add_argument('--transcript', type=Path)
    args = parser.parse_args()
    transcript = args.transcript or (
        Path(__file__).with_name('transcripts') / f'{args.task_file.stem}.txt'
    )
    main(args.model, args.task_file, transcript)
