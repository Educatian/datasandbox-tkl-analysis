# Figure 6 (peri-event profile, lags -10..+10 around requests and tutor-initiated messages, truncated at session
# bounds; RQ3), Figure 1 (learner x Mountain-time course week overview, anonymized P01-P15; Method) and ESM Figure S3
# (lag-1 transition networks, sessions with vs without a request, edges with p >= .05, shared scales). Inputs from
# prep_figure_data.py: figA_peri_event/figA_base.csv, figB_learner_week/figB_learner_totals.csv, figC_transitions.csv.
source("fig_common.R"); suppressPackageStartupMessages({library(tidygraph); library(ggraph)})

# ---------------- Figure 6 (RQ3): peri-event profile, U and T anchors ----------------
cats4 <- c("Manipulation", "Learner request", "Tutor message", "Other")
pal4 <- c("Manipulation" = "#2B3140", "Learner request" = "#3E6E9E", "Tutor message" = "#D4A24C", "Other" = "#D9DCE1")
A <- read_csv(file.path(dat, "figA_peri_event.csv"), show_col_types = FALSE) |>
  mutate(cat = ifelse(cat %in% c("Navigation", "Login or logout"), "Other", cat)) |>
  group_by(panel, lag, n, cat) |> summarise(share = sum(share), .groups = "drop") |>
  mutate(cat = factor(cat, rev(cats4)), panel = factor(panel, c("Aligned on learner requests", "Aligned on tutor-initiated messages")))
base <- read_csv(file.path(dat, "figA_base.csv"), show_col_types = FALSE)
bm <- base$share[base$cat == "Manipulation"]
nlab <- A |> distinct(panel, lag, n)
ticks <- tidyr::expand_grid(panel = factor(levels(A$panel), levels(A$panel)), lag = -10:10)
pa <- ggplot(A, aes(lag, share, fill = cat)) +
  annotate("rect", xmin = -0.5, xmax = 0.5, ymin = -Inf, ymax = Inf, fill = NA, colour = ink, linewidth = 0.35) +
  geom_col(width = 0.86, colour = "white", linewidth = 0.15) +
  geom_segment(data = ticks, aes(x = lag - 0.43, xend = lag - 0.28, y = bm, yend = bm), inherit.aes = FALSE, colour = "white", linewidth = 0.5) +
  geom_segment(data = ticks, aes(x = lag + 0.28, xend = lag + 0.43, y = bm, yend = bm), inherit.aes = FALSE, colour = "white", linewidth = 0.5) +
  geom_text(data = nlab, aes(x = lag, y = 1.045, label = n), inherit.aes = FALSE, size = 1.9, family = fam, colour = mid) +
  geom_segment(data = data.frame(panel = factor(levels(A$panel)[1], levels(A$panel))), aes(x = 10.55, xend = 10.85, y = bm, yend = bm),
               inherit.aes = FALSE, colour = mid, linewidth = 0.4) +
  geom_text(data = data.frame(panel = factor(levels(A$panel)[1], levels(A$panel))), aes(x = 10.95, y = bm, label = paste0("Base rate of\nmanipulation\n(", percent(bm, 0.1), ")")),
            inherit.aes = FALSE, hjust = 0, size = 2.1, family = fam, colour = mid, lineheight = 0.85) +
  scale_fill_manual(values = pal4, breaks = cats4, name = NULL,
                    labels = c("Manipulation", "Learner request", "Tutor message", "Other (navigation, login/logout)")) +
  scale_x_continuous(breaks = seq(-10, 10, 2), labels = function(x) ifelse(x == 0, "0\n(anchor)", ifelse(x > 0, paste0("+", x), x)),
                     expand = expansion(add = c(0.6, 3.6))) +
  scale_y_continuous(labels = percent, breaks = seq(0, 1, 0.25), limits = c(0, 1.07), expand = c(0, 0)) +
  coord_cartesian(clip = "off") + facet_wrap(~panel, ncol = 1) +
  labs(x = "Events before (−) and after (+) the anchor event", y = "Share of events at each lag") + theme_j() +
  theme(legend.position = "bottom", legend.key.size = unit(3, "mm"), legend.text = element_text(size = 7), panel.spacing = unit(4, "mm"))
save_fig(pa, "Figure6_peri_request_profile", 174, 120)

# ---------------- Figure 1 (Method): learner x course week overview ----------------
B <- read_csv(file.path(dat, "figB_learner_week.csv"), show_col_types = FALSE) |> mutate(week = as.Date(week))
Bt <- read_csv(file.path(dat, "figB_learner_totals.csv"), show_col_types = FALSE)
lev <- rev(sort(unique(Bt$pid)))
wk <- seq(min(B$week), max(B$week), by = "week")
B <- B |> mutate(pid = factor(pid, lev), wf = factor(week, wk))
busy <- B |> group_by(week) |> summarise(e = sum(events)) |> slice_max(e, n = 2) |> pull(week)
wl <- paste(format(wk, "%b"), as.integer(format(wk, "%d")))
wl <- ifelse(wk %in% busy, paste0("**", wl, "**"), wl)
pb1 <- ggplot(B, aes(wf, pid)) +
  geom_tile(aes(fill = events), width = 0.9, height = 0.82, colour = "white", linewidth = 0.3) +
  geom_point(data = filter(B, requests > 0), aes(size = requests), shape = 21, fill = ink, colour = "white", stroke = 0.3) +
  geom_text(data = filter(B, requests > 0), aes(label = requests), colour = "white", size = 2.1, family = fam, fontface = "bold") +
  scale_fill_gradient(low = "#E5E7EB", high = "#5B6472", trans = "log10", name = "Events") +
  scale_size(range = c(3, 5.2)) +
  scale_x_discrete(drop = FALSE, labels = wl, position = "top") +
  labs(x = "Course week (starting Monday)", y = NULL) + theme_j() +
  theme(axis.line = element_blank(), axis.ticks = element_blank(), axis.text.x.top = ggtext::element_markdown(size = 7, colour = ink),
        axis.text.y = element_text(size = 7.2, colour = ink))
Bt <- Bt |> mutate(pid = factor(pid, lev))
pb2 <- ggplot(Bt, aes(y = pid)) +
  geom_col(aes(x = events), fill = "#9AA1AC", width = 0.55) +
  geom_text(aes(x = events, label = comma(events)), hjust = -0.15, size = 2.1, family = fam, colour = mid) +
  scale_x_continuous(limits = c(0, max(Bt$events) * 1.3), breaks = NULL, expand = c(0, 0), position = "top") +
  labs(x = "Events", y = NULL) + theme_j() +
  theme(axis.line = element_blank(), axis.ticks = element_blank(), axis.text.y = element_blank(), axis.title.x.top = element_text(size = 7))
pb3 <- ggplot(Bt, aes(y = pid)) +
  geom_text(aes(x = 0, label = sessions), size = 2.3, family = fam, colour = mid) +
  geom_text(aes(x = 1.1, label = ifelse(requests > 0, requests, "\u2013")), size = 2.3, family = fam, colour = ink,
            fontface = ifelse(Bt$requests >= 8, "bold", "plain")) +
  scale_x_continuous(limits = c(-0.6, 1.7), breaks = c(0, 1.1), labels = c("Sessions", "Requests"), position = "top") +
  labs(x = NULL, y = NULL) + theme_j() +
  theme(axis.line = element_blank(), axis.ticks = element_blank(), axis.text.y = element_blank(), axis.text.x = element_text(size = 7, colour = ink))
save_fig(pb1 + pb2 + pb3 + plot_layout(widths = c(5.2, 1.3, 1.35)), "Figure1_learner_week_overview", 174, 112)

# ---------------- ESM Figure S3 (RQ3): transition networks, sessions with vs without a request ----------------
C <- read_csv(file.path(dat, "figC_transitions.csv"), show_col_types = FALSE)
lab <- c(M = "Manipulation", N = "Navigation", S = "Login/\nlogout", U = "Learner\nrequest", R = "Tutor\nreply", T = "Tutor-\ninitiated")
pos <- tibble(name = c("M", "N", "S", "U", "R", "T"), x = c(0, -1.6, -0.8, 1.6, 1.25, 0.6), y = c(0, 0.2, -1.35, 0.85, -0.75, 1.45))
pos <- pos |> mutate(lx = x + c(-0.42, -0.68, 0, 0.62, 0.55, -0.72), ly = y + c(-0.55, 0, -0.5, 0.12, -0.18, 0))
occ <- C |> group_by(panel, to) |> summarise(inn = sum(count), .groups = "drop")
mk <- function(pn) {
  e <- C |> filter(panel == pn, prob >= 0.05) |> transmute(from, to, prob)
  nd <- pos |> filter(name %in% unique(c(C$from[C$panel == pn], C$to[C$panel == pn]))) |>
    left_join(occ |> filter(panel == pn) |> rename(name = to), by = "name") |> mutate(inn = coalesce(inn, 0), label = lab[name])
  g <- tbl_graph(nodes = nd, edges = e |> mutate(from = match(from, nd$name), to = match(to, nd$name)), directed = TRUE)
  ggraph(g, layout = "manual", x = nd$x, y = nd$y) +
    geom_edge_arc(aes(width = prob, alpha = prob, filter = from != to), strength = 0.22, colour = ink,
                  arrow = arrow(length = unit(1.6, "mm"), type = "closed"), end_cap = circle(7.5, "mm"), start_cap = circle(7.5, "mm")) +
    geom_edge_loop(aes(width = prob, alpha = prob, filter = from == to, span = 50, direction = 90, strength = 0.55), colour = ink) +
    geom_node_point(aes(size = sqrt(inn)), colour = ink) +
    geom_node_point(aes(size = sqrt(inn) * 0.6), colour = "white") +
    geom_label(data = nd, aes(x = lx, y = ly, label = label), size = 2.3, family = fam, colour = ink, lineheight = 0.85, inherit.aes = FALSE,
               fill = "white", label.size = 0, label.padding = unit(0.6, "mm"), alpha = 0.9) +
    scale_edge_width(range = c(0.2, 2.6), limits = c(0.05, 1)) + scale_edge_alpha(range = c(0.35, 0.95), limits = c(0.05, 1)) +
    scale_size(range = c(3, 13), limits = c(0, sqrt(max(occ$inn)))) +
    coord_equal(xlim = c(-2.4, 2.4), ylim = c(-2.05, 2.15), clip = "off") +
    labs(title = pn) + theme_void(base_family = fam) +
    theme(legend.position = "none", plot.title = element_text(face = "bold", size = 8.5, colour = ink, hjust = 0),
          plot.background = element_rect(fill = "white", colour = NA))
}
save_fig(mk("Sessions with a request") + mk("Sessions without a request"), "FigureS3_transition_networks", 174, 88)
cat("done\n")
