# The accessor and restore

*Every entry point is also a method on the axes, and `restore` puts everything back.*

Importing `vanzelfsprekend` adds a `vzs` accessor to every axes, in the style of pandas and xarray accessors, so the entry points work anywhere as `ax.vzs.distill()`, `ax.vzs.line_labels()` and so on; `unregister()` removes it again, and `register()` puts it back. The accessor mimics matplotlib's method names where one exists with the same contract: `ax.vzs.set_xlabel("time (s)")` is `vzs.xlabel(ax, "time (s)")`.

`restore(ax)` undoes the treatment exactly: spines, ticks, tick labels, axis labels, the colour cycle and the draw hook all return to what they were before `distill`. Panels distilled together are restored together. A figure you have already saved is unaffected; `restore` is for the axes object you keep working with.

```python
vzs.distill(ax)
fig.savefig("treated.png")
vzs.restore(ax)
fig.savefig("as_it_was.png")
```
