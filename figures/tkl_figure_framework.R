# Analytic framework: data units -> analyses -> RQ -> interpretive goal (consent-16 n values). Vector, 174 mm.
suppressPackageStartupMessages({library(ggplot2); library(dplyr); library(tibble)})
# Figure 3 (Method, Data Analysis). Hand-specified diagram: the n values in the boxes are typed text, not read from
# results; check_numbers.py does not cover them. Output folder from TKL_FIGOUT (repro/run_all.py), default figures/out.
out <- Sys.getenv("TKL_FIGOUT", "out"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
ink <- "#1F2430"; mid <- "#6B7280"; rule <- "#9CA3AF"; fill0 <- "#F3F4F6"; accent <- "#3E6E9E"; fam <- "Arial"
# columns (x centres) and widths
cx <- c(units = 1.55, an = 4.75, rq = 8.0, goal = 10.95); w <- c(units = 2.7, an = 3.1, rq = 2.7, goal = 2.6)
ly <- c(RQ1 = 6.1, RQ2 = 3.95, RQ3 = 1.55); h <- c(RQ1 = 1.55, RQ2 = 1.55, RQ3 = 1.95)
box <- function(col, lane, label, lty = "solid", fill = "white", bold = FALSE, tag = NA, hh = h[[lane]], yy = ly[[lane]]) {
  tibble(x = cx[[col]], y = yy, w = w[[col]], h = hh, label = label, lty = lty, fill = fill, bold = bold, tag = tag)
}
B <- bind_rows(
  box("units", "RQ1", "Sessions (n = 72; 57 in the\nsurvival frame)\nLearner requests (n = 45)\n16 modules \u00d7 5 course weeks"),
  box("units", "RQ2", "Request messages (n = 45)\nfrom 10 requesters\nLearners (n = 15)"),
  box("units", "RQ3", "Lag-1 transitions (n = 6,654)\nReplies (n = 40) vs. tutor-\ninitiated messages (n = 364)\nModule-page events\n(n = 4,597) in 15 learners"),
  box("an", "RQ1", "Kaplan\u2013Meier time to\nfirst request\nModule \u00d7 week request map", tag = "Descriptive"),
  box("an", "RQ2", "Content coding (7 codes;\nAI second coder, \u03ba = .88)\nDescriptive activity profiles", tag = "Descriptive"),
  box("an", "RQ3", "Lag-sequential analysis, split\nby reply vs. tutor-initiated\nReturn curve; peri-request profile\nGEE, module fixed effects,\nbias-reduced SE", lty = "22", tag = "Descriptive + associational"),
  box("rq", "RQ1", "RQ1\nTask contexts and phases\nof help seeking", fill = fill0, bold = TRUE),
  box("rq", "RQ2", "RQ2\nInstrumental and executive\nforms of requests", fill = fill0, bold = TRUE),
  box("rq", "RQ3", "RQ3\nReturn to exploration after\nrequested vs. unsolicited\nsupport", fill = fill0, bold = TRUE),
  box("goal", "RQ1", "Help seeking as a task-\nlocated regulation decision\nunder impasse"),
  box("goal", "RQ2", "Instrumental vs. executive\nhelp seeking"),
  box("goal", "RQ3", "Requested vs. unsolicited\nsupport and the return to\nproductive exploration")
)
# context unit (survey) and ESM branch, converging box
ctx <- tibble(x = cx[["units"]], y = -0.55, w = w[["units"]], h = 0.95, label = "Survey: 33 responses from\n13 learners, 3 class sessions", lty = "solid", fill = "white", bold = FALSE, tag = NA)
esm <- tibble(x = cx[["an"]], y = -0.55, w = w[["an"]], h = 0.95, label = "ESM: specification curve (8 models),\nearlier vs. corrected coding,\ntransition networks", lty = "solid", fill = "white", bold = FALSE, tag = NA)
conv <- tibble(x = 9.475, y = -0.55, w = 5.55, h = 0.95, label = "Help requests to an optional GenAI tutor are task-located and\nmost often seek sensemaking; learners return to exploration\nafter requested and scripted support alike", lty = "solid", fill = fill0, bold = TRUE, tag = NA)
AllB <- bind_rows(B, ctx, esm, conv)
edge <- function(x1, y1, x2, y2, lt = "solid", col = ink) tibble(x = x1, y = y1, xend = x2, yend = y2, lt = lt, col = col)
E <- bind_rows(lapply(names(ly), function(l) bind_rows(
  edge(cx[["units"]] + w[["units"]] / 2, ly[[l]], cx[["an"]] - w[["an"]] / 2, ly[[l]]),
  edge(cx[["an"]] + w[["an"]] / 2, ly[[l]], cx[["rq"]] - w[["rq"]] / 2, ly[[l]]),
  edge(cx[["rq"]] + w[["rq"]] / 2, ly[[l]], cx[["goal"]] - w[["goal"]] / 2, ly[[l]]))))
# goals converge (orthogonal: down a spine at the right of goal column, then into contribution box)
spine_x <- cx[["goal"]] + w[["goal"]] / 2 + 0.25
S <- bind_rows(lapply(names(ly), function(l) tibble(x = cx[["goal"]] + w[["goal"]] / 2, y = ly[[l]], xend = spine_x, yend = ly[[l]])),
               tibble(x = spine_x, y = ly[["RQ1"]], xend = spine_x, yend = -0.55))
S_arrow <- tibble(x = spine_x, y = -0.55, xend = 9.475 + 5.55 / 2, yend = -0.55)
# ESM branch (light, dotted) from RQ3 analyses; survey context to contribution (light)
br <- edge(cx[["an"]], ly[["RQ3"]] - h[["RQ3"]] / 2, cx[["an"]], -0.55 + 0.475, "12", rule)
ctxl <- tibble(x = c(cx[["units"]], cx[["units"]]), y = c(-1.025, -1.3), xend = c(cx[["units"]], 7.6), yend = c(-1.3, -1.3))
ctxa <- tibble(x = 7.6, y = -1.3, xend = 7.6, yend = -1.025)
br2 <- tibble(x = cx[["units"]] + w[["units"]] / 2, y = -0.75, xend = 9.475 - 5.55 / 2, yend = -0.75)
hdr <- tibble(x = cx, y = 7.35, label = c("Data units", "Analyses", "Research questions", "Interpretive goals"))
p <- ggplot() +
  geom_rect(data = AllB, aes(xmin = x - w / 2, xmax = x + w / 2, ymin = y - h / 2, ymax = y + h / 2, linetype = lty, fill = fill),
            colour = ink, linewidth = 0.3) +
  geom_rect(data = filter(AllB, grepl("^RQ", label)), aes(xmin = x - w / 2, xmax = x - w / 2 + 0.06, ymin = y - h / 2, ymax = y + h / 2),
            fill = accent, colour = NA) +
  geom_text(data = AllB, aes(x = x, y = y + ifelse(is.na(tag), 0, 0.1), label = label), family = fam, size = 2.45, colour = ink, lineheight = 0.92) +
  geom_text(data = filter(AllB, !is.na(tag)), aes(x = x + w / 2 - 0.06, y = y - h / 2 + 0.13, label = tag), family = fam,
            size = 2.05, colour = mid, hjust = 1, fontface = "italic") +
  geom_segment(data = E, aes(x, y, xend = xend, yend = yend), colour = ink, linewidth = 0.3,
               arrow = arrow(length = unit(1.3, "mm"), type = "closed")) +
  geom_segment(data = S, aes(x, y, xend = xend, yend = yend), colour = ink, linewidth = 0.3) +
  geom_segment(data = S_arrow, aes(x, y, xend = xend, yend = yend), colour = ink, linewidth = 0.3,
               arrow = arrow(length = unit(1.3, "mm"), type = "closed")) +
  geom_segment(data = br, aes(x, y, xend = xend, yend = yend), colour = rule, linewidth = 0.35, linetype = "12",
               arrow = arrow(length = unit(1.2, "mm"), type = "closed")) +
  geom_text(data = hdr, aes(x, y, label = label), family = fam, size = 2.9, fontface = "bold", colour = ink) +
  annotate("segment", x = 0.15, xend = 12.5, y = 7.0, yend = 7.0, colour = rule, linewidth = 0.3) +
  geom_segment(data = ctxl, aes(x, y, xend = xend, yend = yend), colour = rule, linewidth = 0.35, linetype = "12") +
  geom_segment(data = ctxa, aes(x, y, xend = xend, yend = yend), colour = rule, linewidth = 0.35, linetype = "12",
               arrow = arrow(length = unit(1.2, "mm"), type = "closed")) +
  annotate("text", x = 4.75, y = -1.21, label = "context for interpretation", family = fam, size = 2.05, colour = mid, fontface = "italic") +
  scale_linetype_identity() + scale_fill_identity() +
  coord_cartesian(xlim = c(0.1, 12.55), ylim = c(-1.45, 7.6), expand = FALSE) + theme_void() +
  theme(plot.background = element_rect(fill = "white", colour = NA), plot.margin = margin(2, 2, 2, 2))
for (ext in c("pdf", "png", "tiff")) {
  f <- file.path(out, paste0("Figure3_analytic_framework.", ext))
  if (ext == "pdf") ggsave(f, p, width = 174, height = 122, units = "mm", device = cairo_pdf)
  if (ext == "png") ggsave(f, p, width = 174, height = 122, units = "mm", dpi = 600, device = ragg::agg_png, bg = "white")
  if (ext == "tiff") ggsave(f, p, width = 174, height = 122, units = "mm", dpi = 600, device = ragg::agg_tiff, compression = "lzw")
}
cat("done\n")
