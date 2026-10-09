# F3: copied from 35_governance_v2.R; model specifications retained; final author-approved outcomes.
sink("results/governance_promise_models_F3.txt")
cat("Data: data/promise_model_F3.csv; F3\n")
# Governance extension (KZ+PL+NL): board digital expertise and AI-promise fulfilment
suppressMessages(library(fixest))
d <- read.csv("data/promise_model_F3.csv", stringsAsFactors = FALSE, na.strings = c("", "NA"))
stopifnot(nrow(d)==184, !anyDuplicated(d$promise_id),
  all(d$verdict_version=="F3"),
  !anyNA(d$verdict_f3_source),
  all(d$verdict_f3_source %in% c("agreement_two_rounds", "third_adjudicator_confirmed_by_first_author_2026-10-09")),
  all(d$verdict_final==d$verdict_f3),
  all(d$fulfilled == as.integer(d$verdict_final=="fulfilled")),
  all(d$fulfilled_or_partial == as.integer(d$verdict_final %in% c("fulfilled","partial"))),
  all(d$dropped == as.integer(d$verdict_final=="dropped")))
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

inputs <- setNames(rep(list(s),length(ms)),names(ms))
print(etable(ms, digits=6, fitstat=~n+r2))

# Machine-readable full-precision estimates and actual estimation samples.
export_models <- function(models, inputs, prefix) {
  estimates <- list(); samples <- list()
  for (name in names(models)) {
    model <- models[[name]]; dat <- inputs[[name]][obs(model), , drop = FALSE]
    ct <- coeftable(model)
    estimates[[name]] <- data.frame(model=name, term=rownames(ct), estimate=ct[,1],
      se=ct[,2], statistic=ct[,3], p_value=ct[,4], N=nrow(dat),
      G=length(unique(paste(dat$country, dat$firm))), row.names=NULL)
    samples[[name]] <- data.frame(model=name, promise_id=dat$promise_id,
      country=dat$country, firm=dat$firm)
    cat("\n", name, "actual sample N/G:", nrow(dat), "/",
        length(unique(paste(dat$country, dat$firm))), "\n")
    print(table(dat$country))
  }
  write.csv(do.call(rbind, estimates), paste0("results/",prefix,"_coefficients_F3.csv"), row.names=FALSE)
  write.csv(do.call(rbind, samples), paste0("results/",prefix,"_samples_F3.csv"), row.names=FALSE)
  print(sessionInfo())
}
export_models(ms, inputs, "governance_promise_models")
sink()
