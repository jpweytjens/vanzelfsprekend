# Registration

Importing `vanzelfsprekend` adds a `vzs` accessor to every axes, in the style of pandas and xarray accessors, so the entry points work anywhere as `ax.vzs.apply()`, `ax.vzs.line_labels()` and so on; `unregister()` removes it again, and `register()` puts it back. The accessor mimics matplotlib's method names where one exists with the same contract: `ax.vzs.set_xlabel("time (s)")` is `vzs.xlabel(ax, "time (s)")`.

::: vanzelfsprekend.register

::: vanzelfsprekend.unregister
