# Where the ideas come from

*The treatment compresses a few small books' worth of advice, and each piece has a name.*

Five ideas do the work, each with a source:

- The range frame is Tufte's (*The Visual Display of Quantitative Information*): a frame that shows nothing becomes two spines that show each variable's minimum and maximum.
- Direct labels are Doumont's (*Trees, maps and theorems*): a legend sends the reader on a round trip between line and key, and a label at the line's end deletes the detour. The label placement is the exact least-squares optimum under no-overlap constraints, re-solved on every draw via the pool-adjacent-violators algorithm.
- The round-number ticks come from [Talbot, Lin and Hanrahan's extended Wilkinson algorithm](http://vis.stanford.edu/papers/tick-labels), through [mizani](https://mizani.readthedocs.io/en/stable/)'s breaks, computed from the data on screen rather than the view limits. How many of them an axis gets is the paper's density term, which mizani leaves out: a target gap between labels in physical units, here tick-label heights, so the count follows the axis's length and the labels' size. The frame modes keep that literature's vocabulary: "nice" numbers (1, 2 or 5 times a power of ten) are [Heckbert's](https://dl.acm.org/doi/10.5555/90767.90783) (*Graphics Gems*, 1990), and "loose" is the paper's word for bounds that enclose the data.
- The colours are [Paul Tol's](https://sronpersonalpages.nl/~pault/) colour-blind-safe schemes, arranged ink-first: a single series stays near-black, and colour enters at series two of the same kind. `color="tol:orange"` works anywhere matplotlib takes a colour.
- The placement rule for `label`, a fixed side order with the first clear position taken, is cartography's. Imhof (1975) and Yoeli (1972) ranked the positions around a point, Christensen, Marks and Shieber (1995) made that ranking the standard objective, and Vega's label transform (Kittivorawong, Moritz, Wongsuphasawat and Heer, 2021) runs the same greedy model in production. R's [directlabels](https://github.com/tdhock/directlabels) stacks labels along a line with the quadratic programme that `placement.stack` solves, and its `far.from.others.borders` is the automatic anchor this library deliberately does not pick. [textalloc](https://github.com/ckjellson/textalloc) (MIT) ran the first experiment, and its overlap tests are the pattern the ink harvesting follows.

vanzelfsprekend also joins a long line of Tufte-in-matplotlib work, and its neighbours deserve direct credit:

- [dufte](https://github.com/nschloe/dufte), since merged into [matplotx](https://github.com/nschloe/matplotx), is the closest kin: the same minimal-ink instinct, and its `line_labels` first framed label placement as a least-squares problem under minimum-distance constraints. vanzelfsprekend solves that same problem, exactly.
- [adjustText](https://github.com/Phlya/adjustText), following R's [ggrepel](https://ggrepel.slowkow.com/), tackles the harder general problem of untangling arbitrary 2-D annotations, which takes iterative approximation. Restricting labels to line ends is what lets vanzelfsprekend place them exactly instead.
- [etframes](https://github.com/ahupp/etframes) is the original, drawing range frames in matplotlib since 2007.
