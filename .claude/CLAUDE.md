# Project stage

STAGE: explore   (explore | consolidate | lock)

If the STAGE line above is missing, ask me which stage this project is in, then add the line here. Do not ask again once it exists.
To change stage, I edit that line myself, or tell you "move to <stage>" and you update it.

## Always (every stage)
- Never overwrite or modify raw data in data/raw/.
- Do not add anything I did not ask for. If you think a safeguard, abstraction or check is needed, suggest it in one line and wait for my answer.
- Prefer the simplest thing that works at the current stage.

## explore
- Simple scripts, minimal abstractions, single file where possible, roughly under 100 lines per file.
- No file locks, hashing, input validation, or elaborate eval frameworks.
- Let errors crash loudly. Overwriting output files is fine.

## consolidate
- Save the config next to every result file.
- Use one fixed eval script. Do not change its metrics without telling me.
- Set random seeds. Keep logging simple.
- Still no locks or hash checks unless I ask.

## lock
- Eval code and eval data are frozen. Any change needs my explicit approval.
- Record data hashes and the exact config for every reported number.
- Every reported result must be reproducible from one command.
- Do not overwrite existing result files. Write new ones with a clear name.
