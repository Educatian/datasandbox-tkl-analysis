# Figure 5 (request map, module x Mountain-time course week; RQ1), Figure 7 (next-event composition + return curve;
# RQ3) and ESM Figure S2 (specification curve of the 8 session-level models; RQ3). Inputs from prep_figure_data.py:
# fig2_module_week/fig2_module_totals.csv, fig3_next_composition/fig3_return_curve.csv, fig4_forest.csv.
# Bold weeks = two weeks with most module sessions; per-10 rates from < 5 sessions are gray. Grayscale-safe.
source("fig_common.R")
nice <- function(x) { x <- gsub("-", " ", x); x <- paste0(toupper(substr(x, 1, 1)), substr(x, 2, 99))
  recode(x, "Prob scanner" = "Probability scanner", "P hacking" = "P-hacking", "Mode viz" = "Mode visualizer") }

# ---------------- Figure 5 (RQ1): request map (module x course week, exposure vs requests) ----------------
mw <- read_csv(file.path(dat, "fig2_module_week.csv"), show_col_types = FALSE) |>
  mutate(week = as.Date(week), mod = nice(page))
tot <- read_csv(file.path(dat, "fig2_module_totals.csv"), show_col_types = FALSE) |> mutate(mod = nice(page))
lev <- tot |> arrange(order) |> pull(mod)
mw <- mw |> mutate(mod = factor(mod, rev(lev)))
tot <- tot |> mutate(mod = factor(mod, rev(lev)))
wk <- sort(unique(mw$week)); wlab <- paste(format(wk, "%b"), as.integer(format(wk, "%d")))
busy <- mw |> group_by(week) |> summarise(s = sum(sessions)) |> slice_max(s, n = 2)
p2a <- ggplot(mw, aes(factor(week), mod)) +
  geom_tile(aes(fill = sessions), width = 0.9, height = 0.82, colour = "white", linewidth = 0.3) +
  geom_point(data = filter(mw, requests > 0), aes(size = requests), shape = 21, fill = ink, colour = "white", stroke = 0.3) +
  geom_text(data = filter(mw, requests > 0), aes(label = requests), colour = "white", size = 2.1, family = fam, fontface = "bold") +
  scale_fill_gradient(low = "#E5E7EB", high = "#7B8494", limits = c(1, NA), na.value = "white", name = "Sessions") +
  scale_size(range = c(3.2, 5.8)) +
  scale_x_discrete(labels = ifelse(as.character(wk) %in% as.character(busy$week), paste0("**", wlab, "**"), wlab), position = "top") +
  labs(x = "Course week (starting Monday)", y = NULL) + theme_j() +
  theme(axis.line = element_blank(), axis.ticks = element_blank(), axis.text.x.top = ggtext::element_markdown(size = 7.5, colour = ink),
        axis.text.y = element_text(size = 7.8, colour = ink))
p2b <- ggplot(tot, aes(y = mod)) +
  geom_text(aes(x = 0, label = sessions), family = fam, size = 2.6, colour = mid, hjust = 1) +
  geom_text(aes(x = 1, label = ifelse(requests > 0, requests, "\u2013")), family = fam, size = 2.6, colour = ink, hjust = 1) +
  geom_text(aes(x = 2.15, label = ifelse(requests > 0, sprintf("%.1f", per10), "\u2013")), family = fam, size = 2.6,
            colour = ifelse(tot$sessions < 5, "#9CA3AF", ink), hjust = 1,
            fontface = ifelse(tot$sessions >= 10 & tot$per10 >= 5, "bold", "plain")) +
  scale_x_continuous(limits = c(-0.6, 2.3), breaks = c(-0.05, 0.95, 2.1), labels = c("Sessions", "Requests", "Per 10\nsessions"),
                     position = "top") +
  labs(x = NULL, y = NULL) + theme_j() +
  theme(axis.line = element_blank(), axis.ticks = element_blank(), axis.text.y = element_blank(),
        axis.text.x = element_text(size = 7, colour = ink, lineheight = 0.9))
p2 <- p2a + p2b + plot_layout(widths = c(5, 1.6))
save_fig(p2, "Figure5_request_map", 174, 118)

# ---------------- Figure 7 (RQ3): what learners did next (corrected coding) + return curve ----------------
cmp <- read_csv(file.path(dat, "fig3_next_composition.csv"), show_col_types = FALSE)
cats <- c("Manipulation", "Learner request", "Tutor message", "Navigation", "Login or logout")
grays <- c("Manipulation" = "#2B3140", "Learner request" = "#5B6472", "Tutor message" = "#9AA1AC",
           "Navigation" = "#C9CDD4", "Login or logout" = "#E9EBEE")
nN <- cmp |> distinct(source, N) |> tibble::deframe()
src_lab <- c("Reply to a learner request" = paste0("After a reply to a\nlearner request\n(n = ", nN[["Reply to a learner request"]], ")"),
             "Tutor-initiated message" = paste0("After a tutor-\ninitiated message\n(n = ", nN[["Tutor-initiated message"]], ")"),
             "All events (base rate)" = paste0("All events,\nbase rate\n(n = ", comma(nN[["All events (base rate)"]]), ")"))
cmp <- cmp |> mutate(nxt = factor(`next`, rev(cats)), src = factor(src_lab[source], rev(src_lab))) |>
  group_by(src) |> arrange(desc(nxt)) |> mutate(xend = cumsum(share), xmid = xend - share / 2) |> ungroup()
nlab <- cmp |> distinct(src, N, source) |>
  mutate(lab = case_when(grepl("Reply", source) ~ paste0("n = ", N, " replies"),
                         grepl("Tutor", source) ~ paste0("n = ", N, " messages"), TRUE ~ paste0("n = ", comma(N), " events")))
p3a <- ggplot(cmp, aes(share, src, fill = nxt)) +
  geom_col(width = 0.62, colour = "white", linewidth = 0.3) +
  geom_text(data = filter(cmp, share >= 0.08), aes(x = xmid, label = percent(share, 0.1),
            colour = nxt %in% c("Manipulation", "Learner request")), size = 2.6, family = fam) +
  scale_fill_manual(values = grays, breaks = cats, name = NULL) + guides(colour = "none") + scale_colour_manual(values = c(`TRUE` = "white", `FALSE` = ink)) +
  scale_x_continuous(labels = percent, expand = c(0, 0), breaks = seq(0, 1, 0.25)) +
  scale_y_discrete(expand = expansion(add = c(0.6, 0.75))) +
  labs(x = "Share of next events", y = NULL, tag = "A") + theme_j() +
  theme(axis.line.y = element_blank(), axis.ticks.y = element_blank(), axis.text.y = element_text(colour = ink, lineheight = 0.9),
        legend.position = "bottom", legend.key.size = unit(3, "mm"), legend.text = element_text(size = 7),
        legend.margin = margin(0, 0, 0, 0))
rc <- read_csv(file.path(dat, "fig3_return_curve.csv"), show_col_types = FALSE) |>
  mutate(src = recode(source, "Reply to a learner request" = "Reply to a request", "Tutor-initiated message" = "Tutor-initiated",
                      "All events (base rate)" = "Any event"))
p3b <- ggplot(rc, aes(k, share, group = src)) +
  geom_line(aes(linetype = src, colour = src), linewidth = 0.55) +
  geom_point(aes(shape = src, colour = src), size = 1.8, fill = "white", stroke = 0.6) +
  geom_text(data = rc |> filter(k == 5) |> mutate(lab = recode(src, "Reply to a request" = "Reply to\na request", "Tutor-initiated" = "Tutor-\ninitiated"),
                                                   share = share + c(0.012, -0.012, 0)[rank(-share)]),
            aes(x = 5.15, y = share, label = lab, colour = src), hjust = 0, size = 2.4, family = fam, lineheight = 0.85, inherit.aes = FALSE) +
  scale_shape_manual(values = c("Reply to a request" = 21, "Tutor-initiated" = 22, "Any event" = 4)) +
  scale_linetype_manual(values = c("Reply to a request" = "solid", "Tutor-initiated" = "solid", "Any event" = "22")) +
  scale_colour_manual(values = c("Reply to a request" = ink, "Tutor-initiated" = "#7B8494", "Any event" = mid)) +
  scale_y_continuous(labels = percent, limits = c(0, 1), breaks = seq(0, 1, 0.25)) +
  scale_x_continuous(breaks = 1:5, limits = c(1, 6.6), expand = expansion(add = c(0.25, 0))) +
  labs(x = "Events after the source event (k)", y = "Manipulation within k events", tag = "B") + theme_j()
p3 <- p3a + p3b + plot_layout(widths = c(1.65, 1))
save_fig(p3, "Figure7_what_learners_did_next", 174, 72)

# ---------------- ESM Figure S2 (RQ3): specification curve, 6 GEE + 2 FE logit, bias-reduced / cluster CIs ----------------
fo <- read_csv(file.path(dat, "fig4_forest.csv"), show_col_types = FALSE)
spec <- tibble(
  `Corrected coding`          = c(0, 0, 0, 0, 1, 1, 0, 1),
  `Chat events excluded`      = c(0, 0, 1, 1, 1, 1, 1, 1),
  `System events excluded`    = c(0, 0, 0, 0, 1, 1, 0, 1),
  `Module pages only`         = c(0, 0, 0, 0, 0, 1, 0, 1),
  `Page fixed effects`        = c(0, 1, 0, 1, 0, 1, 1, 1),
  `Learner fixed effects`     = c(0, 0, 0, 0, 0, 0, 1, 1),
  `Fixed-effects logit (vs. GEE)` = c(0, 0, 0, 0, 0, 0, 1, 1))
fo <- bind_cols(fo, spec) |> mutate(primary = grepl("primary", spec), rank = rank(OR, ties.method = "first"))
top <- ggplot(fo, aes(rank, OR)) +
  geom_hline(yintercept = 1, colour = mid, linewidth = 0.35) +
  geom_linerange(aes(ymin = lo, ymax = hi), colour = ifelse(fo$primary, ink, "#8B93A1"), linewidth = 0.55) +
  geom_point(aes(shape = converged), size = 2, fill = ifelse(fo$primary, ink, "white"), colour = ink, stroke = 0.55) +
  geom_text(aes(y = hi, label = sprintf("%.2f", OR + 1e-9)), vjust = -0.7, size = 2.4, family = fam, colour = ink) +
  annotate("text", x = fo$rank[fo$primary], y = 0.3, label = "Primary model", size = 2.4, family = fam, fontface = "bold") +
  scale_shape_manual(values = c(`TRUE` = 21, `FALSE` = 24)) +
  scale_y_log10(breaks = c(0.25, 0.5, 1, 2), labels = c("0.25", "0.5", "1", "2"), limits = c(0.28, 3)) +
  scale_x_continuous(limits = c(0.5, 8.5), breaks = NULL) +
  labs(x = NULL, y = "Odds ratio (log scale)") + theme_j() + theme(axis.line.x = element_blank())
mat <- fo |> select(rank, primary, `Corrected coding`:`Fixed-effects logit (vs. GEE)`) |>
  pivot_longer(-c(rank, primary), names_to = "choice", values_to = "on") |>
  mutate(choice = factor(choice, rev(names(spec))))
bot <- ggplot(mat, aes(rank, choice)) +
  geom_point(aes(fill = factor(on)), shape = 21, size = 2, colour = ifelse(mat$on == 1, ink, "#C9CDD4"), stroke = 0.4) +
  scale_fill_manual(values = c(`0` = "white", `1` = ink)) +
  scale_x_continuous(limits = c(0.5, 8.5), breaks = 1:8, labels = paste0("S", 1:8)) +
  labs(x = "Specifications ordered by odds ratio", y = NULL) + theme_j() +
  theme(axis.line.y = element_blank(), axis.ticks.y = element_blank(), axis.text.y = element_text(colour = ink))
save_fig(top / bot + plot_layout(heights = c(1.15, 1)), "FigureS2_specification_curve", 174, 105)
cat("done\n")
