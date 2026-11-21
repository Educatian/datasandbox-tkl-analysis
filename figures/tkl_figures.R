# Figure 4 (Kaplan-Meier time to first request; RQ1) and ESM Figure S1 (next event after reply vs tutor-initiated
# message under both coding schemes; RQ3). Inputs: fig1_km_curve/fig1_censor_times/fig1_risk_table.csv and
# fig3_transitions.csv from prep_figure_data.py. Censoring ticks sit on the step curve; at-risk row at 0-120 min.
# Style: owner's refined story style (white background, muted multi-hue palette that survives grayscale,
# direct labels, one message per figure). Springer artwork: Arial, 8-10 pt at final size, 174 mm (double column)
# or 84 mm (single column) width, 600 dpi TIFF/PNG + vector PDF. Titles and notes live in the manuscript (APA).
source("fig_common.R"); suppressPackageStartupMessages(library(ggrepel))

ink <- "#202733"; muted <- "#667085"; grid <- "#E4E7EC"
blue <- "#2F6F9F"; coral <- "#C4554F"; teal <- "#1F7F72"; gold <- "#B8901F"; grey <- "#9AA1AC"
fam <- "Arial"

theme_tkl <- function(base = 9) {
  theme_minimal(base_size = base, base_family = fam) +
    theme(plot.background = element_rect(fill = "white", colour = NA),
          panel.background = element_rect(fill = "white", colour = NA),
          panel.grid.minor = element_blank(),
          panel.grid.major = element_line(colour = grid, linewidth = 0.3),
          axis.title = element_text(colour = ink, size = base),
          axis.text = element_text(colour = "#3C4654", size = base - 1),
          axis.line = element_line(colour = "#98A2B3", linewidth = 0.3),
          strip.text = element_text(colour = ink, face = "bold", size = base, hjust = 0),
          legend.position = "none",
          plot.margin = margin(4, 6, 4, 4))
}

# ---- Figure 4 (RQ1): time to first request, sessions 0.1-120 min observed time, KM with censoring marks and risk table ----
km <- read_csv(file.path(dat, "fig1_km_curve.csv"), show_col_types = FALSE)
cens <- read_csv(file.path(dat, "fig1_censor_times.csv"), show_col_types = FALSE)
risk <- read_csv(file.path(dat, "fig1_risk_table.csv"), show_col_types = FALSE)
step_at <- function(t) km$survival[max(which(km$minutes <= t))]
cens$s <- vapply(cens$minutes, step_at, numeric(1))
marks <- tibble(minutes = c(5, 10)) |> mutate(s = vapply(minutes, step_at, numeric(1)),
  lab = paste0(percent(s, 0.1), " request-free\nat ", minutes, " min"))
brks <- c(0, 5, 10, 30, 60, 120)
p1 <- ggplot(km, aes(minutes, survival)) +
  geom_rect(data = km |> mutate(nx = lead(minutes, default = 120)), aes(xmin = minutes, xmax = nx, ymin = lo, ymax = hi),
            inherit.aes = FALSE, fill = blue, alpha = 0.14) +
  geom_step(colour = blue, linewidth = 0.7) +
  geom_point(data = cens, aes(minutes, s), shape = 124, size = 2.2, colour = ink) +
  geom_point(data = marks, aes(minutes, s), shape = 21, fill = "white", colour = blue, size = 1.8, stroke = 0.7) +
  geom_text_repel(data = marks, aes(minutes, s, label = lab), family = fam, size = 2.7, colour = ink,
                  nudge_y = c(0.1, 0.1), nudge_x = c(1.2, 3), segment.colour = muted, segment.size = 0.25,
                  lineheight = 0.9, seed = 1) +
  scale_x_continuous(trans = "sqrt", breaks = brks, limits = c(0, 120), expand = expansion(mult = c(0, 0.02))) +
  scale_y_continuous(labels = percent, limits = c(0.3, 1), breaks = seq(0.3, 1, 0.1)) +
  labs(x = NULL, y = "Sessions without a request") + theme_tkl()
p1r <- ggplot(risk, aes(minutes, 1, label = at_risk)) +
  geom_text(family = fam, size = 2.8, colour = ink) +
  scale_x_continuous(trans = "sqrt", breaks = brks, limits = c(0, 120), expand = expansion(mult = c(0, 0.02))) +
  labs(x = "Minutes since session start (square-root scale)", y = "At risk") +
  coord_cartesian(clip = "off") +
  theme_tkl() + theme(axis.text.y = element_blank(), panel.grid.major = element_blank(), panel.grid.minor = element_blank(),
                      axis.line.y = element_blank(), axis.title.y = element_text(angle = 0, vjust = 0.5))
save_fig(p1 / p1r + plot_layout(heights = c(5, 0.9)), "Figure4_time_to_first_request", 174, 95)

# ---- ESM Figure S1: next event after requested vs unsolicited tutor support, against the base rate ----
tr <- read_csv(file.path(dat, "fig3_transitions.csv"), show_col_types = FALSE) |>
  mutate(scheme = factor(scheme, c("Corrected coding", "Earlier coding")),
         source = factor(source, c("Reply to a learner request", "Tutor-initiated message")),
         lab = sprintf("%d/%d = %s", k, n, percent(p, 0.1)))
base <- tr |> distinct(scheme, base) |> mutate(lab = paste0("Base rate ", percent(base, 0.1)))
p3 <- ggplot(tr, aes(p, source)) +
  geom_vline(data = base, aes(xintercept = base), linetype = "22", colour = muted, linewidth = 0.4) +
  geom_text(data = base, aes(x = base, y = 2.45, label = lab), family = fam, size = 2.5, colour = muted, hjust = -0.05) +
  geom_errorbarh(aes(xmin = lo, xmax = hi), height = 0.12, colour = ink, linewidth = 0.45) +
  geom_point(aes(shape = source, fill = source), size = 2.3, colour = ink, stroke = 0.5) +
  geom_text(aes(x = hi, label = lab), hjust = -0.12, family = fam, size = 2.6, colour = ink) +
  scale_shape_manual(values = c(21, 22)) + scale_fill_manual(values = c(teal, coral)) +
  scale_x_continuous(labels = percent, limits = c(0.5, 1.12), breaks = seq(0.5, 1, 0.1)) +
  scale_y_discrete(limits = rev(levels(tr$source)), expand = expansion(add = c(0.5, 0.7))) +
  facet_wrap(~scheme, ncol = 1) +
  labs(x = "Share of next events that were manipulations", y = NULL) + theme_tkl() +
  theme(panel.grid.major.y = element_blank())
save_fig(p3, "FigureS1_earlier_vs_corrected_coding", 174, 80)

cat("done
")
