# Final analyses for the PCE version. Run from PCE_submission/analysis:  Rscript final_analysis.R
# Inputs: ../repo/data/promise_model_F5.csv, ../repo/data/coded/kz_pl_firm_panel.csv,
#         ../repo/data/coded/report_panel_ai_mentions.csv, ../repo/data/continued_disclosure_content_F5.csv
# Outputs: out/*.csv, out/Figure_1.png/.pdf, out/log.txt
invisible(Sys.setlocale("LC_CTYPE", "en_US.UTF-8")); options(encoding = "UTF-8")
suppressMessages({library(fixest); library(ggplot2)})
base <- if (dir.exists("../repo/data")) "../repo/data" else "../data"  # works in PCE_submission/analysis and in repo/pce_version
dir.create("out", showWarnings = FALSE)
sink("out/log.txt", split = TRUE)
num <- function(x) suppressWarnings(as.numeric(x))
r1 <- function(x) round(x, 1)

## ---------- commitment data ----------
d <- read.csv(file.path(base, "promise_model_F5.csv"), stringsAsFactors = FALSE, fileEncoding = "UTF-8", na.strings = c("", "NA"))
stopifnot(nrow(d) == 183, all(d$verdict_version == "F5"))
d$country <- relevel(factor(d$country), ref = "PL")
d$pilot <- as.integer(d$promise_status == "PILOT"); d$later <- num(d$n_later_reports)
d$general <- as.integer(d$category %in% c("general_ai", "other")); d$spec2 <- as.integer(d$spec_final == 2)
d$fid <- paste(d$country, d$firm)
d$st <- ifelse(d$state == "yes", 1, ifelse(d$state == "no", 0, NA))
d$holding <- as.integer(grepl("самрук_қазына|байтерек", d$firm))
d$sector3 <- ifelse(d$holding == 1, "holding", ifelse(d$finance == 1, "bank_ins", "other"))
d$otherfin <- as.integer(d$firm %in% c("аграрная_кредитная_корпорация", "мфо_эко_финанс"))  # non-bank lenders
d$sector4 <- ifelse(d$holding == 1, "holding", ifelse(d$otherfin == 1, "other_fin", ifelse(d$finance == 1, "bank_ins", "nonfin")))
d$anycont <- 1 - d$dropped
d$outcome <- factor(d$verdict_final, levels = c("fulfilled", "partial", "not_fulfilled", "dropped"),
                    labels = c("Full confirmation", "Partial confirmation", "Reported as ongoing", "Untraced"))
d$ygrp <- ifelse(d$year <= 2022, "2021-22", ifelse(d$year == 2023, "2023", "2024"))

## Table: outcomes by country
tab <- as.data.frame.matrix(table(d$country, d$outcome)); tab$N <- rowSums(tab)
tab$firms <- tapply(d$fid, d$country, function(x) length(unique(x)))[rownames(tab)]
tab$any_later_text <- tapply(d$anycont, d$country, sum)[rownames(tab)]
write.csv(tab, "out/T_outcomes_country.csv")
cat("== Outcomes by country ==\n"); print(tab); print(r1(100 * prop.table(table(d$country, d$outcome), 1)))

## Outcomes by commitment-year group and by follow-up count (KZ, PL, NL)
d$fgrp <- ifelse(d$later >= 2, ">=2 later reports", "1 later report")
yt <- aggregate(cbind(N = 1, full = d$fulfilled, ongoing = d$verdict_final == "not_fulfilled", untraced = d$dropped) ~ country + ygrp, d, sum)
ft <- aggregate(cbind(N = 1, full = d$fulfilled, ongoing = d$verdict_final == "not_fulfilled", untraced = d$dropped) ~ country + fgrp, d, sum)
write.csv(yt, "out/T_outcomes_year.csv", row.names = FALSE); write.csv(ft, "out/T_outcomes_followup.csv", row.names = FALSE)
cat("\n== By year group ==\n"); print(yt); cat("\n== By follow-up ==\n"); print(ft)

## Sector recode and state by country
cat("\n== sector4 x country ==\n"); print(table(d$country, d$sector4))
sec <- aggregate(cbind(N = 1, full = d$fulfilled) ~ country + sector4, d, sum); write.csv(sec, "out/T_sector_country.csv", row.names = FALSE); print(sec)
st <- aggregate(cbind(N = 1, full = d$fulfilled, ongoing = d$verdict_final == "not_fulfilled", untraced = d$dropped) ~ country + state, transform(d, state = ifelse(is.na(state), "unknown", state)), sum)
write.csv(st, "out/T_state_country.csv", row.names = FALSE); cat("\n== State x country ==\n"); print(st)
sp <- aggregate(cbind(N = 1, full = d$fulfilled, untraced = d$dropped) ~ country + spec2, d, sum)
write.csv(sp, "out/T_specificity_country.csv", row.names = FALSE); cat("\n== Specificity x country ==\n"); print(sp)

## ---------- KZ vs PL contrasts ----------
X <- "country + pilot + general + later"
f <- function(y, rhs) as.formula(paste(y, "~", rhs, "| year"))
kz <- function(m, label, dd) {
  b <- coef(m)["countryKZ"]; s <- se(m)["countryKZ"]; p <- pvalue(m)["countryKZ"]
  data.frame(spec = label, est = r1(100 * b), se = r1(100 * s), p = round(p, 3), N = nobs(m),
             N_KZ = sum(dd$country == "KZ"), N_PL = sum(dd$country == "PL"),
             firms_KZPL = length(unique(dd$fid[dd$country != "NL"])))
}
dd <- d
w_eq <- 1 / ave(rep(1, nrow(d)), d$fid, FUN = sum)
dkp <- droplevels(d[d$country != "NL", ])
res <- rbind(
  kz(feols(f("fulfilled", X), d, cluster = ~fid), "Full: baseline controls", d),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d, cluster = ~fid), "Full: + specificity + finance (main)", d),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), dkp, cluster = ~fid), "Full: KZ and PL only", dkp),
  kz(feols(f("fulfilled", paste("spec2 + i(sector4, ref='nonfin') +", X)), d, cluster = ~fid), "Full: banks/insurers, other lenders and holdings separated", d),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d[d$holding == 0, ], cluster = ~fid), "Full: holdings excluded", d[d$holding == 0, ]),
  kz(feols(f("fulfilled", paste("spec2 + finance + st +", X)), d, cluster = ~fid), "Full: + state affiliation (known only)", d[!is.na(d$st), ]),
  kz(feols(f("fulfilled", paste("spec2 + finance + st + log_assets +", X)), d, cluster = ~fid), "Full: + state + log assets", d[!is.na(d$st) & !is.na(d$log_assets), ]),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d[!grepl("самрук_қазына|qazaqgaz|bank_centercredit", d$firm), ], cluster = ~fid), "Full: without the three largest KZ contributors", d[!grepl("самрук_қазына|qazaqgaz|bank_centercredit", d$firm), ]),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d[d$year <= 2023, ], cluster = ~fid), "Full: commitments 2021-2023", d[d$year <= 2023, ]),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d[d$later == 1, ], cluster = ~fid), "Full: exactly one later report", d[d$later == 1, ]),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d[d$later >= 2, ], cluster = ~fid), "Full: two or more later reports", d[d$later >= 2, ]),
  kz(feols(f("fulfilled", paste("spec2 + finance +", X)), d, weights = w_eq, cluster = ~fid), "Full: equal firm weights", d),
  kz(feols(f("fulfilled_or_partial", paste("spec2 + finance +", X)), d, cluster = ~fid), "Full or partial (main controls)", d),
  kz(feols(f("anycont", paste("spec2 + finance +", X)), d, cluster = ~fid), "Any identifiable later text (main controls)", d),
  kz(feols(f("I(as.integer(verdict_final=='not_fulfilled'))", paste("spec2 + finance +", X)), d, cluster = ~fid), "Reported as ongoing (main controls)", d))
write.csv(res, "out/T_contrasts_KZ_PL.csv", row.names = FALSE)
ms_state <- feols(f("fulfilled", paste("spec2 + finance + st +", X)), d, cluster = ~fid)
write.csv(data.frame(term = "state affiliation", est = r1(100 * coef(ms_state)["st"]), se = r1(100 * se(ms_state)["st"]), p = round(pvalue(ms_state)["st"], 3), N = nobs(ms_state)), "out/T_state_coef.csv", row.names = FALSE)
cat("state coef:", r1(100 * coef(ms_state)["st"]), r1(100 * se(ms_state)["st"]), "N", nobs(ms_state), "\n")
cat("Note: in the one-later-report subset fixest drops singleton year-FE observations:", 92 != sum(d$later == 1), "\n")
cat("\n== KZ vs PL contrasts (pp) ==\n"); print(res, row.names = FALSE)

## Leave-one-firm-out (KZ and PL firms), main specification
firms <- unique(d$fid[d$country != "NL"])
lofo <- do.call(rbind, lapply(firms, function(ff) {
  m <- feols(f("fulfilled", paste("spec2 + finance +", X)), d[d$fid != ff, ], cluster = ~fid)
  data.frame(dropped = ff, est = r1(100 * coef(m)["countryKZ"]), se = r1(100 * se(m)["countryKZ"]), p = round(pvalue(m)["countryKZ"], 3)) }))
write.csv(lofo, "out/T_lofo.csv", row.names = FALSE)
cat("\n== LOFO: est range", range(lofo$est), "; max p", max(lofo$p), "; weakest:", lofo$dropped[which.max(lofo$p)], "\n")

## Firm-level comparison (equal firm, nonparametric)
a <- aggregate(fulfilled ~ fid + country, dkp, mean)
wt <- wilcox.test(fulfilled ~ country, a, exact = FALSE)
cat("Firm means:", tapply(a$fulfilled, a$country, function(x) round(mean(x), 3)), " n:", table(a$country), " Wilcoxon p", round(wt$p.value, 3), "\n")

## Raw bootstrap KZ-PL (firm resampling within country), seed fixed
set.seed(20261015)
boot <- replicate(10000, {
  s <- unlist(lapply(c("KZ", "PL"), function(cc) { fs <- unique(dkp$fid[dkp$country == cc]); sample(fs, length(fs), TRUE) }))
  b <- do.call(rbind, lapply(s, function(ff) dkp[dkp$fid == ff, c("country", "fulfilled")]))
  mean(b$fulfilled[b$country == "KZ"]) - mean(b$fulfilled[b$country == "PL"]) })
raw <- mean(dkp$fulfilled[dkp$country == "KZ"]) - mean(dkp$fulfilled[dkp$country == "PL"])
cat("Raw KZ-PL full:", r1(100 * raw), " 95% firm bootstrap:", r1(100 * quantile(boot, c(.025, .975))), "\n")
write.csv(data.frame(raw = r1(100 * raw), lo = r1(100 * quantile(boot, .025)), hi = r1(100 * quantile(boot, .975)),
                     firm_mean_KZ = round(mean(a$fulfilled[a$country == "KZ"]), 3), firm_mean_PL = round(mean(a$fulfilled[a$country == "PL"]), 3),
                     wilcoxon_p = round(wt$p.value, 3)), "out/T_raw_bootstrap.csv", row.names = FALSE)

## Specificity coefficient pooled and leave-country-out
spc <- do.call(rbind, lapply(c("all", "KZ", "PL", "NL"), function(cc) {
  dd <- if (cc == "all") d else droplevels(d[d$country != cc, ])
  m <- feols(f("fulfilled", paste("spec2 + finance +", X)), dd, cluster = ~fid)
  data.frame(sample = ifelse(cc == "all", "all", paste("without", cc)), est = r1(100 * coef(m)["spec2"]), se = r1(100 * se(m)["spec2"]), N = nobs(m)) }))
write.csv(spc, "out/T_specificity_lco.csv", row.names = FALSE); cat("\n== Specificity, leave-country-out ==\n"); print(spc)

## ---------- Continued-disclosure content ----------
cd <- read.csv(file.path(base, "continued_disclosure_content_F5.csv"), stringsAsFactors = FALSE, fileEncoding = "UTF-8")
cd <- merge(cd, d[, c("promise_id", "country")], by = "promise_id")
cat("\n== Continued content (coder 1) ==\n"); print(table(cd$country, cd$disclosure_content))
cat("explanation coder1:\n"); print(table(cd$country, cd$explanation_given)); cat("explanation coder2:\n"); print(table(cd$country, cd$explanation_coder2))

## ---------- Part A: reporting environment ----------
ALIAS <- c("Банк ЦентрКредит" = "Bank CenterCredit", "КазМунайГаз" = "KazMunayGas", "КазАзот" = "KazAzot",
           "КазТрансОйл" = "KazTransOil", "Казатомпром" = "Kazatomprom", "Казахтелеком" = "Kazakhtelecom")
normf <- function(s) { s0 <- gsub("_", " ", s); s1 <- ifelse(s0 %in% names(ALIAS), ALIAS[s0], s); gsub("^_+|_+$", "", gsub("(*UCP)\\W+", "_", s1, perl = TRUE)) }  # same rule as scripts/24_promise_model_data.py
rp <- read.csv(file.path(base, "coded/report_panel_ai_mentions.csv"), stringsAsFactors = FALSE, fileEncoding = "UTF-8")
env <- aggregate(cbind(reports = 1, ai_any = rp$ai_any) ~ country + year, rp, sum)
env$share <- r1(100 * env$ai_any / env$reports); write.csv(env, "out/T_env_year.csv", row.names = FALSE)
cat("\n== AI mention share by country-year ==\n"); print(env)
cat("Reports, firms, AI share by country:\n"); print(aggregate(cbind(reports = 1, ai = rp$ai_any) ~ country, rp, sum))
rp$entity <- ifelse(rp$country == "KZ", normf(rp$company), ifelse(rp$country == "NL", tolower(rp$company), rp$company))
ent <- tapply(rp$entity, rp$country, function(x) length(unique(x))); cat("entities after alias/case normalisation:", ent, "total", sum(ent), "\n")
write.csv(data.frame(country = names(ent), entities = as.vector(ent)), "out/T_entities.csv", row.names = FALSE)
p <- read.csv(file.path(base, "coded/kz_pl_firm_panel.csv"), stringsAsFactors = FALSE, fileEncoding = "UTF-8")
p$firm <- normf(p$firm)
p$st <- ifelse(p$state == "yes", 1, ifelse(p$state == "no", 0, NA)); p$lchars <- log(p$chars)
p$log_assets[!(p$currency %in% c("KZT", "PLN"))] <- NA  # assets used only in domestic currency (KZT, PLN)
p$intensity <- p$ai_sentences / p$chars * 1e5
pa <- do.call(rbind, lapply(c("KZ", "PL"), function(cc) {
  s <- p[p$country == cc & !is.na(p$st), ]
  sc <- s[!is.na(s$log_assets), ]
  ms <- list(raw = feols(ai_any ~ st | year, s, cluster = ~firm),
             raw_constant = feols(ai_any ~ st | year, sc, cluster = ~firm),  # obs() index refers to sc for *_constant models
             length_sector_constant = feols(ai_any ~ st + lchars | year + sector_group, sc, cluster = ~firm),
             length_sector = feols(ai_any ~ st + lchars | year + sector_group, s, cluster = ~firm),
             plus_assets = feols(ai_any ~ st + lchars + log_assets | year + sector_group, s, cluster = ~firm),
             intensity = feols(intensity ~ st + lchars + log_assets | year + sector_group, s, cluster = ~firm))
  do.call(rbind, lapply(names(ms), function(k) { m <- ms[[k]]
    data.frame(country = cc, model = k, est = round(ifelse(k == "intensity", 1, 100) * coef(m)["st"], 1),
               se = round(ifelse(k == "intensity", 1, 100) * se(m)["st"], 1), p = round(pvalue(m)["st"], 3), N = nobs(m),
               firms = length(unique((if (grepl("constant", k)) sc else s)$firm[obs(m)]))) })) }))
write.csv(pa, "out/T_partA_state.csv", row.names = FALSE); cat("\n== Part A: state-linked vs non-state ==\n"); print(pa, row.names = FALSE)
cat("Median chars by state:\n"); print(aggregate(chars ~ country + state, p, median))
cat("Raw any-mention by state:\n"); print(aggregate(ai_any ~ country + state, p, function(x) c(n = length(x), share = round(100 * mean(x), 1))))

## ---------- Figure 1 ----------
fd <- droplevels(d[d$country != "NL", ]); fd$country <- factor(fd$country, levels = c("KZ", "PL"), labels = c("Kazakhstan", "Poland"))
pa1 <- as.data.frame(table(country = fd$country, outcome = fd$outcome)); pa1$panel <- "A. Later reported status"
pb1 <- as.data.frame(table(country = fd$country, outcome = factor(fd$ygrp, levels = c("2021-22", "2023", "2024")))); pb1$panel <- "B. Commitment year"
pal <- c("Full confirmation" = "#1b6ca8", "Partial confirmation" = "#7fb3d5", "Reported as ongoing" = "#e8a33d", "Untraced" = "#b0b0b0",
         "2021-22" = "#3f2a6b", "2023" = "#8a74b8", "2024" = "#d9cfee")
g <- ggplot(rbind(pa1, pb1), aes(x = country, y = Freq, fill = outcome)) +
  geom_col(position = position_fill(reverse = TRUE), width = 0.6, colour = "white") +
  geom_text(aes(label = ifelse(Freq > 0, Freq, "")), position = position_fill(vjust = 0.5, reverse = TRUE), size = 3.2) +
  facet_wrap(~panel) + scale_fill_manual(values = pal, name = NULL) + scale_y_continuous(labels = function(x) paste0(100 * x, "%")) +
  labs(x = NULL, y = "Share of commitments", caption = "Kazakhstan: 27 commitments, 16 entities. Poland: 29 commitments, 13 entities.") +
  theme_minimal(base_size = 10) + theme(legend.position = "bottom", panel.grid.major.x = element_blank())
ggsave("out/Figure_1.png", g, width = 7, height = 4.2, dpi = 300); ggsave("out/Figure_1.pdf", g, width = 7, height = 4.2)
sink()
