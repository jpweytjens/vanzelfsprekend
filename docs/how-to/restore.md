# Restore

*`restore` puts everything back exactly.*

`restore(ax)` puts everything back exactly: spines, ticks, tick labels, axis labels, the colour cycle and the draw hook all return to what they were before `apply`, `range_frame` or `mute`. Panels framed together are restored together. A figure you have already saved is unaffected; `restore` is for the axes object you keep working with.

```python
ax.vzs.apply()
fig.savefig("applied.png")
ax.vzs.restore()
fig.savefig("as_it_was.png")
```

The library only ever touched what it can put back, which is what makes the restore exact; [the frame follows the axes](../explanation/hook.md) says why.
