# Figure 5 (RQ3): (A) event composition before and after learner requests and tutor-initiated messages (pa, from
# tkl_figures_new.R) and (B) share of replies, tutor-initiated messages and all events followed by a manipulation within
# k events (p3b, from tkl_figures_redesign.R). Replaces the former Figures 6 and 7 (7A's shares are reported in the text).
source("tkl_figures_new.R")
source("tkl_figures_redesign.R")
fig5 <- (pa + labs(tag = "A")) / (p3b + labs(tag = "B") + plot_spacer() + plot_layout(widths = c(1.3, 1))) +
  plot_layout(heights = c(1.75, 1))
save_fig(fig5, "Figure5_what_followed_requests_and_messages", 174, 185)
cat("done\n")
