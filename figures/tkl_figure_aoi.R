# Online Resource Fig. S4: where learners clicked and how they moved between controls (AOI work, aoi/heat_figdata.py).
# Rows 1-2: click density (inferno) on the module interface (local Feb-2026 build, 1440-px reference), white nodes = controls
#   (size = actions), arrows = switches between controls (width = n, n >= 2), rings = repeats of the same control.
# Row 3: for the three setting-varying modules, clicks in the 3 clicks after a tutor-initiated message minus all clicks
#   (share difference, scaled to the module's maximum; red = more than usual, blue = fewer).
source("fig_common.R")
library(png); library(grid)
shots <- "../figures/interface/heat"
heat <- read_csv(file.path(dat, "aoi_heat.csv"), show_col_types = FALSE)
diffd <- read_csv(file.path(dat, "aoi_diff.csv"), show_col_types = FALSE)
nodes <- read_csv(file.path(dat, "aoi_nodes.csv"), show_col_types = FALSE)
edges <- read_csv(file.path(dat, "aoi_edges.csv"), show_col_types = FALSE)
pan <- read_csv(file.path(dat, "aoi_panel.csv"), show_col_types = FALSE)
NICE <- c("coin-flipper" = "Coin flipper", "sample-pumper" = "Sample size pumper", "galton-board" = "Galton board",
          "god-mode" = "God mode switch", "summation-machine" = "Summation machine", "rank-line" = "Rank line")
YMAX <- 1000

bg <- function(page, dim = 0.42) {
  img <- readPNG(file.path(shots, paste0(page, ".png")))[1:YMAX, , 1:3]
  g <- (0.299 * img[, , 1] + 0.587 * img[, , 2] + 0.114 * img[, , 3]) * dim + 0.06
  annotation_raster(g, xmin = 0, xmax = 1440, ymin = -YMAX, ymax = 0)
}
frame <- function(p, title) p + coord_fixed(xlim = c(0, 1440), ylim = c(-YMAX, 0), expand = FALSE) +
  labs(title = title) + theme_void(base_family = fam) +
  theme(plot.title = element_text(size = 6.3, colour = ink, margin = margin(0, 0, 2, 0)), legend.position = "none",
        plot.margin = margin(2, 3, 2, 3))

panel_flow <- function(page) {
  h <- filter(heat, page == !!page); n <- filter(nodes, page == !!page); e <- filter(edges, page == !!page)
  e <- e |> left_join(select(n, from = control, x0 = x, y0 = y), by = "from") |> left_join(select(n, to = control, x1 = x, y1 = y), by = "to")
  pi <- filter(pan, page == !!page)
  p <- ggplot() + bg(page) +
    geom_raster(data = h, aes(gx, -gy, fill = val, alpha = val), interpolate = TRUE) +
    scale_fill_viridis_c(option = "inferno", limits = c(0, 1)) + scale_alpha(range = c(0.45, 1)) +
    geom_curve(data = e, aes(x0, -y0, xend = x1, yend = -y1, linewidth = n), curvature = 0.25, colour = "#CFFAFE", alpha = 0.7,
               arrow = arrow(length = unit(0.9, "mm"), type = "closed")) +
    scale_linewidth(range = c(0.2, 1.1)) +
    geom_point(data = filter(n, repeats > 0), aes(x, -y, size = repeats * 1.6 + 6), shape = 21, fill = NA, colour = "#E5E7EB", stroke = 0.45, alpha = 0.8) +
    geom_point(data = n, aes(x, -y, size = actions), shape = 21, fill = "white", colour = "black", stroke = 0.25, alpha = 0.9) +
    scale_size_area(max_size = 3)
  frame(p, sprintf("%s · %d clicks · repeat %s", NICE[[page]], pi$clicks, percent(pi$repeat_share, 1)))
}
panel_diff <- function(page) {
  dd <- filter(diffd, page == !!page); pi <- filter(pan, page == !!page)
  p <- ggplot() + bg(page, 0.30) + geom_raster(data = dd, aes(gx, -gy, fill = val, alpha = abs(val)), interpolate = TRUE) + scale_alpha(range = c(0, 0.95), limits = c(0, 1)) +
    scale_fill_gradient2(low = "#2166AC", mid = "#F7F7F7", high = "#B2182B", midpoint = 0, limits = c(-1, 1))
  frame(p, sprintf("%s · %d clicks after a message", NICE[[page]], pi$after_T_clicks))
}
row1 <- lapply(c("coin-flipper", "sample-pumper", "galton-board"), panel_flow)
row2 <- lapply(c("god-mode", "summation-machine", "rank-line"), panel_flow)
row3 <- lapply(c("god-mode", "summation-machine", "rank-line"), panel_diff)
lab <- function(s) wrap_elements(grid::textGrob(s, x = 0, hjust = 0, gp = gpar(fontfamily = fam, fontsize = 8, fontface = "bold", col = ink)))
fig <- lab("A  Repeating one sampling control") / wrap_plots(row1, nrow = 1) /
       lab("B  Varying settings and rerunning") / wrap_plots(row2, nrow = 1) /
       lab("C  Clicks after a tutor-initiated message minus usual clicks (red = more, blue = fewer)") / wrap_plots(row3, nrow = 1) +
  plot_layout(heights = c(0.07, 1, 0.07, 1, 0.07, 1))
save_fig(fig, "FigureS4_click_heat_aoi_transitions", 174, 150)
cat("done\n")
