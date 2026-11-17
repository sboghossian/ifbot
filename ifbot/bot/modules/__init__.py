"""Drop a module here that defines propose(ctx) -> Proposal | None. It is discovered by name.

A module may also define learn(ctx), called for every message before any propose().
Keep propose() free of side effects; use learn() to write to ctx.memory.
"""
