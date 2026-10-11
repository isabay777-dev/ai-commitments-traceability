# F4 models: main specifications as in F3 plus the robustness checks requested in the pre-submission review.
# Usage (from repository root): Rscript scripts/42_models_F4.R
dir.create("results", showWarnings = FALSE)
suppressMessages(library(fixest))
sink("results/promise_models_F4.txt")
d <- read.csv("data/promise_model_F4.csv", stringsAsFactors = FALSE, na.strings = c("", "NA"))
stopifnot(nrow(d) == 183, !anyDuplicated(d$promise_id), all(d$verdict_version == "F4"))
n <- function(x) suppressWarnings(as.numeric(x))
prep <- function(d) {
  d$country <- relevel(factor(d$country), ref = "NL")
  d$pilot <- as.integer(d$promise_status == "PILOT"); d$later <- n(d$n_later_reports)
  d$general <- as.integer(d$category %in% c("general_ai", "other")); d$spec2 <- as.integer(d$spec_f4 == 2)
  d$fid <- paste(d$country, d$firm); d }
d <- prep(d)
d$spec2_orig <- as.integer(d$specificity_original == 2); d$spec2_sol <- as.integer(d$spec_sol == 2)
cat("== Outcomes by country (F4) ==\n"); print(table(d$country, d$verdict_f4)); print(round(prop.table(table(d$country, d$verdict_f4), 1), 3))
cat("\n== Outcomes by reconciled specificity ==\n"); print(table(d$spec_f4, d$verdict_f4)); print(round(prop.table(table(d$spec_f4, d$verdict_f4), 1), 3))
cat("\n== Specificity agreement: original vs blind recode (binary spec2) ==\n"); print(table(orig = d$spec2_orig, blind = d$spec2_sol))
po <- mean(d$spec2_orig == d$spec2_sol); pe <- mean(d$spec2_orig) * mean(d$spec2_sol) + (1 - mean(d$spec2_orig)) * (1 - mean(d$spec2_sol))
cat("agreement", round(po, 3), "kappa", round((po - pe) / (1 - pe), 3), "\n")
cat("\n== Sector (finance) by country, full confirmation ==\n"); print(round(tapply(d$fulfilled, list(d$country, d$finance), mean), 3)); print(table(d$country, d$finance))
cat("\n== Fisher exact: full confirmation KZ vs PL, KZ vs NL ==\n")
for (cc in c("PL", "NL")) { s <- droplevels(subset(d, country %in% c("KZ", cc))); print(fisher.test(table(s$country, s$fulfilled))$p.value) }
X <- "country + pilot + general + later"
f <- function(y, rhs) as.formula(paste(y, "~", rhs, "| year"))
ms <- list(
  m1  = feols(fulfilled ~ country | year, d, cluster = ~fid),
  m2  = feols(f("fulfilled", paste("spec2 +", X)), d, cluster = ~fid),
  m2f = feols(f("fulfilled", paste("spec2 + finance +", X)), d, cluster = ~fid),
  m3  = feols(f("fulfilled_or_partial", paste("spec2 +", X)), d, cluster = ~fid),
  m3f = feols(f("fulfilled_or_partial", paste("spec2 + finance +", X)), d, cluster = ~fid),
  m4  = feglm(f("fulfilled", paste("spec2 + finance +", X)), d, family = binomial, cluster = ~fid),
  md  = feols(f("dropped", paste("spec2 + finance +", X)), d, cluster = ~fid),
  m2_orig = feols(f("fulfilled", paste("spec2_orig + finance +", X)), d, cluster = ~fid),
  m2_sol  = feols(f("fulfilled", paste("spec2_sol + finance +", X)), d, cluster = ~fid),
  m2_comp = feols(f("fulfilled", paste("proc_n + spec_identify + spec_evaluable + stage_n + finance +", X)),
                  transform(d, proc_n = n(proc), stage_n = n(stage)), cluster = ~fid),
  m2f_grp = feols(f("fulfilled", paste("spec2 + finance +", X)), d, cluster = ~firm_group))
print(etable(ms[1:7], digits = 4, fitstat = ~n + r2)); print(etable(ms[8:11], digits = 4, fitstat = ~n + r2))
cat("\nClusters (firms):", length(unique(d$fid)), " corporate groups:", length(unique(d$firm_group)), "\n")

# Alternative fragment selection (review A3): same firm x category x year keys, different retained fragment.
a <- read.csv("data/alt_fragments_F4.csv", stringsAsFactors = FALSE, na.strings = c("", "NA"))
a <- subset(a, verdict_f4 %in% c("fulfilled", "partial", "not_fulfilled", "dropped"))
base <- d[, c("promise_id", "country", "firm", "year", "category", "promise_status", "n_later_reports", "finance", "firm_group")]
pick <- function(fun) {
  s <- do.call(rbind, lapply(split(a, a$promise_id), function(q) { q <- q[order(-q$retained), ]; q[fun(q$spec_f4), ][1, ] }))
  s <- merge(base, s[, c("promise_id", "verdict_f4", "spec_f4")], by = "promise_id")
  s$fulfilled <- as.integer(s$verdict_f4 == "fulfilled"); s$dropped <- as.integer(s$verdict_f4 == "dropped"); prep(s) }
s_max <- pick(function(x) x == max(x)); s_min <- pick(function(x) x == min(x))
extra <- subset(a, retained == 0 & same_object == "no")
s_all <- rbind(transform(d[, c(names(base), "verdict_f4", "spec_f4")]),
  merge(base, extra[, c("promise_id", "verdict_f4", "spec_f4")], by = "promise_id"))
s_all$fulfilled <- as.integer(s_all$verdict_f4 == "fulfilled"); s_all <- prep(s_all)
cat("\n== Alternative selection: N max/min/all-distinct:", nrow(s_max), nrow(s_min), nrow(s_all), "\n")
cat("keys whose selected fragment differs (max, min):", sum(s_max$spec_f4 != d$spec_f4[match(s_max$promise_id, d$promise_id)]),
    sum(s_min$spec_f4 != d$spec_f4[match(s_min$promise_id, d$promise_id)]), "\n")
alt_ms <- list(
  alt_max = feols(f("fulfilled", paste("spec2 + finance +", X)), s_max, cluster = ~fid),
  alt_min = feols(f("fulfilled", paste("spec2 + finance +", X)), s_min, cluster = ~fid),
  alt_all = feols(f("fulfilled", paste("spec2 + finance +", X)), s_all, cluster = ~fid))
print(etable(alt_ms, digits = 4, fitstat = ~n + r2))

# Governance (secondary, exploratory): common sample, nested specifications, sector adjustment, leave-one-firm-out.
g <- d; g$dig_any <- as.integer(n(g$dig) > 0); g$dig_nar <- as.integer(n(g$dig_narrow) > 0)
g$state_y <- as.integer(tolower(g$state) == "yes"); g$la <- n(g$log_assets)
g <- subset(g, !is.na(dig_any) & !is.na(la) & !is.na(state_y))
g$size_z <- ave(g$la, g$country, FUN = function(x) (x - mean(x)) / sd(x))
cat("\n== Governance common sample:", nrow(g), "commitments,", length(unique(g$fid)), "firms ==\n")
print(table(country = g$country, broad = g$dig_any)); print(table(country = g$country, narrow = g$dig_nar))
cat("narrow-expertise exposed: records", sum(g$dig_nar), "firms", length(unique(g$fid[g$dig_nar == 1])), "finance among them", sum(g$finance[g$dig_nar == 1]), "\n")
Z <- "country + spec2 + general + size_z + state_y"
gms <- list(
  g1  = feols(fulfilled ~ dig_any + country | year, g, cluster = ~fid),
  g2  = feols(f("fulfilled", paste("dig_any +", Z)), g, cluster = ~fid),
  g2f = feols(f("fulfilled", paste("dig_any + finance +", Z)), g, cluster = ~fid),
  g3f = feols(f("fulfilled_or_partial", paste("dig_any + finance +", Z)), g, cluster = ~fid),
  g5  = feols(f("fulfilled", paste("dig_nar +", Z)), g, cluster = ~fid),
  g5f = feols(f("fulfilled", paste("dig_nar + finance +", Z)), g, cluster = ~fid),
  g6f = feols(f("dropped", paste("dig_any + finance +", Z)), g, cluster = ~fid))
print(etable(gms, digits = 4, fitstat = ~n + r2))
cat("\nLeave-one-exposed-firm-out, narrow expertise (g5f):\n")
for (ff in unique(g$fid[g$dig_nar == 1])) { m <- feols(f("fulfilled", paste("dig_nar + finance +", Z)), subset(g, fid != ff), cluster = ~fid)
  cat(ff, round(coef(m)["dig_nar"], 3), "\n") }

all_ms <- c(ms, alt_ms, gms)
est <- do.call(rbind, lapply(names(all_ms), function(nm) { ct <- coeftable(all_ms[[nm]])
  data.frame(model = nm, term = rownames(ct), estimate = ct[, 1], se = ct[, 2], p_value = ct[, 4], N = nobs(all_ms[[nm]]), row.names = NULL) }))
write.csv(est, "results/models_coefficients_F4.csv", row.names = FALSE)
print(sessionInfo())
sink()
