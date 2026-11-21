# Shared setup for the TKL figure scripts: input/output folders, export helper, journal theme.
# Paths come from TKL_FIGDATA / TKL_FIGOUT (set by repro/run_all.py); defaults are relative to figures/.
# Springer artwork: Arial, 174 mm double-column width, vector PDF + 600 dpi TIFF/PNG.
suppressPackageStartupMessages({library(ggplot2); library(dplyr); library(readr); library(tidyr); library(patchwork); library(scales)})
dat <- Sys.getenv("TKL_FIGDATA", "data"); out <- Sys.getenv("TKL_FIGOUT", "out"); dir.create(out, showWarnings = FALSE, recursive = TRUE)
ink <- "#1F2430"; mid <- "#6B7280"; rule <- "#9CA3AF"; fam <- "Arial"
theme_j <- function(base = 8.5) theme_classic(base_size = base, base_family = fam) +
  theme(axis.line = element_line(colour = rule, linewidth = 0.3), axis.ticks = element_line(colour = rule, linewidth = 0.3),
        axis.text = element_text(colour = "#374151", size = base - 0.5), axis.title = element_text(colour = ink, size = base),
        plot.tag = element_text(face = "bold", size = base + 1, family = fam), legend.position = "none",
        plot.background = element_rect(fill = "white", colour = NA), panel.background = element_rect(fill = "white", colour = NA),
        strip.background = element_blank(), strip.text = element_text(face = "bold", hjust = 0, size = base, colour = ink),
        plot.margin = margin(3, 4, 3, 3))
save_fig <- function(p, name, w, h) {
  ggsave(file.path(out, paste0(name, ".pdf")), p, width = w, height = h, units = "mm", device = cairo_pdf)
  ggsave(file.path(out, paste0(name, ".tiff")), p, width = w, height = h, units = "mm", dpi = 600, device = ragg::agg_tiff, compression = "lzw")
  ggsave(file.path(out, paste0(name, ".png")), p, width = w, height = h, units = "mm", dpi = 600, device = ragg::agg_png, bg = "white")
}
