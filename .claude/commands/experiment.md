Create an isolated git worktree for a new experiment.

Ask the user: "What should this experiment be called?" if they didn't provide a name.

Then run:
```
git worktree add experiments/{name} -b experiment/{name}
```

Say: "Worktree created at experiments/{name} on branch experiment/{name}. Work there, then merge back to main when ready."
