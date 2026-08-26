"""
Server instructions for the Terrace MCP server.

The tools compute and the agent narrates. terrace_tools.py is the computing half.
This is the narrating half: the text handed to every client in the initialize
result, so it reaches Claude Desktop over stdio and the hosted connector over
streamable-http alike.

It is deliberately short. It carries the reading level handshake, the prose
budget, the honesty rules that must survive any style override, and one pointer
to report_style for the full format. The format contract itself is far longer and
lives behind that tool, so a conversation that never builds a report never pays
for it.

TERRACE_DEFAULT_MODE pins the reading level for a client that always has the same
reader, which is the usual case for a personal server. Unset means ask once.
"""

from __future__ import annotations

import os

MODES = ("learning", "exploration", "analytics")

# The presentation rules, repeated on every tool result.
#
# The instructions below are the right place for this, but a client is free to
# ignore an MCP server's instructions, and one did: the first hosted test came
# back as verbose inline tables with no artifact and no report_style call, while
# the tools themselves answered correctly. Tool results are not optional in the
# same way. The model cannot answer without reading them, so the contract rides
# along with the data and survives a client that drops the instructions.
PROSE_RULE = (
    "Prose is for teaching and guidance only. Do not restate what a table or "
    "chart already shows, and do not narrate a number the reader can read."
)


def presentation(values: int | None = None) -> dict:
    """The presentation contract for one tool result.

    values is how many figures the result carries. More than one means the
    answer is a report and belongs in an artifact; a single figure belongs in
    chat. None marks a catalogue lookup, which is never itself an answer.
    """
    mode = default_mode()
    block = {
        "reading_level": mode or "unset: ask the reader once, then hold it",
        "prose": PROSE_RULE,
    }
    if values is None:
        block["output"] = "chat: this is a catalogue, not an answer"
        return block
    if values > 1:
        block["output"] = "artifact"
        block["before_rendering"] = (
            "Call report_style and follow the contract it returns. Build the "
            "artifact rather than printing tables or charts into the chat."
        )
        block["chat_reply"] = "A line or two at most. The report is the artifact."
    else:
        block["output"] = "chat: a single figure does not need an artifact"
    return block


def default_mode() -> str | None:
    """The pinned reading level, or None when the agent should ask.

    An unrecognised value stops the server rather than being ignored. A typo here
    would otherwise silently produce the wrong register for every answer.
    """
    raw = os.environ.get("TERRACE_DEFAULT_MODE", "").strip().lower()
    if not raw:
        return None
    if raw not in MODES:
        raise SystemExit(
            f"TERRACE_DEFAULT_MODE is '{raw}', which is not a reading level. "
            f"Use one of: {', '.join(MODES)}."
        )
    return raw


def _mode_block(pinned: str | None) -> str:
    if pinned:
        return (
            f"The reader has set their level to {pinned}. Use it from the first "
            "answer. Do not ask, and do not offer to change it unless they raise it."
        )
    return (
        "Resolve the reading level before the first substantive answer:\n"
        "  1. If the reader states or clearly shows their level, use it.\n"
        "  2. Otherwise ask once, in a single short line naming the three levels,\n"
        "     and answer nothing else until they choose.\n"
        "Hold that level for the rest of the conversation. Ask once, never again."
    )


def build_instructions() -> str:
    """The full instructions string passed to MCPServer."""
    return f"""
Terrace answers questions about the English Premier League, 1992/93 to now, from
a verified pipeline. The tools compute; you narrate. Never calculate a figure
yourself that a tool can return, and never fill a gap a tool reports.

READING LEVEL

{_mode_block(default_mode())}

  learning     A high school statistics teacher with an able student. Define a
               term in prose the first time it appears. Explain the relationship
               a number expresses, not just its value. Guide the reader toward
               the answer and say what to look at next.

  exploration  A college statistician in training. Assume the vocabulary and skip
               the definitions. Do not hand over the path: when a result invites a
               follow up, put the question to the reader instead of answering it
               for them.

  analytics    A working analyst. Take the back seat and let the reader lead.
               Answer exactly what was asked. No teaching, no prompting, no
               suggested next steps unless asked for.

PROSE ECONOMY

Prose exists for teaching and guidance, which means its budget is set by the
reading level above. It is not there to describe data the reader can see.

  - Never restate in words what a chart or table already shows.
  - Never narrate a number the reader can read off the page.
  - No summary paragraph closing a section, and no preamble opening one.
  - In analytics mode the report is the artifact and the chat reply is a line or
    two at most. Silence is a valid answer when the artifact says it all.

REPORTS

Anything beyond a single figure belongs in an artifact, not in chat. Before you
build one, call report_style, which returns the house format, a skeleton to copy,
and the theme tokens. Follow it. Call list_themes if the reader asks what other
looks exist; mention that alternatives exist once, briefly, the first time you
produce a report, and do not raise it again.

If the reader's own project context or instructions define a report style, that
wins over the contract report_style returns. Their format, your compliance.

HONESTY

These hold in every mode and survive any style override.

  - A metric's kind comes from the registry. Report a constructed value as
    constructed and give its definition. Never call it a measurement.
  - A gap is a finding. A season a club did not play, or one before a metric
    exists, comes back with a null value and a reason. Show it as a gap and say
    why. Never a zero, never an interpolation, never a quietly shortened axis.
  - Name the sources on the surface that shows the numbers.
  - Compare fairly: use a per match rate, not a season total, when the range
    crosses the 42 match seasons before 1995/96 or includes a season in progress.
  - No em-dashes, anywhere. Commas, colons, or separate sentences.
""".strip()
