# A custom agent built around the question this assignment asks:
# which decisions am I willing to let an agent make?
#
# In HW1g my agent ran every tool the model asked for, immediately and without
# asking. That is an answer to the question -- "all of them" -- but it is an
# answer I made by accident, just by not writing a confirmation step.
#
# This agent makes the answer explicit. Every tool declares a DecisionTier, and
# the loop enforces it:
#
#   AUTO     The agent decides and acts. Reversible, low-stakes, menial.
#   CONFIRM  The agent decides and proposes; I approve before it acts.
#   RESERVED The agent may not act. It can explain what it would do and why,
#            but the decision stays mine.
#
# RESERVED is the interesting tier. The capability exists and the model knows
# about it, so the agent can still reason about the decision and advise me.
# What it cannot do is make it. That distinction -- advice versus authority --
# is the one my write-up is really about.
#
#   python decision_agent.py                      # interactive
#   python decision_agent.py --approve-all        # treat CONFIRM as AUTO
#   python decision_agent.py --dry-run            # show tiers, call nothing

import argparse
import json
import shutil
import sys
from enum import Enum
from pathlib import Path
from time import time

from dotenv import load_dotenv
from openai import OpenAI

from usage import print_usage

load_dotenv(Path(__file__).resolve().parent.parent / '.env')


class DecisionTier(Enum):
    AUTO = 'auto'
    CONFIRM = 'confirm'
    RESERVED = 'reserved'


SYSTEM_PROMPT = """You are an agent operating under an explicit decision policy.

Each of your tools carries a decision tier:

- auto: you may call it freely.
- confirm: you may call it, but the user approves before it runs. Explain why
  you want to call it; a bare request is harder to approve.
- reserved: you may NOT call it. The user has kept this decision. You can still
  reason about it and recommend a course of action, and you should when it is
  relevant -- your judgment is wanted, your authority is not.

If a task needs a reserved action, say plainly what you would do and why, and
leave the decision with the user. Do not route around the policy by using an
auto tool to accomplish what a reserved tool would have done.
"""


class PolicyToolBox:
    """A tool registry where every tool carries the tier of decision it makes."""

    def __init__(self):
        self._funcs = {}
        self._tiers = {}
        self.schemas = []

    def tool(self, tier: DecisionTier, description: str, parameters: dict):
        def register(func):
            self._funcs[func.__name__] = func
            self._tiers[func.__name__] = tier
            self.schemas.append({
                'type': 'function',
                'name': func.__name__,
                # The tier goes in the description so the model can plan around
                # it rather than discovering the boundary by being refused.
                'description': f'[{tier.value}] {description}',
                'parameters': parameters,
                'strict': True,
            })
            return func
        return register

    def tier_of(self, name): return self._tiers.get(name)
    def func_of(self, name): return self._funcs.get(name)


toolbox = PolicyToolBox()

_STR = lambda *names: {
    'type': 'object',
    'properties': {n: {'type': 'string'} for n in names},
    'required': list(names),
    'additionalProperties': False,
}


@toolbox.tool(DecisionTier.AUTO, 'List files under a directory.', _STR('directory'))
def list_files(directory: str) -> str:
    base = Path(directory).expanduser()
    if not base.is_dir():
        return f'Not a directory: {base}'
    return '\n'.join(sorted(p.name + ('/' if p.is_dir() else '') for p in base.iterdir())) or '(empty)'


@toolbox.tool(DecisionTier.AUTO, 'Read a text file.', _STR('path'))
def read_file(path: str) -> str:
    try:
        return Path(path).expanduser().read_text(encoding='utf-8')[:8000]
    except Exception as exc:
        return f'Failed to read: {type(exc).__name__}: {exc}'


@toolbox.tool(DecisionTier.CONFIRM, 'Write text to a file, overwriting it.', _STR('path', 'content'))
def write_file(path: str, content: str) -> str:
    target = Path(path).expanduser()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding='utf-8')
    return f'Wrote {target} ({len(content)} chars)'


@toolbox.tool(DecisionTier.CONFIRM, 'Delete a file or directory.', _STR('path'))
def delete_path(path: str) -> str:
    target = Path(path).expanduser()
    if not target.exists():
        return f'Nothing at {target}'
    shutil.rmtree(target) if target.is_dir() else target.unlink()
    return f'Deleted {target}'


@toolbox.tool(
    DecisionTier.RESERVED,
    'Submit coursework for a grade. Reserved: submitting is a claim about my own '
    'learning, so it stays mine to make.',
    _STR('assignment', 'file_path'),
)
def submit_assignment(assignment: str, file_path: str) -> str:
    return 'unreachable: reserved tools are never executed'


@toolbox.tool(
    DecisionTier.RESERVED,
    'Send a message to another person on my behalf. Reserved: speaking to someone '
    'in my own voice is not something I delegate.',
    _STR('recipient', 'message'),
)
def send_message(recipient: str, message: str) -> str:
    return 'unreachable: reserved tools are never executed'


def describe_policy() -> str:
    rows = []
    for schema in toolbox.schemas:
        name = schema['name']
        rows.append(f"  {toolbox.tier_of(name).value:9} {name}")
    return '\n'.join(rows)


def confirm(name: str, args: dict) -> bool:
    print(f'\n  [confirm] the agent proposes: {name}', file=sys.stderr)
    for key, value in args.items():
        shown = str(value)
        print(f'            {key}: {shown[:300]}{"..." if len(shown) > 300 else ""}', file=sys.stderr)
    try:
        return input('            approve? [y/N] ').strip().lower() in {'y', 'yes'}
    except EOFError:
        return False


def dispatch(name: str, args: dict, approve_all: bool, dry_run: bool) -> str:
    tier = toolbox.tier_of(name)

    if tier is DecisionTier.RESERVED:
        print(f'  [reserved] refused: {name}', file=sys.stderr)
        return (
            f'REFUSED. `{name}` is reserved to the user, who has not delegated this '
            f'decision. Explain what you would do and why, and leave the choice to them.'
        )

    if dry_run:
        print(f'  [dry-run]  would call: {name}', file=sys.stderr)
        return f'DRY RUN: {name} was not executed.'

    if tier is DecisionTier.CONFIRM and not approve_all:
        if not confirm(name, args):
            return f'DECLINED. The user did not approve `{name}`. Do not retry it another way.'

    print(f'  [{tier.value}] {name}', file=sys.stderr)
    try:
        return str(toolbox.func_of(name)(**args))
    except Exception as exc:
        return f'Tool raised {type(exc).__name__}: {exc}'


def run_turn(client, model, reasoning, history, approve_all, dry_run):
    turn, usage = [], []
    while True:
        response = client.responses.create(
            model=model,
            input=history + turn,
            reasoning={'effort': reasoning},
            tools=toolbox.schemas,
        )
        turn += response.output
        usage.append((response.model, response.usage))

        # A response can carry BOTH a text message and a function call -- the
        # model often narrates what it is about to do. Returning as soon as
        # there is text leaves that call unanswered, and the next request fails
        # with "No tool output found for function call". So dispatch first, and
        # only treat the turn as finished when nothing was called.
        calls = [item for item in response.output if item.type == 'function_call']

        if not calls:
            return response.output_text, turn, usage

        for item in calls:
            result = dispatch(item.name, json.loads(item.arguments), approve_all, dry_run)
            turn.append({
                'type': 'function_call_output',
                'call_id': item.call_id,
                'output': result,
            })


def main(model, reasoning, approve_all, dry_run):
    client = OpenAI()
    print('Decision policy for this agent:', file=sys.stderr)
    print(describe_policy(), file=sys.stderr)
    print('\nPress Enter on an empty line to quit.\n', file=sys.stderr)

    history = [{'role': 'system', 'content': SYSTEM_PROMPT}]
    usage = []

    while True:
        try:
            message = input('USER: ')
        except EOFError:
            break
        if not message:
            break

        history.append({'role': 'user', 'content': message})
        start = time()
        text, turn, turn_usage = run_turn(client, model, reasoning, history, approve_all, dry_run)
        history += turn
        usage += turn_usage
        print(f'{round(time() - start, 2)} seconds elapsed', file=sys.stderr)
        print('AGENT:', text, '\n')

    if usage:
        print_usage(usage)


if __name__ == '__main__':
    parser = argparse.ArgumentParser('Agent with an explicit decision policy')
    parser.add_argument('--model', default='gpt-5.6-luna')
    parser.add_argument('--reasoning', default='none')
    parser.add_argument('--approve-all', action='store_true', help='treat confirm as auto')
    parser.add_argument('--dry-run', action='store_true', help='never execute, just report tiers')
    args = parser.parse_args()
    main(args.model, args.reasoning, args.approve_all, args.dry_run)
