# Expanded KZ+PL models: verified board digital expertise vs AI disclosure
suppressMessages(library(fixest))
d <- read.csv("data/panel_kzpl_expanded.csv", stringsAsFactors = FALSE, na.strings = c("NA", ""))
n <- function(x) suppressWarnings(as.numeric(x))
d$dig_any <- as.integer(n(d$dig) > 0); d$dig_nar <- as.integer(n(d$dig_narrow) > 0)
d$bsize <- n(d$board_size); d$indep_sh <- pmin(n(d$n_independent) / d$bsize, 1)
d$state <- as.integer(tolower(d$state) == "yes"); d$log_chars <- log(d$chars)
d$fid <- paste(d$country, d$firm); d$cy <- paste(d$country, d$year)
s <- subset(d, !is.na(dig_any) & !is.na(log_assets) & sector_group != "NA")
cat("Sample:", nrow(s), "firm-years,", length(unique(s$fid)), "firms\n"); print(table(s$country, s$dig_any))
ms <- list(
  raw    = feols(ai_any ~ dig_any | cy, s, cluster = ~fid),
  sector = feols(ai_any ~ dig_any | cy + sector_group, s, cluster = ~fid),
  size   = feols(ai_any ~ dig_any + log_assets + log_chars | cy + sector_group, s, cluster = ~fid),
  full   = feols(ai_any ~ dig_any + log_assets + log_chars + bsize + indep_sh + state | cy + sector_group, s, cluster = ~fid),
  pois   = fepois(ai_sentences ~ dig_any + log_assets + bsize + indep_sh + state | cy + sector_group, s, offset = ~log_chars, cluster = ~fid),
  narrow = feols(ai_any ~ dig_nar + log_assets + log_chars + bsize + indep_sh + state | cy + sector_group, s, cluster = ~fid),
  bycty  = feols(ai_any ~ dig_any:i(country) + log_assets + log_chars + bsize + indep_sh + state | cy + sector_group, s, cluster = ~fid))
for (k in names(ms)) { ct <- coeftable(ms[[k]]); for (v in grep("dig", rownames(ct), value = TRUE))
  cat(sprintf("%-7s %-22s n=%3d  b=%6.3f  se=%.3f  p=%.3f\n", k, v, nobs(ms[[k]]), ct[v,1], ct[v,2], ct[v,4])) }
sink("results/models_expanded.txt"); print(etable(ms, digits = 3)); sink()
