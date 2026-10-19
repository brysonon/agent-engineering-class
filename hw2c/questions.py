# The evaluation set for the judge.
#
# Each question carries three answers at a quality level I set deliberately, so
# the correct ranking is known before the judge ever runs. A judge that works
# ranks strong > middling > weak every time. That is the only reason I can say
# anything about whether a prompt change helped.
#
# The `strong` answers are the real ones I submitted on the 1h, 2a and 2b
# quizzes, most of which earned full marks. I wrote the `middling` and `weak`
# variants myself.

QUESTIONS = [
    {
        'id': 'agent-skill',
        'question': 'What is an agent skill? How is it defined? How is it used?',
        'required_points': [
            'A skill is a packaged set of instructions (and optionally files) for a specific kind of task',
            'It is defined in a folder containing a SKILL.md file with a name and description',
            'Only the metadata (name/description) sits in context; the body loads when the task matches',
        ],
        'strong': (
            'A skill is a packaged set of instructions and files that teaches an agent how to do a '
            'specific kind of task. It is defined usually in a folder with a SKILL.md file. Each skill '
            'has a name and a description, and the body holds the detailed instructions. The agent is '
            'given every skill in its context, but it only sees each skill’s metadata. When a task '
            'matches one, it loads the instructions only when needed and follows them in full context.'
        ),
        'middling': (
            'A skill is a set of instructions you give an agent so it knows how to do something. You '
            'write it in a markdown file and the agent reads it when it needs to. It helps the agent '
            'do tasks the right way instead of guessing.'
        ),
        'weak': (
            'An agent skill is a special ability that gets trained into the model so it permanently '
            'knows how to do a task. You enable skills in the settings and the model is retrained with '
            'them, which is why skills make the model smarter over time.'
        ),
    },
    {
        'id': 'harness-engineering',
        'question': 'Describe harness engineering. What is it? What goal does it seek to achieve?',
        'required_points': [
            'It is the design of everything surrounding the model: tools, context, memory, instructions',
            'The environment is built for a specific purpose rather than being general',
            'The goal is reliable agent work with less human supervision; humans set direction',
        ],
        'strong': (
            'Harness engineering is designing everything around the model. It includes its tools, '
            'context, memory, and instructions. It is what you build around the agent, usually gearing '
            'it towards a specific purpose. The goal is to make agents reliable enough to do lots of '
            'work with less human supervision. Humans set the direction and build the environment '
            'while agents do the work.'
        ),
        'middling': (
            'Harness engineering means building things around the model so it works better. You set up '
            'the tools and the prompts so the agent can do its job. The goal is to get better results '
            'out of the agent than you would with just a prompt.'
        ),
        'weak': (
            'Harness engineering is the process of fine-tuning a model on your own data so it performs '
            'better on your tasks. You collect examples, train the model on them, and the harness is '
            'the training pipeline that produces the improved weights.'
        ),
    },
    {
        'id': 'progressive-disclosure',
        'question': 'What is progressive disclosure? Why is it important?',
        'required_points': [
            'Information is given to the agent in layers, only as needed',
            'Example: skill metadata is always present, full instructions load on demand',
            'It matters because the context window is limited and loading everything wastes tokens and distracts the agent',
        ],
        'strong': (
            'Progressive disclosure is giving the agent information in layers only as it needs it. For '
            'example, it sees short summaries of a skill’s name and description and only loads the '
            'full instructions when they are needed. An agent is only given the context it requires and '
            'nothing more. This matters because the context window is limited and loading everything up '
            'front wastes tokens and can over-burden the agent. It keeps the agent more focused and '
            'within the realm it is meant to operate in.'
        ),
        'middling': (
            'Progressive disclosure means you do not give the agent everything at once. You give it '
            'information a bit at a time. This is important because too much information is not good '
            'for the agent and it might get confused.'
        ),
        'weak': (
            'Progressive disclosure is a user interface principle where you hide advanced options behind '
            'an "advanced settings" menu so beginners are not overwhelmed. In agents it means showing '
            'the user a simple answer first and the detailed reasoning only if they click to expand it.'
        ),
    },
    {
        'id': 'agent-legibility',
        'question': 'Describe the principle of agent legibility. Why is it important? What does it aim to accomplish?',
        'required_points': [
            'Making the codebase and environment easy for an agent to read and verify',
            'Concrete means: AGENTS.md, consistent conventions, readable logs and errors',
            'It lets the agent verify its own work and act autonomously without a human explaining the system',
        ],
        'strong': (
            'Agent legibility is making the codebase and environment easy for an agent to read and '
            'check. For example, giving an agent a good AGENTS.md file, using consistent conventions, '
            'and making logs easy for the agent to read. This is important because the agent cannot use '
            'information that is not in its context, and it keeps the agent from getting confused or '
            'missing relevant information. Agent legibility lets the agent understand the entire system '
            'and verify its own work without a human having to explain things to it.'
        ),
        'middling': (
            'Agent legibility means making your code readable for the agent. If the code is clean and '
            'well organized the agent will do a better job with it. It is important because confusing '
            'code leads to confusing results.'
        ),
        'weak': (
            'Agent legibility is about making the agent’s own reasoning visible to the user so you can '
            'read its chain of thought and see why it made a decision. It aims to build trust by making '
            'the model explain itself in plain language.'
        ),
    },
    {
        'id': 'trust-folder',
        'question': 'Why does Codex ask whether you trust a folder?',
        'required_points': [
            'Codex reads the folder’s contents automatically',
            'It may follow instructions found in those files (prompt injection), not merely execute code',
            'Consequences include running malicious code or exposing sensitive information',
        ],
        'strong': (
            'Codex asks whether you trust a folder because it reads the folder’s contents and may '
            'follow instructions it finds in those files. A file in an untrusted repository can contain '
            'instructions aimed at the agent rather than at a human reader, which could get malicious '
            'code executed on my machine or expose sensitive information. Because agents automatically '
            'read and load files, opening an untrusted repository hands that content to the agent '
            'before I have reviewed it.'
        ),
        'middling': (
            'Codex asks about trusting a folder to prevent malicious code from being executed. Opening '
            'a repository you do not trust could let bad code run on your machine and steal your '
            'information, since agents read and load files automatically.'
        ),
        'weak': (
            'Codex asks whether you trust a folder so it knows whether to index the files for search. '
            'Trusted folders get indexed for faster lookups and untrusted ones are skipped, which is '
            'mostly a performance and privacy preference rather than a security boundary.'
        ),
    },
    {
        'id': 'agents-md',
        'question': 'What is an AGENTS.md file, and what purpose does it serve for a coding agent?',
        'required_points': [
            'A Markdown file of explicit instructions for coding agents, like a README but for the agent',
            'Lives in the repository (root, or nearest file to the working directory)',
            'Conveys project conventions and guides behavior, improving consistency',
        ],
        'strong': (
            'An AGENTS.md file is a markdown file given to the agent to provide explicit instructions to '
            'AI coding agents, like a README file for users. It lies in the root of the repository. It '
            'tells the agent what conventions are used in that specific project and guides its behavior. '
            'It also helps improve consistency by grounding the agent in the project’s specific rules.'
        ),
        'middling': (
            'AGENTS.md is a file that tells the agent about your project. You put it in your repo and '
            'the agent reads it. It helps the agent understand what you want.'
        ),
        'weak': (
            'AGENTS.md is a configuration file where you declare which agents are allowed to run in the '
            'repository and what permissions each one has. The coding agent parses it at startup to '
            'determine whether it is authorized to edit files in that project.'
        ),
    },
]

TIERS = ['strong', 'middling', 'weak']
