# Locators

Each locator works on its own, on any matplotlib axes, and can be set before or after `apply` or `range_frame`, which keeps a locator you set instead of overwriting it. The exception is grouped framing, `small_multiples` or shared axes, which computes a shared scale and owns the ticks itself.

::: vanzelfsprekend.TalbotLocator

::: vanzelfsprekend.LogBreaksLocator

::: vanzelfsprekend.DateBreaksLocator

::: vanzelfsprekend.FeatureLocator

::: vanzelfsprekend.SummaryLocator

::: vanzelfsprekend.QuartileLocator

::: vanzelfsprekend.AugmentedLocator
