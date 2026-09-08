# Style

Importing `vanzelfsprekend` registers a matplotlib style of the same name for `plt.style.use` and `plt.style.context`: lighter lines, smaller marks, quieter titles. It sets no colour and no frame property; those belong to `distill` and `palettes.cycle`.

```python
with plt.style.context("vanzelfsprekend"):
    fig, ax = plt.subplots()
    ax.plot(x, y)
    vzs.distill(ax)
    fig.savefig("figure.png")
```

Keep the drawing, `distill` and the save inside the context. matplotlib reads these defaults when it renders, not when you call `plot`.
