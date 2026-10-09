# F3: copied from 34_models_v2.R; model specifications retained; final author-approved outcomes.
sink("results/promise_models_F3.txt")
cat("Data: data/promise_model_F3.csv; F3\n")
# Article 1 models: who fulfils AI promises?
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
d$spec2 <- as.integer(d$specificity == 2); d$pilot <- as.integer(d$promise_status == "PILOT")
d$later <- n(d$n_later_reports); d$general <- as.integer(d$category %in% c("general_ai", "other"))
cat("== Raw rates by country ==\n"); print(aggregate(cbind(fulfilled, fulfilled_or_partial, dropped) ~ country, d, mean)); print(table(d$country))
cat("\n== Fisher exact: full fulfilment KZ vs PL, KZ vs NL ==\n")
for (cc in c("PL", "NL")) { s <- droplevels(subset(d, country %in% c("KZ", cc)))
  print(fisher.test(table(s$country, s$fulfilled))$p.value) }
m1 <- feols(fulfilled ~ country | year, d, cluster = ~firm)
m2 <- feols(fulfilled ~ country + spec2 + pilot + general + later | year, d, cluster = ~firm)
m3 <- feols(fulfilled_or_partial ~ country + spec2 + pilot + general + later | year, d, cluster = ~firm)
m4 <- feglm(fulfilled ~ country + spec2 + pilot + general + later | year, d, family = binomial, cluster = ~firm)
k <- subset(d, country %in% c("KZ", "PL") & !is.na(log_assets)); k$country <- droplevels(k$country)
k$dig_any <- as.integer(n(k$dig) > 0); k$state_y <- as.integer(tolower(k$state) == "yes")
cat("\nKZ+PL promises with firm data:", nrow(k), "\n")
m5 <- feols(fulfilled ~ dig_any + state_y + log_assets + country + spec2 + pilot + general + later | year, k, cluster = ~firm)
m6 <- feols(fulfilled_or_partial ~ dig_any + state_y + log_assets + country + spec2 + pilot + general + later | year, k, cluster = ~firm)

ms <- list(m1=m1,m2=m2,m3=m3,m4=m4,m5=m5,m6=m6)
inputs <- list(m1=d,m2=d,m3=d,m4=d,m5=k,m6=k)
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
export_models(ms, inputs, "promise_models")
sink()
