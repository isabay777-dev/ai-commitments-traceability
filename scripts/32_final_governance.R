# Governance extension (KZ+PL+NL): board digital expertise and AI-promise fulfilment
suppressMessages(library(fixest))
d <- read.csv("data/promise_model_final.csv", stringsAsFactors = FALSE, na.strings = c("", "NA"))
n <- function(x) suppressWarnings(as.numeric(x))
d$country <- relevel(factor(d$country), ref = "NL")
d$spec2 <- as.integer(d$specificity == 2); d$general <- as.integer(d$category %in% c("general_ai", "other"))
d$dig_any <- as.integer(n(d$dig) > 0); d$dig_nar <- as.integer(n(d$dig_narrow) > 0)
d$state_y <- as.integer(tolower(d$state) == "yes"); d$la <- n(d$log_assets)
d$fid <- paste(d$country, d$firm)
s <- subset(d, !is.na(dig_any) & !is.na(la))
# within-country standardised size (currencies differ across countries)
s$size_z <- ave(s$la, s$country, FUN = function(x) (x - mean(x)) / sd(x))
cat("Governance sample:", nrow(s), "promises,", length(unique(s$fid)), "firms\n"); print(table(s$country, s$dig_any))
cat("\nRaw full-fulfilment by expert:\n"); print(round(tapply(s$fulfilled, list(s$country, s$dig_any), mean), 2))
ms <- list(
  g1 = feols(fulfilled ~ dig_any + country | year, s, cluster = ~fid),
  g2 = feols(fulfilled ~ dig_any + country + spec2 + general + size_z + state_y | year, s, cluster = ~fid),
  g3 = feols(fulfilled_or_partial ~ dig_any + country + spec2 + general + size_z + state_y | year, s, cluster = ~fid),
  g4 = feglm(fulfilled ~ dig_any + country + spec2 + general + size_z + state_y | year, s, family = binomial, cluster = ~fid),
  g5 = feols(fulfilled ~ dig_nar + country + spec2 + general + size_z + state_y | year, s, cluster = ~fid),
  g6 = feols(dropped ~ dig_any + country + spec2 + general + size_z + state_y | year, s, cluster = ~fid))
print(etable(ms, digits = 3, fitstat = ~ n + r2))
sink("results/governance_promise_models_final.txt"); print(etable(ms, digits = 3, fitstat = ~ n + r2)); sink()
